"""
test_scenario_to_risk.py
========================
Tests for the Member 3 (Scenario & Risk) coordination adapter.
"""

from __future__ import annotations

from integration.forecast_to_scenario import convert_financial_state_to_scenario_model
from integration.scenario_to_risk import run_scenario_and_risk_analysis


def test_run_scenario_and_risk_analysis(sample_financial_state, sample_as_of):
    m3_state = convert_financial_state_to_scenario_model(sample_financial_state, as_of=sample_as_of)

    results = run_scenario_and_risk_analysis(m3_state)

    assert "baseline_risk" in results
    assert "scenarios" in results
    assert results["shocks"] is None
    assert results["reoptimization_required"] is False

    # Baseline Risk structure
    risk = results["baseline_risk"]
    assert "risk_score" in risk
    assert "risk_level" in risk
    assert "factor_breakdown" in risk
    assert "liquidity" in risk["factor_breakdown"]
    assert "receivable" in risk["factor_breakdown"]
    assert "supplier" in risk["factor_breakdown"]
    assert "obligation" in risk["factor_breakdown"]
    assert "financing" in risk["factor_breakdown"]

    # Scenarios structure
    scenarios = results["scenarios"]
    assert len(scenarios) >= 4  # Normal, Delay, Cash Shock, Supplier Stress, Financing Shock
    types = [s["scenario_type"] for s in scenarios]
    assert "NORMAL" in types
    assert "RECEIVABLE_DELAY" in types
    assert "CASH_SHOCK" in types
    assert "SUPPLIER_STRESS" in types
    assert "FINANCING_SHOCK" in types

    for s in scenarios:
        assert "projected_cash" in s
        assert "cash_impact" in s
        assert "liquidity_ratio" in s
        assert "liquidity_status" in s
        assert "risk_score" in s


def test_shock_detection(sample_financial_state, sample_as_of):
    m3_current = convert_financial_state_to_scenario_model(sample_financial_state, as_of=sample_as_of)

    # Create previous state with higher cash
    m3_previous = m3_current.copy()
    m3_previous.cash_balance = 10_000_000.0  # 50% drop in cash -> should trigger cash shock

    results = run_scenario_and_risk_analysis(
        m3_state=m3_current,
        previous_state=m3_previous,
    )

    assert results["shocks"] is not None
    assert len(results["shocks"]) == 5
    assert results["reoptimization_required"] is True

    cash_shock = next(s for s in results["shocks"] if s["shock_type"] == "cash_shock")
    assert cash_shock["detected"] is True
