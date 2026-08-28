"""
pipeline.py
===========
Unified integration pipeline orchestrating all three backend modules:

Member 1 (Financial State)
      ↓
Member 2 (Forecasting Engine)
      ↓
Member 3 (Scenario Generation & Risk Evaluation)
      ↓
Member 4 (Optimization Hook - Extension Point)
      ↓
Unified Result
"""

from __future__ import annotations

import datetime as dt
import logging
from typing import Any, Dict, Optional, Union

import integration._path_setup  # noqa: F401

from data.database import SessionLocal, init_db
from data.schemas import FinancialState
from services.financial_state import get_financial_state
from integration.financial_to_forecast import run_forecasting
from integration.forecast_to_scenario import convert_financial_state_to_scenario_model
from integration.scenario_to_risk import run_scenario_and_risk_analysis
from integration.adapters.optimization_adapter import (
    OptimizationEngineExtension,
    NoOpOptimizationAdapter,
)

logger = logging.getLogger("cashsurvive.pipeline")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def _serialize_financial_state(state: FinancialState) -> Dict[str, Any]:
    """Helper to convert Pydantic FinancialState to a JSON-safe dictionary."""
    if hasattr(state, "model_dump"):
        return state.model_dump(mode="json")
    elif hasattr(state, "dict"):
        return state.dict()
    return dict(state)


def run_pipeline(
    financial_state: Optional[Union[FinancialState, Dict[str, Any]]] = None,
    horizon_days: int = 30,
    num_simulations: int = 2000,
    confidence_level: float = 0.90,
    as_of: Optional[dt.date] = None,
    previous_state: Optional[Union[FinancialState, Dict[str, Any]]] = None,
    optimization_adapter: Optional[OptimizationEngineExtension] = None,
) -> Dict[str, Any]:
    """
    Executes the complete end-to-end CashSurvive pipeline across all modules.

    Parameters:
        financial_state: Optional explicit FinancialState or payload dict. If omitted,
                         loads the company financial state from the SQLite database.
        horizon_days: Number of days to forecast (default 30).
        num_simulations: Monte Carlo path count (default 2000).
        confidence_level: Confidence level for uncertainty bands (default 0.90).
        as_of: Evaluation date anchor (defaults to financial_state.as_of or today).
        previous_state: Optional previous snapshot for shock detection.
        optimization_adapter: Optional custom Member 4 optimization engine.

    Returns:
        UnifiedResult dictionary containing:
        - status: "success"
        - financial_state: current company position snapshot
        - forecast: projections, Monte Carlo bands, summary, aging, customer risk
        - scenarios: stress scenarios evaluated with projected cash & risk
        - risk: baseline risk score, factor breakdown, explanations
        - shocks: list of detected shocks (if previous_state provided)
        - reoptimization_required: boolean flag
        - optimization_extension: Member 4 hook result
    """
    logger.info("=== Starting CashSurvive Integrated Pipeline ===")

    # -------------------------------------------------------------
    # STAGE 1: Load / Validate Member 1 Financial State
    # -------------------------------------------------------------
    logger.info("Stage 1: Resolving Financial State (Member 1)...")
    if financial_state is None:
        init_db()
        db = SessionLocal()
        try:
            m1_state = get_financial_state(db, as_of=as_of)
        finally:
            db.close()
    elif isinstance(financial_state, dict):
        m1_state = FinancialState.model_validate(financial_state)
    elif isinstance(financial_state, FinancialState):
        m1_state = financial_state
    else:
        raise TypeError(
            f"Expected FinancialState or dict, got {type(financial_state).__name__}"
        )

    eval_as_of = as_of or m1_state.as_of
    logger.info(
        f"Financial State loaded: Cash={m1_state.current_cash:,.2f} {m1_state.currency}, "
        f"Reserve={m1_state.minimum_cash_reserve:,.2f} {m1_state.currency}, "
        f"Receivables count={len(m1_state.receivables)}, "
        f"Payables count={len(m1_state.payables)}"
    )

    # -------------------------------------------------------------
    # STAGE 2: Execute Member 2 Forecasting Engine
    # -------------------------------------------------------------
    logger.info(
        f"Stage 2: Executing Forecasting Engine (Member 2) [Horizon={horizon_days}d, Sims={num_simulations}]..."
    )
    forecast_results = run_forecasting(
        financial_state=m1_state,
        horizon_days=horizon_days,
        num_simulations=num_simulations,
        confidence_level=confidence_level,
        as_of=eval_as_of,
    )
    logger.info(
        f"Forecast completed: Ending Balance={forecast_results['summary']['ending_balance']:,.2f}, "
        f"Runway={forecast_results['summary']['runway_days']} days, "
        f"Shortfall Prob={forecast_results['summary']['probability_of_shortfall_pct']}%"
    )

    # -------------------------------------------------------------
    # STAGE 3 & 4: Adapt and Execute Member 3 Scenario & Risk Engine
    # -------------------------------------------------------------
    logger.info("Stage 3 & 4: Adapting to Scenario & Risk Engine (Member 3)...")
    m3_current_state = convert_financial_state_to_scenario_model(
        m1_state, as_of=eval_as_of
    )

    m3_previous_state = None
    if previous_state is not None:
        if isinstance(previous_state, dict):
            prev_m1 = FinancialState.model_validate(previous_state)
        else:
            prev_m1 = previous_state
        m3_previous_state = convert_financial_state_to_scenario_model(
            prev_m1, as_of=eval_as_of
        )

    scenario_risk_results = run_scenario_and_risk_analysis(
        m3_state=m3_current_state,
        previous_state=m3_previous_state,
    )
    logger.info(
        f"Scenario & Risk analysis completed: Baseline Risk Score={scenario_risk_results['baseline_risk']['risk_score']}/100 "
        f"({scenario_risk_results['baseline_risk']['risk_level']}), "
        f"Evaluated {len(scenario_risk_results['scenarios'])} scenarios"
    )

    # -------------------------------------------------------------
    # STAGE 5: Member 4 Optimization Hook (Extension Point)
    # -------------------------------------------------------------
    logger.info("Stage 5: Invoking Member 4 Optimization Extension Point...")
    opt_adapter = optimization_adapter or NoOpOptimizationAdapter()
    pipeline_context = {
        "financial_state": _serialize_financial_state(m1_state),
        "forecast": forecast_results,
        "scenarios": scenario_risk_results["scenarios"],
        "risk": scenario_risk_results["baseline_risk"],
    }
    opt_result = opt_adapter.optimize(pipeline_context)

    # -------------------------------------------------------------
    # ASSEMBLE UNIFIED RESULT
    # -------------------------------------------------------------
    logger.info("=== Pipeline Execution Succeeded ===")

    return {
        "status": "success",
        "financial_state": _serialize_financial_state(m1_state),
        "forecast": forecast_results,
        "scenarios": scenario_risk_results["scenarios"],
        "risk": scenario_risk_results["baseline_risk"],
        "shocks": scenario_risk_results["shocks"],
        "reoptimization_required": scenario_risk_results["reoptimization_required"],
        "optimization_extension": opt_result,
    }
