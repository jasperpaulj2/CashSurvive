"""Repository layer tests (supporting infrastructure for tests 7-9)."""

from __future__ import annotations

import datetime as dt

from data import repository
from data.schemas import ReceivableCreate, SupplierCreate

TODAY = dt.date.today()


def test_create_and_get_receivable(db_session, seeded_company):
    repository.create_receivable(
        db_session,
        ReceivableCreate(
            customer="ABC Ltd",
            amount=50_000,
            expected_date=TODAY + dt.timedelta(days=7),
            payment_probability=0.9,
        ),
    )
    receivables = repository.get_receivables(db_session)
    assert len(receivables) == 1
    assert receivables[0].customer == "ABC Ltd"


def test_create_and_get_supplier(db_session):
    repository.create_supplier(
        db_session,
        SupplierCreate(
            name="Supplier X",
            strategic_importance=0.6,
            liquidity_risk=0.4,
            dependency_score=0.5,
        ),
    )
    suppliers = repository.get_suppliers(db_session)
    assert len(suppliers) == 1
    assert suppliers[0].name == "Supplier X"


def test_get_company_returns_seeded_company(db_session, seeded_company):
    company = repository.get_company(db_session)
    assert company is not None
    assert company.name == "Test Co"
