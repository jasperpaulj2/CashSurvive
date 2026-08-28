"""
requests.py
===========
Pydantic v2 request validation schemas for CashSurvive API endpoints.
Reuses existing Member 1 FinancialState schema to prevent schema duplication.
"""

from __future__ import annotations

import datetime as dt
from typing import Optional
from pydantic import BaseModel, Field

import integration._path_setup  # noqa: F401
from data.schemas import FinancialState


class PipelineRunRequest(BaseModel):
    """Request body for POST /api/pipeline/run"""

    horizon_days: int = Field(
        default=30,
        ge=1,
        le=365,
        description="Forecast horizon in days (1 to 365).",
    )
    num_simulations: int = Field(
        default=2000,
        ge=100,
        le=20000,
        description="Monte Carlo simulation iterations for uncertainty modeling.",
    )
    confidence_level: float = Field(
        default=0.90,
        ge=0.50,
        le=0.99,
        description="Confidence level for uncertainty envelopes (0.50 to 0.99).",
    )
    as_of: Optional[dt.date] = Field(
        default=None,
        description="Optional evaluation date anchor. Defaults to financial state as_of date or current date.",
    )
    financial_state: Optional[FinancialState] = Field(
        default=None,
        description="Optional custom FinancialState snapshot. If omitted, loads latest state from the database.",
    )
    previous_state: Optional[FinancialState] = Field(
        default=None,
        description="Optional previous FinancialState snapshot for shock detection.",
    )


class ForecastRequest(BaseModel):
    """Request body for POST /api/forecast"""

    horizon_days: int = Field(
        default=30,
        ge=1,
        le=365,
        description="Forecast horizon in days.",
    )
    num_simulations: int = Field(
        default=2000,
        ge=100,
        le=20000,
        description="Monte Carlo simulation count.",
    )
    confidence_level: float = Field(
        default=0.90,
        ge=0.50,
        le=0.99,
        description="Confidence level for uncertainty bounds.",
    )
    as_of: Optional[dt.date] = Field(
        default=None,
        description="Evaluation date.",
    )
    financial_state: Optional[FinancialState] = Field(
        default=None,
        description="Optional custom financial state. If omitted, loads from database.",
    )


class ScenarioRequest(BaseModel):
    """Request body for POST /api/scenarios"""

    as_of: Optional[dt.date] = Field(
        default=None,
        description="Evaluation date.",
    )
    financial_state: Optional[FinancialState] = Field(
        default=None,
        description="Optional custom financial state. If omitted, loads from database.",
    )


class RiskRequest(BaseModel):
    """Request body for POST /api/risk"""

    as_of: Optional[dt.date] = Field(
        default=None,
        description="Evaluation date.",
    )
    financial_state: Optional[FinancialState] = Field(
        default=None,
        description="Optional custom financial state. If omitted, loads from database.",
    )
