"""
scenario_engine.py
===================
Generates and evaluates forward-looking financial stress scenarios.

Each scenario is produced by applying a deterministic transformation to a
copy of the supplied FinancialState, then projecting cash and risk from
that adjusted state. No scenario mutates the caller's original
FinancialState.
"""

from __future__ import annotations

import uuid
from dataclasses import replace
from typing import Any, Dict, List, Optional

from .config import (
    DEFAULT_SCENARIO_PARAMS,
    RECEIVABLE_DELAY_PROB_DROP_PER_DAY,
    RECEIVABLE_DELAY_MAX_PROB_DROP,
    MIN_RECEIVABLE_PROBABILITY,
    LIQUIDITY_STATUS_TIGHT_MULTIPLIER,
    EPSILON,
)
from .exceptions import InvalidScenarioError, InvalidFinancialStateError
from .models import (
    FinancialState,
    Scenario,
    ScenarioResult,
    ScenarioType,
    Severity,
    LiquidityStatus,
    Obligation,
)
from .risk_engine import RiskEngine


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


class ScenarioEngine:
    """Generates and evaluates financial stress scenarios."""

    def __init__(self, risk_engine: Optional[RiskEngine] = None) -> None:
        self.risk_engine = risk_engine or RiskEngine()

    # ------------------------------------------------------------------
    # Scenario generators
    # ------------------------------------------------------------------
    def generate_normal_scenario(
        self, financial_state: FinancialState
    ) -> Scenario:
        """Baseline scenario: receivables arrive as expected, no
        unexpected obligations occur."""
        self._validate_state(financial_state)
        return Scenario(
            scenario_id=_new_id("scn-normal"),
            name="Normal / Baseline",
            scenario_type=ScenarioType.NORMAL,
            severity=Severity.LOW,
            parameters={},
            description=(
                "Business-as-usual projection assuming receivables arrive "
                "on schedule and no unexpected obligations occur."
            ),
        )

    def generate_receivable_delay_scenario(
        self,
        financial_state: FinancialState,
        delay_days: int,
        receivable_id: Optional[str] = None,
    ) -> Scenario:
        """A receivable (or all receivables, if receivable_id is None) is
        delayed by `delay_days`."""
        self._validate_state(financial_state)
        if delay_days <= 0:
            raise InvalidScenarioError("delay_days must be a positive integer")
        if receivable_id is not None:
            self._require_receivable(financial_state, receivable_id)

        target = receivable_id or "all receivables"
        severity = self._severity_from_days(delay_days)
        return Scenario(
            scenario_id=_new_id("scn-recv-delay"),
            name=f"Receivable Delay ({delay_days} days)",
            scenario_type=ScenarioType.RECEIVABLE_DELAY,
            severity=severity,
            parameters={
                "delay_days": delay_days,
                "receivable_id": receivable_id,
            },
            description=(
                f"Simulates a {delay_days}-day delay affecting {target}, "
                f"including a corresponding drop in collection probability."
            ),
        )

    def generate_cash_shock_scenario(
        self,
        financial_state: FinancialState,
        unexpected_expense: Optional[float] = None,
        description: Optional[str] = None,
    ) -> Scenario:
        """An unexpected cash obligation appears."""
        self._validate_state(financial_state)
        if unexpected_expense is None:
            unexpected_expense = (
                financial_state.cash_balance
                * DEFAULT_SCENARIO_PARAMS["cash_shock_fraction_of_cash"]
            )
        if unexpected_expense <= 0:
            raise InvalidScenarioError("unexpected_expense must be positive")

        severity = self._severity_from_fraction(
            unexpected_expense, financial_state.cash_balance
        )
        return Scenario(
            scenario_id=_new_id("scn-cash-shock"),
            name="Unexpected Cash Shock",
            scenario_type=ScenarioType.CASH_SHOCK,
            severity=severity,
            parameters={"unexpected_expense": unexpected_expense},
            description=description
            or (
                f"Simulates an unexpected obligation of "
                f"{unexpected_expense:,.2f} hitting the business immediately."
            ),
        )

    def generate_supplier_stress_scenario(
        self,
        financial_state: FinancialState,
        supplier_id: str,
        liquidity_risk_increase: Optional[float] = None,
    ) -> Scenario:
        """A key supplier's liquidity risk increases."""
        self._validate_state(financial_state)
        supplier = self._require_supplier(financial_state, supplier_id)
        if liquidity_risk_increase is None:
            liquidity_risk_increase = DEFAULT_SCENARIO_PARAMS[
                "supplier_liquidity_risk_increase"
            ]
        if liquidity_risk_increase <= 0:
            raise InvalidScenarioError(
                "liquidity_risk_increase must be positive"
            )

        new_risk = min(1.0, supplier.liquidity_risk + liquidity_risk_increase)
        severity = self._severity_from_fraction(new_risk, 1.0)
        return Scenario(
            scenario_id=_new_id("scn-supplier-stress"),
            name=f"Supplier Stress ({supplier.name})",
            scenario_type=ScenarioType.SUPPLIER_STRESS,
            severity=severity,
            parameters={
                "supplier_id": supplier_id,
                "liquidity_risk_increase": liquidity_risk_increase,
            },
            description=(
                f"Simulates supplier '{supplier.name}' liquidity risk "
                f"rising from {supplier.liquidity_risk:.2f} to "
                f"{new_risk:.2f}."
            ),
        )

    def generate_financing_shock_scenario(
        self,
        financial_state: FinancialState,
        interest_rate_change: Optional[float] = None,
        financing_id: Optional[str] = None,
    ) -> Scenario:
        """Financing/borrowing cost increases."""
        self._validate_state(financial_state)
        if financing_id is not None:
            self._require_financing(financial_state, financing_id)
        elif not financial_state.financing_options:
            raise InvalidScenarioError(
                "No financing options available to apply financing shock to"
            )
        if interest_rate_change is None:
            interest_rate_change = DEFAULT_SCENARIO_PARAMS[
                "financing_interest_rate_change"
            ]
        if interest_rate_change <= 0:
            raise InvalidScenarioError(
                "interest_rate_change must be positive"
            )

        target = financing_id or "all financing options"
        severity = self._severity_from_fraction(interest_rate_change, 0.10)
        return Scenario(
            scenario_id=_new_id("scn-financing-shock"),
            name="Financing Cost Shock",
            scenario_type=ScenarioType.FINANCING_SHOCK,
            severity=severity,
            parameters={
                "interest_rate_change": interest_rate_change,
                "financing_id": financing_id,
            },
            description=(
                f"Simulates a +{interest_rate_change * 100:.1f} percentage "
                f"point increase in borrowing cost for {target}."
            ),
        )

    def generate_all_scenarios(
        self, financial_state: FinancialState
    ) -> List[Scenario]:
        """Generate the full standard scenario set using config-driven
        default parameters."""
        self._validate_state(financial_state)
        scenarios = [
            self.generate_normal_scenario(financial_state),
            self.generate_receivable_delay_scenario(
                financial_state,
                delay_days=DEFAULT_SCENARIO_PARAMS["receivable_delay_days"],
            ),
            self.generate_cash_shock_scenario(financial_state),
        ]
        if financial_state.supplier_risks:
            most_critical = max(
                financial_state.supplier_risks,
                key=lambda s: s.importance * s.dependency,
            )
            scenarios.append(
                self.generate_supplier_stress_scenario(
                    financial_state, most_critical.supplier_id
                )
            )
        if financial_state.financing_options:
            scenarios.append(
                self.generate_financing_shock_scenario(financial_state)
            )
        return scenarios

    # ------------------------------------------------------------------
    # Scenario evaluation
    # ------------------------------------------------------------------
    def evaluate_scenario(
        self, financial_state: FinancialState, scenario: Scenario
    ) -> ScenarioResult:
        """Apply a scenario to the financial state and compute the
        resulting projected cash, liquidity position, and risk score."""
        self._validate_state(financial_state)
        if scenario is None:
            raise InvalidScenarioError("scenario must not be None")

        baseline_cash = self.risk_engine.project_cash(financial_state)
        adjusted_state, affected_items = self._apply_scenario(
            financial_state, scenario
        )
        projected_cash = self.risk_engine.project_cash(adjusted_state)
        cash_impact = projected_cash - baseline_cash

        liquidity_ratio = projected_cash / max(
            financial_state.minimum_cash_reserve, EPSILON
        )
        liquidity_status = self._liquidity_status(
            projected_cash, financial_state.minimum_cash_reserve
        )

        risk_result = self.risk_engine.calculate_risk(adjusted_state)

        return ScenarioResult(
            scenario_id=scenario.scenario_id,
            projected_cash=round(projected_cash, 2),
            cash_impact=round(cash_impact, 2),
            liquidity_ratio=round(liquidity_ratio, 3),
            liquidity_status=liquidity_status,
            risk_score=risk_result.risk_score,
            risk_level=risk_result.risk_level,
            affected_items=affected_items,
            description=scenario.description,
        )

    def evaluate_all(
        self, financial_state: FinancialState, scenarios: List[Scenario]
    ) -> List[ScenarioResult]:
        """Convenience helper: evaluate a list of scenarios in one call."""
        return [
            self.evaluate_scenario(financial_state, s) for s in scenarios
        ]

    # ------------------------------------------------------------------
    # Internal: scenario -> adjusted FinancialState
    # ------------------------------------------------------------------
    def _apply_scenario(
        self, financial_state: FinancialState, scenario: Scenario
    ) -> (FinancialState, List[str]):
        state = financial_state.copy()
        affected: List[str] = []

        if scenario.scenario_type == ScenarioType.NORMAL:
            pass

        elif scenario.scenario_type == ScenarioType.RECEIVABLE_DELAY:
            delay_days = scenario.parameters["delay_days"]
            receivable_id = scenario.parameters.get("receivable_id")
            prob_drop = min(
                RECEIVABLE_DELAY_MAX_PROB_DROP,
                delay_days * RECEIVABLE_DELAY_PROB_DROP_PER_DAY,
            )
            for r in state.receivables:
                if receivable_id is None or r.id == receivable_id:
                    r.expected_days += delay_days
                    r.probability = max(
                        MIN_RECEIVABLE_PROBABILITY, r.probability - prob_drop
                    )
                    affected.append(r.id)
            if not affected:
                raise InvalidScenarioError(
                    f"receivable_id '{receivable_id}' not found in "
                    "financial state"
                )

        elif scenario.scenario_type == ScenarioType.CASH_SHOCK:
            expense = scenario.parameters["unexpected_expense"]
            new_obligation = Obligation(
                id=_new_id("obl-shock"),
                amount=expense,
                due_days=0,
                description="Unexpected expense (scenario)",
            )
            state.upcoming_obligations.append(new_obligation)
            affected.append(new_obligation.id)

        elif scenario.scenario_type == ScenarioType.SUPPLIER_STRESS:
            supplier_id = scenario.parameters["supplier_id"]
            increase = scenario.parameters["liquidity_risk_increase"]
            found = False
            for s in state.supplier_risks:
                if s.supplier_id == supplier_id:
                    s.liquidity_risk = min(1.0, s.liquidity_risk + increase)
                    affected.append(s.supplier_id)
                    found = True
                    # Flag other highly-dependent suppliers as indirectly
                    # affected (supply-chain contagion signal).
                    for other in state.supplier_risks:
                        if (
                            other.supplier_id != supplier_id
                            and other.dependency >= 0.6
                        ):
                            affected.append(other.supplier_id)
            if not found:
                raise InvalidScenarioError(
                    f"supplier_id '{supplier_id}' not found in financial "
                    "state"
                )

        elif scenario.scenario_type == ScenarioType.FINANCING_SHOCK:
            financing_id = scenario.parameters.get("financing_id")
            rate_change = scenario.parameters["interest_rate_change"]
            for f in state.financing_options:
                if financing_id is None or f.id == financing_id:
                    f.interest_rate = f.interest_rate + rate_change
                    affected.append(f.id)
            if not affected:
                raise InvalidScenarioError(
                    "No financing options available to apply financing "
                    "shock to"
                )

        else:
            raise InvalidScenarioError(
                f"Unsupported scenario_type: {scenario.scenario_type}"
            )

        return state, affected

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _liquidity_status(
        projected_cash: float, minimum_cash_reserve: float
    ) -> LiquidityStatus:
        if projected_cash < 0:
            return LiquidityStatus.NEGATIVE
        if projected_cash < minimum_cash_reserve:
            return LiquidityStatus.BELOW_MINIMUM
        if projected_cash < minimum_cash_reserve * LIQUIDITY_STATUS_TIGHT_MULTIPLIER:
            return LiquidityStatus.TIGHT
        return LiquidityStatus.HEALTHY

    @staticmethod
    def _severity_from_days(delay_days: int) -> Severity:
        if delay_days <= 5:
            return Severity.LOW
        if delay_days <= 15:
            return Severity.MEDIUM
        if delay_days <= 30:
            return Severity.HIGH
        return Severity.CRITICAL

    @staticmethod
    def _severity_from_fraction(value: float, reference: float) -> Severity:
        if reference <= 0:
            return Severity.MEDIUM
        fraction = value / reference
        if fraction <= 0.15:
            return Severity.LOW
        if fraction <= 0.35:
            return Severity.MEDIUM
        if fraction <= 0.60:
            return Severity.HIGH
        return Severity.CRITICAL

    @staticmethod
    def _validate_state(financial_state: FinancialState) -> None:
        if financial_state is None:
            raise InvalidFinancialStateError("financial_state must not be None")
        if financial_state.minimum_cash_reserve <= 0:
            raise InvalidFinancialStateError(
                "minimum_cash_reserve must be > 0"
            )

    @staticmethod
    def _require_receivable(financial_state: FinancialState, receivable_id: str):
        for r in financial_state.receivables:
            if r.id == receivable_id:
                return r
        raise InvalidScenarioError(
            f"receivable_id '{receivable_id}' not found in financial state"
        )

    @staticmethod
    def _require_supplier(financial_state: FinancialState, supplier_id: str):
        for s in financial_state.supplier_risks:
            if s.supplier_id == supplier_id:
                return s
        raise InvalidScenarioError(
            f"supplier_id '{supplier_id}' not found in financial state"
        )

    @staticmethod
    def _require_financing(financial_state: FinancialState, financing_id: str):
        for f in financial_state.financing_options:
            if f.id == financing_id:
                return f
        raise InvalidScenarioError(
            f"financing_id '{financing_id}' not found in financial state"
        )
