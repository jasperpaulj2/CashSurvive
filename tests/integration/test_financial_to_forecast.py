"""
test_financial_to_forecast.py
=============================
Tests for the Member 1 (Financial State) -> Member 2 (Forecasting) adapter.
"""

from __future__ import annotations

import datetime as dt
from integration.financial_to_forecast import (
    convert_receivables_to_invoices,
    convert_payables_and_obligations_to_cash_flow_items,
    build_receivable_forecaster,
    build_cash_flow_forecaster,
    run_forecasting,
)
from receivable_forecast import InvoiceStatus


def test_convert_receivables_to_invoices(sample_financial_state, sample_as_of):
    invoices = convert_receivables_to_invoices(sample_financial_state, as_of=sample_as_of)
    assert len(invoices) == 3

    # Check mapping
    inv_expected = next(i for i in invoices if i.customer_id == "ABC Ltd")
    assert inv_expected.amount == 3_000_000.0
    assert inv_expected.status == InvoiceStatus.OPEN
    assert inv_expected.due_date == sample_as_of + dt.timedelta(days=15)
    assert inv_expected.issue_date == inv_expected.due_date - dt.timedelta(days=30)

    inv_delayed = next(i for i in invoices if i.customer_id == "LMN Ltd")
    assert inv_delayed.amount == 1_000_000.0
    assert inv_delayed.status == InvoiceStatus.OVERDUE


def test_convert_payables_and_obligations(sample_financial_state):
    items = convert_payables_and_obligations_to_cash_flow_items(sample_financial_state)
    # 3 payables (2 unpaid + 1 overdue) + 3 obligations = 6 items
    assert len(items) == 6

    # Verify all outflow amounts are negative
    assert all(item.amount < 0 for item in items)

    # Check obligation label
    labels = [i.label for i in items]
    assert any("Payroll" in l for l in labels)
    assert any("GST Payment" in l for l in labels)


def test_build_forecasters(sample_financial_state, sample_as_of):
    ar_forecaster = build_receivable_forecaster(sample_financial_state, as_of=sample_as_of)
    assert len(ar_forecaster.invoices) == 3
    assert len(ar_forecaster.customer_profiles) == 3

    cff = build_cash_flow_forecaster(sample_financial_state, as_of=sample_as_of)
    assert cff.starting_balance == sample_financial_state.current_cash
    assert cff.receivable_forecaster is not None


def test_run_forecasting_execution(sample_financial_state, sample_as_of):
    result = run_forecasting(
        sample_financial_state,
        horizon_days=30,
        num_simulations=500,
        as_of=sample_as_of,
    )

    assert "summary" in result
    assert "projections" in result
    assert "receivable_aging" in result
    assert "days_sales_outstanding" in result
    assert "customer_profiles" in result

    summary = result["summary"]
    assert summary["starting_balance"] == 5_000_000.0
    assert "ending_balance" in summary
    assert "lowest_balance" in summary
    assert "scenario" in summary
    assert "best_case" in summary["scenario"]

    projections = result["projections"]
    assert len(projections) == 30
    first_day = projections[0]
    assert "date" in first_day
    assert "projected_balance" in first_day
    assert "uncertainty" in first_day
