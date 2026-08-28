"""
models.py
=========
Data models for the Scenario & Risk Engine.

Plain Python dataclasses are used (no external dependency required) so that
this module can run independently and be trivially serialised to JSON for
the eventual API layer. Every model exposes a `to_dict()` helper for that
purpose.

These models are intentionally loose/adaptable: Member 1's FinancialState
payload may not match this exactly, so `FinancialState.from_dict()` is
tolerant of missing optional fields and extra keys.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional

from .exceptions import InvalidFinancialStateError, InvalidScenarioError


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------
class ScenarioType(str, Enum):
    NORMAL = "NORMAL"
    RECEIVABLE_DELAY = "RECEIVABLE_DELAY"
    CASH_SHOCK = "CASH_SHOCK"
    SUPPLIER_STRESS = "SUPPLIER_STRESS"
    FINANCING_SHOCK = "FINANCING_SHOCK"


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class LiquidityStatus(str, Enum):
    HEALTHY = "HEALTHY"
    TIGHT = "TIGHT"
    BELOW_MINIMUM = "BELOW_MINIMUM"
    NEGATIVE = "NEGATIVE"


# ---------------------------------------------------------------------------
# Base mixin
# ---------------------------------------------------------------------------
class _DictMixin:
    """Provides a generic to_dict() for any dataclass, converting Enums to
    their plain string value so the result is JSON-serialisable."""

    def to_dict(self) -> Dict[str, Any]:
        def _convert(obj: Any) -> Any:
            if isinstance(obj, Enum):
                return obj.value
            if isinstance(obj, list):
                return [_convert(v) for v in obj]
            if isinstance(obj, dict):
                return {k: _convert(v) for k, v in obj.items()}
            if hasattr(obj, "to_dict"):
                return obj.to_dict()
            return obj

        return {k: _convert(v) for k, v in asdict(self).items()}


# ---------------------------------------------------------------------------
# FinancialState sub-components
# ---------------------------------------------------------------------------
@dataclass
class Receivable(_DictMixin):
    """A single expected incoming payment."""

    id: str
    amount: float
    expected_days: int  # days from now until expected receipt
    probability: float = 1.0  # 0.0 - 1.0 probability of on-time collection
    description: str = ""

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise InvalidFinancialStateError(
                f"Receivable '{self.id}' has negative amount: {self.amount}"
            )
        if not 0.0 <= self.probability <= 1.0:
            raise InvalidFinancialStateError(
                f"Receivable '{self.id}' probability must be in [0,1], "
                f"got {self.probability}"
            )


@dataclass
class Payable(_DictMixin):
    """A single confirmed outgoing payment owed to a supplier/vendor."""

    id: str
    amount: float
    due_days: int
    description: str = ""

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise InvalidFinancialStateError(
                f"Payable '{self.id}' has negative amount: {self.amount}"
            )


@dataclass
class Obligation(_DictMixin):
    """A confirmed or contractual upcoming obligation (loan repayment,
    tax, payroll, etc.) distinct from a trade payable."""

    id: str
    amount: float
    due_days: int
    description: str = ""

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise InvalidFinancialStateError(
                f"Obligation '{self.id}' has negative amount: {self.amount}"
            )


@dataclass
class SupplierRisk(_DictMixin):
    """Risk profile of a supplier the company depends on."""

    supplier_id: str
    name: str
    importance: float  # 0.0 - 1.0, how critical this supplier is
    liquidity_risk: float  # 0.0 - 1.0, likelihood supplier is in distress
    dependency: float = 0.5  # 0.0 - 1.0, how hard to replace this supplier

    def __post_init__(self) -> None:
        for attr_name in ("importance", "liquidity_risk", "dependency"):
            value = getattr(self, attr_name)
            if not 0.0 <= value <= 1.0:
                raise InvalidFinancialStateError(
                    f"SupplierRisk '{self.supplier_id}'.{attr_name} must be "
                    f"in [0,1], got {value}"
                )


@dataclass
class FinancingOption(_DictMixin):
    """An available financing/borrowing facility."""

    id: str
    available_amount: float
    interest_rate: float  # annualised, e.g. 0.08 == 8%
    description: str = ""

    def __post_init__(self) -> None:
        if self.available_amount < 0:
            raise InvalidFinancialStateError(
                f"FinancingOption '{self.id}' has negative available_amount"
            )
        if self.interest_rate < 0:
            raise InvalidFinancialStateError(
                f"FinancingOption '{self.id}' has negative interest_rate"
            )


# ---------------------------------------------------------------------------
# FinancialState
# ---------------------------------------------------------------------------
@dataclass
class FinancialState(_DictMixin):
    """A snapshot of the company's financial position.

    This is intentionally adaptable: Member 1's real payload structure is
    unknown at the time of writing, so `from_dict()` fills in sensible
    defaults for any missing optional collections.
    """

    cash_balance: float
    minimum_cash_reserve: float
    receivables: List[Receivable] = field(default_factory=list)
    payables: List[Payable] = field(default_factory=list)
    upcoming_obligations: List[Obligation] = field(default_factory=list)
    supplier_risks: List[SupplierRisk] = field(default_factory=list)
    financing_options: List[FinancingOption] = field(default_factory=list)
    as_of: Optional[str] = None  # ISO timestamp label, optional metadata

    def __post_init__(self) -> None:
        if self.cash_balance < 0:
            raise InvalidFinancialStateError(
                f"cash_balance cannot be negative, got {self.cash_balance}"
            )
        if self.minimum_cash_reserve < 0:
            raise InvalidFinancialStateError(
                "minimum_cash_reserve cannot be negative, got "
                f"{self.minimum_cash_reserve}"
            )

    # -- convenience constructors -----------------------------------------
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "FinancialState":
        """Tolerantly build a FinancialState from a plain dict (e.g. the
        payload received from Member 1's module)."""
        if data is None:
            raise InvalidFinancialStateError("financial state payload is None")
        try:
            receivables = [
                r if isinstance(r, Receivable) else Receivable(**r)
                for r in data.get("receivables", []) or []
            ]
            payables = [
                p if isinstance(p, Payable) else Payable(**p)
                for p in data.get("payables", []) or []
            ]
            obligations = [
                o if isinstance(o, Obligation) else Obligation(**o)
                for o in data.get("upcoming_obligations", []) or []
            ]
            supplier_risks = [
                s if isinstance(s, SupplierRisk) else SupplierRisk(**s)
                for s in data.get("supplier_risks", []) or []
            ]
            financing_options = [
                f if isinstance(f, FinancingOption) else FinancingOption(**f)
                for f in data.get("financing_options", []) or []
            ]
        except TypeError as exc:
            raise InvalidFinancialStateError(
                f"Malformed nested item in financial state payload: {exc}"
            ) from exc

        if "cash_balance" not in data or "minimum_cash_reserve" not in data:
            raise InvalidFinancialStateError(
                "financial state payload must include 'cash_balance' and "
                "'minimum_cash_reserve'"
            )

        return FinancialState(
            cash_balance=data["cash_balance"],
            minimum_cash_reserve=data["minimum_cash_reserve"],
            receivables=receivables,
            payables=payables,
            upcoming_obligations=obligations,
            supplier_risks=supplier_risks,
            financing_options=financing_options,
            as_of=data.get("as_of"),
        )

    def copy(self) -> "FinancialState":
        """Deep-ish copy sufficient for scenario mutation (new list/objects,
        no shared mutable references back to the original)."""
        return FinancialState(
            cash_balance=self.cash_balance,
            minimum_cash_reserve=self.minimum_cash_reserve,
            receivables=[Receivable(**asdict(r)) for r in self.receivables],
            payables=[Payable(**asdict(p)) for p in self.payables],
            upcoming_obligations=[
                Obligation(**asdict(o)) for o in self.upcoming_obligations
            ],
            supplier_risks=[
                SupplierRisk(**asdict(s)) for s in self.supplier_risks
            ],
            financing_options=[
                FinancingOption(**asdict(f)) for f in self.financing_options
            ],
            as_of=self.as_of,
        )


# ---------------------------------------------------------------------------
# Scenario
# ---------------------------------------------------------------------------
@dataclass
class Scenario(_DictMixin):
    scenario_id: str
    name: str
    scenario_type: ScenarioType
    severity: Severity
    parameters: Dict[str, Any] = field(default_factory=dict)
    description: str = ""

    def __post_init__(self) -> None:
        if not self.scenario_id:
            raise InvalidScenarioError("scenario_id must not be empty")
        if not isinstance(self.scenario_type, ScenarioType):
            try:
                self.scenario_type = ScenarioType(self.scenario_type)
            except ValueError as exc:
                raise InvalidScenarioError(
                    f"Unknown scenario_type: {self.scenario_type}"
                ) from exc
        if not isinstance(self.severity, Severity):
            try:
                self.severity = Severity(self.severity)
            except ValueError as exc:
                raise InvalidScenarioError(
                    f"Unknown severity: {self.severity}"
                ) from exc


# ---------------------------------------------------------------------------
# ScenarioResult
# ---------------------------------------------------------------------------
@dataclass
class ScenarioResult(_DictMixin):
    scenario_id: str
    projected_cash: float
    cash_impact: float
    liquidity_ratio: float
    liquidity_status: LiquidityStatus
    risk_score: float
    risk_level: RiskLevel
    affected_items: List[str] = field(default_factory=list)
    description: str = ""


# ---------------------------------------------------------------------------
# RiskResult
# ---------------------------------------------------------------------------
@dataclass
class RiskResult(_DictMixin):
    risk_score: float
    risk_level: RiskLevel
    risk_factors: List[str] = field(default_factory=list)
    explanation: str = ""
    factor_breakdown: Dict[str, float] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# ShockEvent
# ---------------------------------------------------------------------------
@dataclass
class ShockEvent(_DictMixin):
    event_id: str
    shock_type: str
    severity: Severity
    detected: bool
    reason: str
    changes: Dict[str, Any] = field(default_factory=dict)
    reoptimize: bool = False
