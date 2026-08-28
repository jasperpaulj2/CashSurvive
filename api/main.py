"""
main.py
=======
FastAPI Application Entry Point for CashSurvive Backend.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import integration._path_setup  # noqa: F401
from data.database import init_db, SessionLocal
from data.repository import get_company
from data.seed_data import seed
from scenario_risk_engine.exceptions import ScenarioRiskEngineError

from api.routes.health import router as health_router
from api.routes.financial_state import router as financial_state_router
from api.routes.forecast import router as forecast_router
from api.routes.scenario import router as scenario_router
from api.routes.risk import router as risk_router
from api.routes.pipeline import router as pipeline_router

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
)
logger = logging.getLogger("cashsurvive.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes SQLite database and seeds default company data if empty."""
    logger.info("Initializing CashSurvive database tables...")
    init_db()

    # Automatically seed default demo company if database is fresh
    db = SessionLocal()
    try:
        company = get_company(db)
        if company is None:
            logger.info("Fresh database detected. Seeding default demo company...")
            seed()
    except Exception as exc:
        logger.warning(f"Database auto-seed check skipped: {exc}")
    finally:
        db.close()

    yield
    logger.info("Shutting down CashSurvive backend...")


tags_metadata = [
    {
        "name": "System & Health",
        "description": "Health checks, root metadata, and module availability status.",
    },
    {
        "name": "Unified Pipeline",
        "description": "Primary end-to-end endpoint orchestrating all backend modules.",
    },
    {
        "name": "Financial State (Member 1)",
        "description": "Query and manage company financial position and database records.",
    },
    {
        "name": "Forecasting Engine (Member 2)",
        "description": "Receivable timing prediction and Monte Carlo cash flow forecasting.",
    },
    {
        "name": "Scenario Engine (Member 3)",
        "description": "Forward-looking financial stress scenarios simulation.",
    },
    {
        "name": "Risk Engine (Member 3)",
        "description": "Deterministic, explainable 0-100 financial risk evaluation.",
    },
]

app = FastAPI(
    title="CASH SURVIVE API",
    description="Unified Backend API for CashSurvive: Cash Flow Forecasting, Stress Scenario Simulation, and Risk Engine.",
    version="1.0.0",
    openapi_tags=tags_metadata,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# -------------------------------------------------------------
# CORS Middleware Configuration
# -------------------------------------------------------------
frontend_origin_env = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173")
origins: List[str] = [orig.strip() for orig in frontend_origin_env.split(",") if orig.strip()]

# If wildcard is explicitly configured in development
allow_all = "*" in origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all else origins,
    allow_credentials=True if not allow_all else False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------------
# Exception Handlers
# -------------------------------------------------------------
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Formats Pydantic validation errors into clean API error responses."""
    logger.warning(f"Request validation failed on {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "error_type": "RequestValidationError",
            "message": "Input validation failed. Please check the supplied fields.",
            "detail": exc.errors(),
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Standardizes HTTP exceptions."""
    logger.warning(f"HTTP exception on {request.url.path}: status={exc.status_code}, detail={exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "error_type": "HTTPException",
            "message": exc.detail if isinstance(exc.detail, str) else "An HTTP error occurred.",
            "detail": exc.detail,
        },
    )


@app.exception_handler(ScenarioRiskEngineError)
async def scenario_risk_exception_handler(request: Request, exc: ScenarioRiskEngineError):
    """Handles domain errors from Member 3 Scenario/Risk engine."""
    logger.error(f"Scenario/Risk engine error on {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "status": "error",
            "error_type": type(exc).__name__,
            "message": str(exc),
            "detail": None,
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Catch-all handler preventing internal stack trace exposure."""
    logger.exception(f"Unhandled internal server error on {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "error_type": "InternalServerError",
            "message": "An unexpected error occurred while processing your request.",
            "detail": str(exc),
        },
    )


# -------------------------------------------------------------
# Include Routers
# -------------------------------------------------------------
app.include_router(health_router)
app.include_router(pipeline_router)
app.include_router(financial_state_router)
app.include_router(forecast_router)
app.include_router(scenario_router)
app.include_router(risk_router)
