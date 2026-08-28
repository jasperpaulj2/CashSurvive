"""
FastAPI application entrypoint.

Run with:  uvicorn main:app --reload
"""

from __future__ import annotations

from fastapi import FastAPI

from api.financial_routes import router as financial_router
from data.database import init_db

app = FastAPI(
    title="CashSurvive AI - Financial Data & State Module",
    description=(
        "Member 1's module: financial data models, database, validation, "
        "and the FinancialState contract consumed by forecasting, "
        "scenario/risk, and optimization modules."
    ),
    version="1.0.0",
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


app.include_router(financial_router, tags=["financial-data"])


@app.get("/", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "financial-data-module"}
