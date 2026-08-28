"""
forecast.py
===========
Routes for executing standalone Member 2 forecasting logic.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import integration._path_setup  # noqa: F401
from data.database import get_db
from services.financial_state import get_financial_state
from integration.financial_to_forecast import run_forecasting
from api.schemas.requests import ForecastRequest

router = APIRouter(prefix="/api/forecast", tags=["Forecasting Engine (Member 2)"])


@router.post(
    "",
    summary="Run Standalone Cash & AR Forecast",
    description="Generates day-by-day cash balance projections, Monte Carlo confidence intervals, shortfall runway, AR collection schedule, aging report, and customer risk scores.",
)
def generate_forecast(
    request: ForecastRequest,
    db: Session = Depends(get_db),
):
    try:
        if request.financial_state is not None:
            m1_state = request.financial_state
        else:
            m1_state = get_financial_state(db, as_of=request.as_of)

        eval_as_of = request.as_of or m1_state.as_of

        forecast_data = run_forecasting(
            financial_state=m1_state,
            horizon_days=request.horizon_days,
            num_simulations=request.num_simulations,
            confidence_level=request.confidence_level,
            as_of=eval_as_of,
        )
        return {
            "status": "success",
            "as_of": eval_as_of.isoformat() if eval_as_of else None,
            "horizon_days": request.horizon_days,
            **forecast_data,
        }
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Forecasting calculation failed: {str(exc)}",
        ) from exc
