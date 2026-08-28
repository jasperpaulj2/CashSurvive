"""
API routes package
"""

from api.routes.health import router as health_router
from api.routes.financial_state import router as financial_state_router
from api.routes.forecast import router as forecast_router
from api.routes.scenario import router as scenario_router
from api.routes.risk import router as risk_router
from api.routes.pipeline import router as pipeline_router

__all__ = [
    "health_router",
    "financial_state_router",
    "forecast_router",
    "scenario_router",
    "risk_router",
    "pipeline_router",
]
