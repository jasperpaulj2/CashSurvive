"""
responses.py
============
Pydantic v2 response schemas for standard CashSurvive API endpoints.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Response model for GET /health"""

    status: str = Field(description="Service health status", json_schema_extra={"example": "healthy"})
    version: str = Field(description="Backend application version", json_schema_extra={"example": "1.0.0"})
    modules: Dict[str, str] = Field(
        description="Availability status of Member 1, Member 2, and Member 3 modules"
    )
    timestamp: str = Field(description="UTC timestamp of health check")


class SeedResponse(BaseModel):
    """Response model for POST /api/financial-state/seed"""

    status: str = Field(json_schema_extra={"example": "success"})
    message: str = Field(json_schema_extra={"example": "Demo company financial state seeded successfully."})
    company_name: str = Field(json_schema_extra={"example": "Aarav Textiles Pvt Ltd"})


class ErrorResponse(BaseModel):
    """Structured error payload for API exceptions."""

    status: str = Field(default="error", json_schema_extra={"example": "error"})
    error_type: str = Field(description="Class or category of error", json_schema_extra={"example": "ValueError"})
    message: str = Field(description="User-friendly error explanation")
    detail: Optional[Any] = Field(default=None, description="Detailed validation errors or context")
