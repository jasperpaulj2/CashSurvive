"""
risk_engine.py
==============
Transparent, deterministic, configurably-weighted risk scoring.

No machine learning and no randomness: every score is derived directly from
the numbers in the supplied FinancialState, using the weights and
thresholds defined in config.py.
"""

from __future__ import annotations

from typing import Dict, List

from .config import (
    RISK_WEIGHTS,
    RISK_LEVELS,
    TARGET_LIQUIDITY_RATIO,
    BASE_FINANCING_RATE,
    EPSILON,
)
from .exceptions import InvalidRiskInputError
from .models import FinancialState, RiskResult, RiskLevel


class RiskEngine:
    """Calculates a transparent, explainable 0-100 risk score for a given
    FinancialState using a fixed set of weighted risk factors."""

    def __init__(self, weights: Dict[str, float] = None) -> None:
        self.weights = weights or RISK_WEIGHTS
        total = sum(self.weights.values())
        if abs(total - 1.0) > 1e-6:
            raise InvalidRiskInputError(
                f"RISK_WEIGHTS must sum to 1.0, got {total}"
            )

    # -- public API ----------------------------------------------------
    def calculate_risk(self, financial_state: FinancialState) -> RiskResult:
        """Compute the overall risk score/level for a FinancialState."""
        if financial_state is None:
            raise InvalidRiskInputError("financial_state must not be None")
        if financial_state.minimum_cash_reserve <= 0:
            raise InvalidRiskInputError(
                "minimum_cash_reserve must be > 0 to compute liquidity risk"
            )

        liquidity_risk, liquidity_ratio = self._liquidity_risk(financial_state)
        receivable_risk = self._receivable_risk(financial_state)
        supplier_risk = self._supplier_risk(financial_state)
        obligation_risk = self._obligation_risk(financial_state)
        financing_risk = self._financing_risk(financial_state)

        breakdown = {
            "liquidity": round(liquidity_risk, 2),
            "receivable": round(receivable_risk, 2),
            "supplier": round(supplier_risk, 2),
            "obligation": round(obligation_risk, 2),
            "financing": round(financing_risk, 2),
        }

        risk_score = (
            self.weights["liquidity"] * liquidity_risk
            + self.weights["receivable"] * receivable_risk
            + self.weights["supplier"] * supplier_risk
            + self.weights["obligation"] * obligation_risk
            + self.weights["financing"] * financing_risk
        )
        risk_score = round(max(0.0, min(100.0, risk_score)), 2)
        risk_level = self._risk_level(risk_score)

        risk_factors = self._build_risk_factors(
            breakdown, liquidity_ratio, financial_state
        )
        explanation = (
            f"Overall risk score is {risk_score}/100 ({risk_level.value}), "
            f"driven primarily by "
            f"{self._dominant_factor(breakdown)} risk."
        )

        return RiskResult(
            risk_score=risk_score,
            risk_level=risk_level,
            risk_factors=risk_factors,
            explanation=explanation,
            factor_breakdown=breakdown,
        )

    # -- risk level lookup ----------------------------------------------
    @staticmethod
    def _risk_level(score: float) -> RiskLevel:
        for level_name, (low, high) in RISK_LEVELS.items():
            if low <= score <= high:
                return RiskLevel(level_name)
        # Score above the highest defined band (shouldn't happen given
        # clamping, but fail safe to CRITICAL).
        return RiskLevel.CRITICAL

    # -- individual factor calculations ----------------------------------
    @staticmethod
    def project_cash(financial_state: FinancialState) -> float:
        """Deterministic baseline cash projection: current cash plus
        probability-weighted receivables, minus confirmed payables and
        upcoming obligations."""
        expected_receivables = sum(
            r.amount * r.probability for r in financial_state.receivables
        )
        total_payables = sum(p.amount for p in financial_state.payables)
        total_obligations = sum(
            o.amount for o in financial_state.upcoming_obligations
        )
        return (
            financial_state.cash_balance
            + expected_receivables
            - total_payables
            - total_obligations
        )

    def _liquidity_risk(self, financial_state: FinancialState) -> (float, float):
        projected_cash = self.project_cash(financial_state)
        ratio = projected_cash / max(
            financial_state.minimum_cash_reserve, EPSILON
        )
        # ratio >= TARGET_LIQUIDITY_RATIO -> risk 0
        # ratio <= 0 -> risk 100
        # linear in between
        if ratio >= TARGET_LIQUIDITY_RATIO:
            risk = 0.0
        elif ratio <= 0:
            risk = 100.0
        else:
            risk = (
                (TARGET_LIQUIDITY_RATIO - ratio) / TARGET_LIQUIDITY_RATIO
            ) * 100.0
        return risk, ratio

    @staticmethod
    def _receivable_risk(financial_state: FinancialState) -> float:
        receivables = financial_state.receivables
        if not receivables:
            return 0.0
        total_amount = sum(r.amount for r in receivables)
        if total_amount <= 0:
            return 0.0
        weighted_risk = sum(
            (r.amount / total_amount) * (1.0 - r.probability) * 100.0
            for r in receivables
        )
        return max(0.0, min(100.0, weighted_risk))

    @staticmethod
    def _supplier_risk(financial_state: FinancialState) -> float:
        suppliers = financial_state.supplier_risks
        if not suppliers:
            return 0.0
        # Worst-case supplier drives the score: a single critical, fragile
        # supplier should visibly raise risk even if others are healthy.
        worst = max(
            s.liquidity_risk * 100.0 * ((s.importance + s.dependency) / 2.0)
            for s in suppliers
        )
        return max(0.0, min(100.0, worst))

    @staticmethod
    def _obligation_risk(financial_state: FinancialState) -> float:
        total_obligations = sum(
            o.amount for o in financial_state.upcoming_obligations
        )
        total_payables = sum(p.amount for p in financial_state.payables)
        near_term_outflow = total_obligations + total_payables
        denom = max(financial_state.cash_balance, EPSILON)
        ratio = near_term_outflow / denom
        return max(0.0, min(100.0, ratio * 100.0))

    @staticmethod
    def _financing_risk(financial_state: FinancialState) -> float:
        options = financial_state.financing_options
        if not options:
            return 0.0
        worst_increase = max(
            (o.interest_rate - BASE_FINANCING_RATE) / BASE_FINANCING_RATE
            for o in options
        )
        return max(0.0, min(100.0, worst_increase * 100.0))

    # -- explanation helpers ----------------------------------------------
    @staticmethod
    def _dominant_factor(breakdown: Dict[str, float]) -> str:
        return max(breakdown, key=breakdown.get)

    @staticmethod
    def _build_risk_factors(
        breakdown: Dict[str, float],
        liquidity_ratio: float,
        financial_state: FinancialState,
    ) -> List[str]:
        factors: List[str] = []

        if breakdown["liquidity"] >= 50:
            factors.append(
                f"Liquidity buffer is stressed: projected cash covers only "
                f"{liquidity_ratio:.2f}x the minimum cash reserve."
            )
        elif breakdown["liquidity"] >= 25:
            factors.append(
                "Liquidity buffer is approaching the minimum reserve level."
            )

        if breakdown["receivable"] >= 40:
            factors.append(
                "A significant portion of expected receivables carry low "
                "collection probability."
            )

        if breakdown["supplier"] >= 40:
            risky = [
                s.name
                for s in financial_state.supplier_risks
                if s.liquidity_risk >= 0.5
            ]
            if risky:
                factors.append(
                    f"Critical supplier(s) with elevated liquidity risk: "
                    f"{', '.join(risky)}."
                )
            else:
                factors.append("Supplier risk exposure is elevated.")

        if breakdown["obligation"] >= 50:
            factors.append(
                "Upcoming obligations and payables are large relative to "
                "current cash balance."
            )

        if breakdown["financing"] >= 30:
            factors.append(
                "Available financing options carry interest rates well "
                "above the baseline rate."
            )

        if not factors:
            factors.append("No individual risk factor is significantly elevated.")

        return factors
