"""
Repository layer: the only place that talks directly to the ORM/DB session.

Business logic (financial_state.py) and API routes should never import
`data.models` or touch a `Session` directly — they go through these
functions instead. This keeps DB access swappable and testable.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from data import models
from data.schemas import (
    CompanyCreate,
    FinancingOptionCreate,
    ObligationCreate,
    PayableCreate,
    ReceivableCreate,
    SupplierCreate,
)

# ------------------------------------------------------------------
# Reads
# ------------------------------------------------------------------


def get_company(db: Session) -> models.Company | None:
    """Returns the (single) company row for this hackathon prototype."""
    return db.execute(select(models.Company)).scalars().first()


def get_receivables(db: Session) -> list[models.Receivable]:
    return list(db.execute(select(models.Receivable)).scalars().all())


def get_payables(db: Session) -> list[models.Payable]:
    return list(db.execute(select(models.Payable)).scalars().all())


def get_suppliers(db: Session) -> list[models.Supplier]:
    return list(db.execute(select(models.Supplier)).scalars().all())


def get_obligations(db: Session) -> list[models.Obligation]:
    return list(db.execute(select(models.Obligation)).scalars().all())


def get_financing_options(db: Session) -> list[models.FinancingOption]:
    return list(db.execute(select(models.FinancingOption)).scalars().all())


# ------------------------------------------------------------------
# Writes (useful for seeding and for other members' test fixtures)
# ------------------------------------------------------------------


def create_company(db: Session, data: CompanyCreate) -> models.Company:
    obj = models.Company(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def create_receivable(db: Session, data: ReceivableCreate) -> models.Receivable:
    obj = models.Receivable(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def create_supplier(db: Session, data: SupplierCreate) -> models.Supplier:
    obj = models.Supplier(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def create_payable(db: Session, data: PayableCreate) -> models.Payable:
    obj = models.Payable(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def create_obligation(db: Session, data: ObligationCreate) -> models.Obligation:
    obj = models.Obligation(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def create_financing_option(db: Session, data: FinancingOptionCreate) -> models.FinancingOption:
    obj = models.FinancingOption(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj
