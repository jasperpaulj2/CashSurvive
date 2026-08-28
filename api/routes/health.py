"""
health.py
=========
Root and health check endpoints for CashSurvive API.
"""

from __future__ import annotations

import datetime as dt
from fastapi import APIRouter
from api.schemas.responses import HealthResponse

router = APIRouter(tags=["System & Health"])


@router.get(
    "/",
    summary="API Root Information",
    description="Returns service metadata, status, and link to OpenAPI documentation.",
)
def root():
    return {
        "app": "CASH SURVIVE API",
        "description": "Autonomous cash flow forecasting, stress scenario simulation, and risk engine backend.",
        "version": "1.0.0",
        "status": "online",
        "docs_url": "/docs",
        "health_url": "/health",
        "pipeline_url": "/api/pipeline/run",
    }


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health & Module Availability Check",
    description="Performs a fast, non-blocking check on backend modules and database availability.",
)
def health():
    modules = {}

    # Check Member 1 (Financial State)
    try:
        from data.schemas import FinancialState  # noqa: F401
        from data.database import engine  # noqa: F401
        modules["financial_state_member_1"] = "available"
    except Exception as e:
        modules["financial_state_member_1"] = f"unavailable: {str(e)}"

    # Check Member 2 (Forecasting Engine)
    try:
        from receivable_forecast import ReceivableForecaster  # noqa: F401
        from cash_forecast import CashFlowForecaster  # noqa: F401
        modules["forecasting_engine_member_2"] = "available"
    except Exception as e:
        modules["forecasting_engine_member_2"] = f"unavailable: {str(e)}"

    # Check Member 3 (Scenario & Risk Engine)
    try:
        from scenario_risk_engine.scenario_engine import ScenarioEngine  # noqa: F401
        from scenario_risk_engine.risk_engine import RiskEngine  # noqa: F401
        modules["scenario_risk_engine_member_3"] = "available"
    except Exception as e:
        modules["scenario_risk_engine_member_3"] = f"unavailable: {str(e)}"

    # Check Member 4 (Optimization Hook)
    modules["optimization_engine_member_4"] = "extension_hook_ready (not_implemented)"

    is_healthy = all(
        v == "available"
        for k, v in modules.items()
        if k != "optimization_engine_member_4"
    )

    return HealthResponse(
        status="healthy" if is_healthy else "degraded",
        version="1.0.0",
        modules=modules,
        timestamp=dt.datetime.now(dt.timezone.utc).isoformat(),
    )
