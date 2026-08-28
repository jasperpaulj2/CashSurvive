"""
scenario_risk_engine
=====================
Member 3's backend module for CashSurvive AI: Scenario Generation,
Risk Scoring, and Material Change (Shock) Detection.

Public API:

    from scenario_risk_engine import (
        FinancialState, Receivable, Payable, Obligation,
        SupplierRisk, FinancingOption,
        Scenario, ScenarioResult, RiskResult, ShockEvent,
        ScenarioEngine, RiskEngine, ShockDetector,
    )
"""

from .models import (
    FinancialState,
    Receivable,
    Payable,
    Obligation,
    SupplierRisk,
    FinancingOption,
    Scenario,
    ScenarioResult,
    RiskResult,
    ShockEvent,
    ScenarioType,
    Severity,
    RiskLevel,
    LiquidityStatus,
)
from .scenario_engine import ScenarioEngine
from .risk_engine import RiskEngine
from .shock_detector import ShockDetector
from .exceptions import (
    ScenarioRiskEngineError,
    InvalidFinancialStateError,
    InvalidScenarioError,
    InvalidRiskInputError,
)

__all__ = [
    "FinancialState",
    "Receivable",
    "Payable",
    "Obligation",
    "SupplierRisk",
    "FinancingOption",
    "Scenario",
    "ScenarioResult",
    "RiskResult",
    "ShockEvent",
    "ScenarioType",
    "Severity",
    "RiskLevel",
    "LiquidityStatus",
    "ScenarioEngine",
    "RiskEngine",
    "ShockDetector",
    "ScenarioRiskEngineError",
    "InvalidFinancialStateError",
    "InvalidScenarioError",
    "InvalidRiskInputError",
]

__version__ = "1.0.0"
