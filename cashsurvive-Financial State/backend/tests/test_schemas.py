"""Tests 1-6: Pydantic schema validation."""

from __future__ import annotations

import datetime as dt

import pytest
from pydantic import ValidationError

from data.schemas import PayableCreate, ReceivableCreate, SupplierCreate

TODAY = dt.date.today()


# 1. Valid receivable
def test_valid_receivable_passes():
    receivable = ReceivableCreate(
        customer="ABC Ltd",
        amount=100_000,
        expected_date=TODAY + dt.timedelta(days=10),
        payment_probability=0.8,
        status="expected",
    )
    assert receivable.amount == 100_000


# 2. Invalid receivable amount
def test_invalid_receivable_amount_rejected():
    with pytest.raises(ValidationError):
        ReceivableCreate(
            customer="ABC Ltd",
            amount=-100,
            expected_date=TODAY,
            payment_probability=0.8,
        )


# 3. Invalid payment probability
def test_invalid_payment_probability_rejected():
    with pytest.raises(ValidationError):
        ReceivableCreate(
            customer="ABC Ltd",
            amount=100_000,
            expected_date=TODAY,
            payment_probability=1.5,
        )


# 4. Invalid payable amount
def test_invalid_payable_amount_rejected():
    with pytest.raises(ValidationError):
        PayableCreate(
            supplier_id=1,
            amount=0,
            invoice_date=TODAY,
            due_date=TODAY + dt.timedelta(days=5),
        )


# 5. Invalid payable dates
def test_invalid_payable_dates_rejected():
    with pytest.raises(ValidationError):
        PayableCreate(
            supplier_id=1,
            amount=1000,
            invoice_date=TODAY,
            due_date=TODAY - dt.timedelta(days=5),  # due before invoice
        )


# 6. Invalid supplier risk
def test_invalid_supplier_risk_rejected():
    with pytest.raises(ValidationError):
        SupplierCreate(
            name="Supplier X",
            strategic_importance=0.5,
            liquidity_risk=1.2,  # out of [0,1]
            dependency_score=0.5,
        )
