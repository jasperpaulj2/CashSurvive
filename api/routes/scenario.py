"""
scenario.py
===========
Routes for executing standalone Member 3 stress scenario simulation.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import integration._path_setup  # noqa: F401
from data.database import get_db
from services.financial_state import get_financial_state
from integration.forecast_to_scenario import convert_financial_state_to_scenario_model
from integration.scenario_to_risk import run_scenario_and_risk_analysis
from api.schemas.requests import ScenarioRequest

router = APIRouter(prefix="/api/scenarios", tags=["Scenario Engine (Member 3)"])


@router.post(
    "",
    summary="Simulate Stress Scenarios",
    description="Simulates standard stress scenarios (Baseline/Normal, Receivable Delay, Cash Shock, Supplier Stress, Financing Shock) and projects the cash impact and liquidity status for each.",
)
def run_scenarios(
    request: ScenarioRequest,
    db: Session = Depends(get_db),
):
    try:
        if request.financial_state is not None:
            m1_state = request.financial_state
        else:
            m1_state = get_financial_state(db, as_of=request.as_of)

        eval_as_of = request.as_of or m1_state.as_of
        m3_state = convert_financial_state_to_scenario_model(m1_state, as_of=eval_as_of)

        analysis = run_scenario_and_risk_analysis(m3_state)

        return {
            "status": "success",
            "as_of": eval_as_of.isoformat() if eval_as_of else None,
            "scenarios": analysis["scenarios"],
        }
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scenario evaluation failed: {str(exc)}",
        ) from exc
