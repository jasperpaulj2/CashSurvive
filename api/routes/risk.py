"""
risk.py
=======
Routes for executing standalone Member 3 risk evaluation logic.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import integration._path_setup  # noqa: F401
from data.database import get_db
from services.financial_state import get_financial_state
from integration.forecast_to_scenario import convert_financial_state_to_scenario_model
from scenario_risk_engine.risk_engine import RiskEngine
from api.schemas.requests import RiskRequest

router = APIRouter(prefix="/api/risk", tags=["Risk Engine (Member 3)"])


@router.post(
    "",
    summary="Evaluate Financial Risk",
    description="Calculates a transparent 0-100 risk score, risk level, factor breakdown (liquidity, receivable, supplier, obligation, financing), and human-readable risk drivers.",
)
def evaluate_risk(
    request: RiskRequest,
    db: Session = Depends(get_db),
):
    try:
        if request.financial_state is not None:
            m1_state = request.financial_state
        else:
            m1_state = get_financial_state(db, as_of=request.as_of)

        eval_as_of = request.as_of or m1_state.as_of
        m3_state = convert_financial_state_to_scenario_model(m1_state, as_of=eval_as_of)

        risk_engine = RiskEngine()
        risk_result = risk_engine.calculate_risk(m3_state)

        return {
            "status": "success",
            "as_of": eval_as_of.isoformat() if eval_as_of else None,
            "risk": risk_result.to_dict(),
        }
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Risk evaluation failed: {str(exc)}",
        ) from exc
