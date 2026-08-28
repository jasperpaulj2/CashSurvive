"""
pipeline.py
===========
Primary unified pipeline route executing all CashSurvive backend modules.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

import integration._path_setup  # noqa: F401
from integration.pipeline import run_pipeline
from api.schemas.requests import PipelineRunRequest

router = APIRouter(prefix="/api/pipeline", tags=["Unified Pipeline"])


@router.post(
    "/run",
    summary="Run Complete Unified Pipeline",
    description="Orchestrates Member 1 (Financial State) -> Member 2 (Forecasting) -> Member 3 (Scenario & Risk) -> Member 4 (Optimization Hook) into a single unified JSON result.",
)
def execute_pipeline(request: PipelineRunRequest):
    try:
        result = run_pipeline(
            financial_state=request.financial_state,
            horizon_days=request.horizon_days,
            num_simulations=request.num_simulations,
            confidence_level=request.confidence_level,
            as_of=request.as_of,
            previous_state=request.previous_state,
        )
        return result
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline execution failed: {str(exc)}",
        ) from exc
