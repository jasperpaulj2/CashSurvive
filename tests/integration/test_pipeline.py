"""
test_pipeline.py
================
End-to-end integration tests for the unified CashSurvive pipeline.
"""

from __future__ import annotations

import json
from unittest.mock import patch

from integration.pipeline import run_pipeline
from services.financial_state import get_financial_state


def test_run_pipeline_with_explicit_state(sample_financial_state, sample_as_of):
    result = run_pipeline(
        financial_state=sample_financial_state,
        horizon_days=30,
        num_simulations=500,
        as_of=sample_as_of,
    )

    assert result["status"] == "success"
    assert "financial_state" in result
    assert "forecast" in result
    assert "scenarios" in result
    assert "risk" in result
    assert "optimization_extension" in result

    # Financial State
    fs = result["financial_state"]
    assert fs["current_cash"] == 5_000_000.0
    assert fs["minimum_cash_reserve"] == 2_000_000.0

    # Forecast
    fc = result["forecast"]
    assert "summary" in fc
    assert "projections" in fc
    assert len(fc["projections"]) == 30

    # Scenarios
    scenarios = result["scenarios"]
    assert len(scenarios) >= 4

    # Risk
    risk = result["risk"]
    assert "risk_score" in risk
    assert "risk_level" in risk

    # Optimization Extension Point
    opt = result["optimization_extension"]
    assert opt["status"] == "ready_for_extension"
    assert opt["implemented"] is False

    # Verify complete JSON serializability
    json_str = json.dumps(result)
    assert json_str is not None
    loaded = json.loads(json_str)
    assert loaded["status"] == "success"


def test_run_pipeline_with_db(in_memory_db, sample_as_of):
    # Test pipeline loading directly from Member 1 database
    with patch("integration.pipeline.SessionLocal", return_value=in_memory_db):
        result = run_pipeline(
            financial_state=None,
            horizon_days=14,
            num_simulations=300,
            as_of=sample_as_of,
        )

        assert result["status"] == "success"
        assert result["financial_state"]["current_cash"] == 5_000_000.0
        assert len(result["forecast"]["projections"]) == 14
        assert len(result["scenarios"]) >= 3
