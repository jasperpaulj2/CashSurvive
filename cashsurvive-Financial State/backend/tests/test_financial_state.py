"""Tests 7-10: FinancialState generation, totals, and the API endpoint."""

from __future__ import annotations

import datetime as dt

from data import repository
from data.schemas import (
    FinancingOptionCreate,
    ObligationCreate,
    PayableCreate,
    ReceivableCreate,
    SupplierCreate,
)
from services.financial_state import get_financial_state

TODAY = dt.date.today()


def _seed_full_dataset(db_session, seeded_company):
    supplier = repository.create_supplier(
        db_session,
        SupplierCreate(
            name="Supplier X",
            strategic_importance=0.5,
            liquidity_risk=0.3,
            dependency_score=0.4,
        ),
    )
    repository.create_receivable(
        db_session,
        ReceivableCreate(
            customer="ABC Ltd",
            amount=200_000,
            expected_date=TODAY + dt.timedelta(days=10),
            payment_probability=0.9,
        ),
    )
    repository.create_receivable(
        db_session,
        ReceivableCreate(
            customer="XYZ Ltd",
            amount=100_000,
            expected_date=TODAY - dt.timedelta(days=2),
            payment_probability=0.4,
            status="delayed",
        ),
    )
    repository.create_payable(
        db_session,
        PayableCreate(
            supplier_id=supplier.id,
            amount=150_000,
            invoice_date=TODAY - dt.timedelta(days=30),
            due_date=TODAY - dt.timedelta(days=1),  # overdue
            discount_percent=1.0,
            late_penalty_percent=2.0,
            status="overdue",
        ),
    )
    repository.create_obligation(
        db_session,
        ObligationCreate(
            name="Payroll",
            obligation_type="payroll",
            amount=90_000,
            due_date=TODAY + dt.timedelta(days=3),
            priority=1,
        ),
    )
    repository.create_financing_option(
        db_session,
        FinancingOptionCreate(
            provider="Test Bank",
            financing_type="line_of_credit",
            maximum_amount=500_000,
            annual_interest_rate=0.1,
        ),
    )


# 7. FinancialState generation
def test_financial_state_generation(db_session, seeded_company):
    _seed_full_dataset(db_session, seeded_company)
    state = get_financial_state(db_session, as_of=TODAY)

    assert state.current_cash == 1_000_000
    assert state.minimum_cash_reserve == 300_000
    assert state.cash_above_reserve == 700_000
    assert len(state.receivables) == 2
    assert len(state.payables) == 1
    assert len(state.suppliers) == 1
    assert len(state.obligations) == 1
    assert len(state.financing_options) == 1


# 8. Total receivable calculation
def test_total_receivables_calculation(db_session, seeded_company):
    _seed_full_dataset(db_session, seeded_company)
    state = get_financial_state(db_session, as_of=TODAY)
    assert state.total_receivables == 300_000  # 200,000 + 100,000


# 9. Total payable calculation
def test_total_payables_calculation(db_session, seeded_company):
    _seed_full_dataset(db_session, seeded_company)
    state = get_financial_state(db_session, as_of=TODAY)
    assert state.total_payables == 150_000
    assert state.overdue_payables_count == 1
    assert state.delayed_receivables_count == 1


# 10. API /financial-state response
def test_api_financial_state_endpoint(client, db_session, seeded_company):
    _seed_full_dataset(db_session, seeded_company)
    response = client.get("/financial-state")
    assert response.status_code == 200
    body = response.json()
    assert body["current_cash"] == 1_000_000
    assert body["total_receivables"] == 300_000
    assert body["total_payables"] == 150_000
    assert len(body["receivables"]) == 2
