"""
test_api_endpoints.py
=====================
Tests for all FastAPI routes, request validation, error handlers, and CORS.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import integration._path_setup  # noqa: F401
from api.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["app"] == "CASH SURVIVE API"
    assert data["status"] == "online"
    assert "docs_url" in data


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded")
    assert "modules" in data
    assert data["modules"]["financial_state_member_1"] == "available"
    assert data["modules"]["forecasting_engine_member_2"] == "available"
    assert data["modules"]["scenario_risk_engine_member_3"] == "available"


def test_seed_and_get_financial_state(client):
    # Seed
    seed_res = client.post("/api/financial-state/seed")
    assert seed_res.status_code == 201
    seed_data = seed_res.json()
    assert seed_data["status"] == "success"
    assert seed_data["company_name"] == "Aarav Textiles Pvt Ltd"

    # Get
    get_res = client.get("/api/financial-state")
    assert get_res.status_code == 200
    fs = get_res.json()
    assert fs["currency"] == "INR"
    assert fs["current_cash"] == 5_000_000.0
    assert len(fs["receivables"]) >= 3
    assert len(fs["payables"]) >= 3


def test_forecast_endpoint(client, sample_financial_state):
    # Test with custom state
    payload = {
        "horizon_days": 14,
        "num_simulations": 300,
        "financial_state": sample_financial_state.model_dump(mode="json"),
    }
    response = client.post("/api/forecast", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["projections"]) == 14
    assert "summary" in data
    assert "receivable_aging" in data


def test_scenarios_endpoint(client, sample_financial_state):
    payload = {
        "financial_state": sample_financial_state.model_dump(mode="json"),
    }
    response = client.post("/api/scenarios", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["scenarios"]) >= 4


def test_risk_endpoint(client, sample_financial_state):
    payload = {
        "financial_state": sample_financial_state.model_dump(mode="json"),
    }
    response = client.post("/api/risk", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "risk" in data
    assert "risk_score" in data["risk"]
    assert "factor_breakdown" in data["risk"]


def test_pipeline_run_endpoint_with_custom_state(client, sample_financial_state):
    payload = {
        "horizon_days": 30,
        "num_simulations": 500,
        "financial_state": sample_financial_state.model_dump(mode="json"),
    }
    response = client.post("/api/pipeline/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "financial_state" in data
    assert "forecast" in data
    assert "scenarios" in data
    assert "risk" in data
    assert "optimization_extension" in data
    assert data["optimization_extension"]["status"] == "ready_for_extension"


def test_pipeline_run_endpoint_with_db(client):
    # Call without passing financial_state (loads from seeded DB)
    payload = {
        "horizon_days": 10,
        "num_simulations": 200,
    }
    response = client.post("/api/pipeline/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["financial_state"]["current_cash"] == 5_000_000.0


def test_request_validation_failure(client):
    # Invalid horizon_days (< 1)
    bad_payload = {
        "horizon_days": -10,
        "num_simulations": 1000,
    }
    response = client.post("/api/pipeline/run", json=bad_payload)
    assert response.status_code == 422
    data = response.json()
    assert data["status"] == "error"
    assert data["error_type"] == "RequestValidationError"
    assert "detail" in data


def test_num_simulations_validation_failure(client):
    # Invalid num_simulations (< 100)
    bad_payload = {
        "horizon_days": 30,
        "num_simulations": 10,
    }
    response = client.post("/api/pipeline/run", json=bad_payload)
    assert response.status_code == 422
    data = response.json()
    assert data["status"] == "error"
    assert data["error_type"] == "RequestValidationError"
