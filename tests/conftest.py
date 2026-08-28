"""
conftest.py
===========
Shared test fixtures for integration and API test suites.
"""

from __future__ import annotations

import datetime as dt
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import integration._path_setup  # noqa: F401

from data.database import Base
from data.schemas import (
    FinancialState,
    ReceivableRead,
    PayableRead,
    SupplierRead,
    ObligationRead,
    FinancingOptionRead,
    CompanyCreate,
    ReceivableCreate,
    PayableCreate,
    SupplierCreate,
    ObligationCreate,
    FinancingOptionCreate,
)
from data.repository import (
    create_company,
    create_receivable,
    create_payable,
    create_supplier,
    create_obligation,
    create_financing_option,
)


@pytest.fixture
def sample_as_of() -> dt.date:
    return dt.date(2026, 8, 28)


@pytest.fixture
def sample_financial_state(sample_as_of: dt.date) -> FinancialState:
    """Provides a realistic in-memory FinancialState without database access."""
    return FinancialState(
        as_of=sample_as_of,
        currency="INR",
        current_cash=5_000_000.0,
        minimum_cash_reserve=2_000_000.0,
        cash_above_reserve=3_000_000.0,
        total_receivables=5_500_000.0,
        total_payables=2_800_000.0,
        total_obligations=1_450_000.0,
        overdue_payables_count=1,
        delayed_receivables_count=1,
        receivables=[
            ReceivableRead(
                id=1,
                customer="ABC Ltd",
                amount=3_000_000.0,
                expected_date=sample_as_of + dt.timedelta(days=15),
                payment_probability=0.90,
                status="expected",
            ),
            ReceivableRead(
                id=2,
                customer="PQR Ltd",
                amount=1_500_000.0,
                expected_date=sample_as_of + dt.timedelta(days=30),
                payment_probability=0.75,
                status="expected",
            ),
            ReceivableRead(
                id=3,
                customer="LMN Ltd",
                amount=1_000_000.0,
                expected_date=sample_as_of - dt.timedelta(days=5),
                payment_probability=0.50,
                status="delayed",
            ),
        ],
        payables=[
            PayableRead(
                id=1,
                supplier_id=1,
                amount=1_000_000.0,
                invoice_date=sample_as_of - dt.timedelta(days=20),
                due_date=sample_as_of + dt.timedelta(days=10),
                early_payment_date=sample_as_of + dt.timedelta(days=3),
                discount_percent=2.0,
                late_penalty_percent=1.5,
                status="unpaid",
            ),
            PayableRead(
                id=2,
                supplier_id=2,
                amount=600_000.0,
                invoice_date=sample_as_of - dt.timedelta(days=40),
                due_date=sample_as_of - dt.timedelta(days=5),
                early_payment_date=None,
                discount_percent=0.0,
                late_penalty_percent=2.5,
                status="overdue",
            ),
            PayableRead(
                id=3,
                supplier_id=3,
                amount=1_200_000.0,
                invoice_date=sample_as_of - dt.timedelta(days=10),
                due_date=sample_as_of + dt.timedelta(days=20),
                early_payment_date=sample_as_of + dt.timedelta(days=5),
                discount_percent=1.0,
                late_penalty_percent=1.0,
                status="unpaid",
            ),
        ],
        suppliers=[
            SupplierRead(
                id=1,
                name="Supplier A - Raw Cotton Co",
                strategic_importance=0.9,
                liquidity_risk=0.2,
                dependency_score=0.8,
            ),
            SupplierRead(
                id=2,
                name="Supplier B - Dye Chemicals Ltd",
                strategic_importance=0.5,
                liquidity_risk=0.6,
                dependency_score=0.4,
            ),
            SupplierRead(
                id=3,
                name="Supplier C - Packaging Solutions",
                strategic_importance=0.3,
                liquidity_risk=0.3,
                dependency_score=0.2,
            ),
        ],
        obligations=[
            ObligationRead(
                id=1,
                name="Monthly Payroll",
                obligation_type="payroll",
                amount=900_000.0,
                due_date=sample_as_of + dt.timedelta(days=5),
                priority=1,
            ),
            ObligationRead(
                id=2,
                name="GST Payment",
                obligation_type="tax",
                amount=350_000.0,
                due_date=sample_as_of + dt.timedelta(days=12),
                priority=1,
            ),
            ObligationRead(
                id=3,
                name="Office Rent",
                obligation_type="rent",
                amount=200_000.0,
                due_date=sample_as_of + dt.timedelta(days=8),
                priority=2,
            ),
        ],
        financing_options=[
            FinancingOptionRead(
                id=1,
                provider="HDFC Bank",
                financing_type="line_of_credit",
                maximum_amount=3_000_000.0,
                annual_interest_rate=0.12,
                available=True,
            ),
            FinancingOptionRead(
                id=2,
                provider="KredX Invoice Factoring",
                financing_type="invoice_factoring",
                maximum_amount=2_000_000.0,
                annual_interest_rate=0.15,
                available=True,
            ),
        ],
    )


@pytest.fixture
def in_memory_db(sample_as_of: dt.date):
    """Provides an isolated SQLite in-memory database populated with seed records."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSessionLocal()

    try:
        # Seed company
        create_company(
            session,
            CompanyCreate(
                name="Aarav Textiles Pvt Ltd",
                currency="INR",
                current_cash=5_000_000.0,
                minimum_cash_reserve=2_000_000.0,
            ),
        )
        # Seed suppliers
        s1 = create_supplier(
            session,
            SupplierCreate(
                name="Supplier A",
                strategic_importance=0.9,
                liquidity_risk=0.2,
                dependency_score=0.8,
            ),
        )
        s2 = create_supplier(
            session,
            SupplierCreate(
                name="Supplier B",
                strategic_importance=0.5,
                liquidity_risk=0.6,
                dependency_score=0.4,
            ),
        )
        # Seed receivables
        create_receivable(
            session,
            ReceivableCreate(
                customer="ABC Ltd",
                amount=3_000_000.0,
                expected_date=sample_as_of + dt.timedelta(days=15),
                payment_probability=0.9,
                status="expected",
            ),
        )
        # Seed payables
        create_payable(
            session,
            PayableCreate(
                supplier_id=s1.id,
                amount=1_000_000.0,
                invoice_date=sample_as_of - dt.timedelta(days=20),
                due_date=sample_as_of + dt.timedelta(days=10),
                early_payment_date=sample_as_of + dt.timedelta(days=3),
                discount_percent=2.0,
                late_penalty_percent=1.5,
                status="unpaid",
            ),
        )
        # Seed obligation
        create_obligation(
            session,
            ObligationCreate(
                name="Payroll",
                obligation_type="payroll",
                amount=900_000.0,
                due_date=sample_as_of + dt.timedelta(days=5),
                priority=1,
            ),
        )
        # Seed financing
        create_financing_option(
            session,
            FinancingOptionCreate(
                provider="HDFC Bank",
                financing_type="line_of_credit",
                maximum_amount=3_000_000.0,
                annual_interest_rate=0.12,
                available=True,
            ),
        )

        yield session
    finally:
        session.close()
