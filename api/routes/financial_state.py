"""
financial_state.py
==================
Routes for querying and seeding Member 1 Financial State.
"""

from __future__ import annotations

import datetime as dt
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

import integration._path_setup  # noqa: F401
from data.database import get_db, init_db
from data.schemas import FinancialState
from data.seed_data import seed
from services.financial_state import get_financial_state
from api.schemas.responses import SeedResponse

router = APIRouter(prefix="/api/financial-state", tags=["Financial State (Member 1)"])


@router.get(
    "",
    response_model=FinancialState,
    summary="Get Current Financial State",
    description="Assembles the company's current financial position (cash, receivables, payables, obligations, suppliers, financing) from the database.",
)
def read_financial_state(
    as_of: Optional[dt.date] = Query(
        default=None,
        description="Optional calculation date. Defaults to current date.",
    ),
    db: Session = Depends(get_db),
):
    try:
        return get_financial_state(db, as_of=as_of)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{str(exc)} Please run POST /api/financial-state/seed to populate initial demo data.",
        ) from exc


@router.post(
    "/seed",
    response_model=SeedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Seed Demo Financial State",
    description="Initializes the SQLite database and populates it with realistic demo records for Aarav Textiles Pvt Ltd.",
)
def seed_demo_data():
    init_db()
    seed()
    return SeedResponse(
        status="success",
        message="Demo company financial state seeded successfully.",
        company_name="Aarav Textiles Pvt Ltd",
    )
