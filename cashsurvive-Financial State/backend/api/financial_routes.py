"""
API routes for the Financial Data & Financial State module.

No business logic lives here — routes only wire together the
repository layer and the financial_state service.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from data import repository
from data.database import get_db
from data.schemas import (
    CompanyRead,
    FinancialState,
    FinancingOptionRead,
    ObligationRead,
    PayableRead,
    ReceivableRead,
    SupplierRead,
)
from services.financial_state import get_financial_state

router = APIRouter()


@router.get("/company", response_model=CompanyRead)
def read_company(db: Session = Depends(get_db)) -> CompanyRead:
    company = repository.get_company(db)
    if company is None:
        raise HTTPException(status_code=404, detail="No company found. Run the seed script.")
    return CompanyRead.model_validate(company)


@router.get("/financial-state", response_model=FinancialState)
def read_financial_state(db: Session = Depends(get_db)) -> FinancialState:
    try:
        return get_financial_state(db)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/receivables", response_model=list[ReceivableRead])
def read_receivables(db: Session = Depends(get_db)) -> list[ReceivableRead]:
    return [ReceivableRead.model_validate(r) for r in repository.get_receivables(db)]


@router.get("/payables", response_model=list[PayableRead])
def read_payables(db: Session = Depends(get_db)) -> list[PayableRead]:
    return [PayableRead.model_validate(p) for p in repository.get_payables(db)]


@router.get("/suppliers", response_model=list[SupplierRead])
def read_suppliers(db: Session = Depends(get_db)) -> list[SupplierRead]:
    return [SupplierRead.model_validate(s) for s in repository.get_suppliers(db)]


@router.get("/obligations", response_model=list[ObligationRead])
def read_obligations(db: Session = Depends(get_db)) -> list[ObligationRead]:
    return [ObligationRead.model_validate(o) for o in repository.get_obligations(db)]


@router.get("/financing-options", response_model=list[FinancingOptionRead])
def read_financing_options(db: Session = Depends(get_db)) -> list[FinancingOptionRead]:
    return [FinancingOptionRead.model_validate(f) for f in repository.get_financing_options(db)]
