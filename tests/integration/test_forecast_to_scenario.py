"""
test_forecast_to_scenario.py
============================
Tests for the Member 1 (Financial State) -> Member 3 (Scenario & Risk) adapter.
"""

from __future__ import annotations

from integration.forecast_to_scenario import convert_financial_state_to_scenario_model
from scenario_risk_engine.models import FinancialState as M3FinancialState


def test_convert_financial_state_to_scenario_model(sample_financial_state, sample_as_of):
    m3_state = convert_financial_state_to_scenario_model(sample_financial_state, as_of=sample_as_of)

    assert isinstance(m3_state, M3FinancialState)
    assert m3_state.cash_balance == 5_000_000.0
    assert m3_state.minimum_cash_reserve == 2_000_000.0

    # Receivables (expected and delayed)
    assert len(m3_state.receivables) == 3
    r1 = next(r for r in m3_state.receivables if r.id == "AR-1")
    assert r1.amount == 3_000_000.0
    assert r1.expected_days == 15
    assert r1.probability == 0.90

    # Payables (unpaid and overdue)
    assert len(m3_state.payables) == 3
    p1 = next(p for p in m3_state.payables if p.id == "AP-1")
    assert p1.amount == 1_000_000.0
    assert p1.due_days == 10

    # Obligations
    assert len(m3_state.upcoming_obligations) == 3
    o1 = next(o for o in m3_state.upcoming_obligations if o.id == "OBL-1")
    assert o1.amount == 900_000.0
    assert o1.due_days == 5

    # Suppliers
    assert len(m3_state.supplier_risks) == 3
    s1 = next(s for s in m3_state.supplier_risks if s.supplier_id == "SUP-1")
    assert s1.name == "Supplier A - Raw Cotton Co"
    assert s1.importance == 0.9
    assert s1.liquidity_risk == 0.2
    assert s1.dependency == 0.8

    # Financing Options
    assert len(m3_state.financing_options) == 2
    f1 = next(f for f in m3_state.financing_options if f.id == "FIN-1")
    assert f1.available_amount == 3_000_000.0
    assert f1.interest_rate == 0.12
