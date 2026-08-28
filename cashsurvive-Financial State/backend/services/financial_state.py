"""
Builds the FinancialState — the single source of truth handed to the
rest of the backend (Members 2, 3, 4).

Only CURRENT-state aggregation happens here:
  - totals
  - cash above/below reserve
  - simple overdue/delayed counts based on existing status/date fields

No forecasting, no scenario generation, no optimization, no autonomous
decisions. Those belong to other modules.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy.orm import Session

from data import repository
from data.schemas import (
    FinancialState,
    FinancingOptionRead,
    ObligationRead,
    PayableRead,
    ReceivableRead,
    SupplierRead,
)


def _total_receivables(receivables: list[ReceivableRead]) -> float:
    return sum(r.amount for r in receivables)


def _total_payables(payables: list[PayableRead]) -> float:
    return sum(p.amount for p in payables)


def _total_obligations(obligations: list[ObligationRead]) -> float:
    return sum(o.amount for o in obligations)


def _overdue_payables_count(payables: list[PayableRead], as_of: dt.date) -> int:
    return sum(1 for p in payables if p.status == "overdue" or p.due_date < as_of)


def _delayed_receivables_count(receivables: list[ReceivableRead]) -> int:
    return sum(1 for r in receivables if r.status == "delayed")


def get_financial_state(db: Session, as_of: dt.date | None = None) -> FinancialState:
    """
    Assembles the complete current FinancialState from the database.

    Raises:
        ValueError: if no Company row exists yet (seed data not loaded).
    """
    as_of = as_of or dt.date.today()

    company = repository.get_company(db)
    if company is None:
        raise ValueError("No company found. Did you run the seed script?")

    receivables = [ReceivableRead.model_validate(r) for r in repository.get_receivables(db)]
    payables = [PayableRead.model_validate(p) for p in repository.get_payables(db)]
    suppliers = [SupplierRead.model_validate(s) for s in repository.get_suppliers(db)]
    obligations = [ObligationRead.model_validate(o) for o in repository.get_obligations(db)]
    financing_options = [
        FinancingOptionRead.model_validate(f) for f in repository.get_financing_options(db)
    ]

    total_receivables = _total_receivables(receivables)
    total_payables = _total_payables(payables)
    total_obligations = _total_obligations(obligations)

    return FinancialState(
        as_of=as_of,
        currency=company.currency,
        current_cash=company.current_cash,
        minimum_cash_reserve=company.minimum_cash_reserve,
        cash_above_reserve=company.current_cash - company.minimum_cash_reserve,
        total_receivables=total_receivables,
        total_payables=total_payables,
        total_obligations=total_obligations,
        overdue_payables_count=_overdue_payables_count(payables, as_of),
        delayed_receivables_count=_delayed_receivables_count(receivables),
        receivables=receivables,
        payables=payables,
        suppliers=suppliers,
        obligations=obligations,
        financing_options=financing_options,
    )
