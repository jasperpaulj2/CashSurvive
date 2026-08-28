"""
CashSurvive Integration Package
===============================
Connects:
- Member 1: Financial State
- Member 2: Forecasting Engine
- Member 3: Scenario & Risk Engine
- Member 4: Optimization Engine (Extension Hook)
"""

import integration._path_setup  # noqa: F401

from integration.financial_to_forecast import (
    convert_receivables_to_invoices,
    convert_payables_and_obligations_to_cash_flow_items,
    build_receivable_forecaster,
    build_cash_flow_forecaster,
    run_forecasting,
)
from integration.forecast_to_scenario import (
    convert_financial_state_to_scenario_model,
)
from integration.scenario_to_risk import (
    run_scenario_and_risk_analysis,
)
from integration.adapters.optimization_adapter import (
    OptimizationEngineExtension,
    NoOpOptimizationAdapter,
)
from integration.pipeline import run_pipeline

__all__ = [
    "convert_receivables_to_invoices",
    "convert_payables_and_obligations_to_cash_flow_items",
    "build_receivable_forecaster",
    "build_cash_flow_forecaster",
    "run_forecasting",
    "convert_financial_state_to_scenario_model",
    "run_scenario_and_risk_analysis",
    "OptimizationEngineExtension",
    "NoOpOptimizationAdapter",
    "run_pipeline",
]