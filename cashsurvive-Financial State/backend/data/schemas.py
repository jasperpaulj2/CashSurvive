"""
Pydantic v2 schemas: request/response shapes + validation rules.

These are the objects that cross the API boundary. ORM models
(models.py) stay internal to the data layer; schemas are what
Members 2, 3 and 4 (and the frontend) actually consume.
"""

from __future__ import annotations

import datetime as dt
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

# ------------------------------------------------------------------
# Company
# ------------------------------------------------------------------


class CompanyBase(BaseModel):
    name: str
    currency: str = "INR"
    current_cash: float = Field(ge=0, description="Must not be negative.")
    minimum_cash_reserve: float = Field(ge=0, description="Must not be negative.")

    # Design decision: minimum_cash_reserve is allowed to exceed current_cash.
    # This is deliberate — it represents a company that is ALREADY below its
    # target reserve, which is exactly the stressed state this system needs
    # to be able to represent (e.g. for Member 3's risk/scenario engine).
    # We only validate non-negativity here; "reserve > cash" is a valid,
    # meaningful state, not a data error.


class CompanyCreate(CompanyBase):
    pass


class CompanyRead(CompanyBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ------------------------------------------------------------------
# Receivable
# ------------------------------------------------------------------

ReceivableStatus = Literal["expected", "received", "delayed"]


class ReceivableBase(BaseModel):
    customer: str
    amount: float = Field(gt=0)
    expected_date: dt.date
    payment_probability: float = Field(ge=0, le=1)
    status: ReceivableStatus = "expected"


class ReceivableCreate(ReceivableBase):
    pass


class ReceivableRead(ReceivableBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ------------------------------------------------------------------
# Payable
# ------------------------------------------------------------------

PayableStatus = Literal["unpaid", "paid", "overdue"]


class PayableBase(BaseModel):
    supplier_id: int
    amount: float = Field(gt=0)
    invoice_date: dt.date
    due_date: dt.date
    early_payment_date: dt.date | None = None
    discount_percent: float = Field(ge=0, default=0.0)
    late_penalty_percent: float = Field(ge=0, default=0.0)
    status: PayableStatus = "unpaid"

    @model_validator(mode="after")
    def check_dates(self) -> "PayableBase":
        if self.due_date < self.invoice_date:
            raise ValueError("due_date must not be before invoice_date")
        if self.early_payment_date is not None and self.early_payment_date < self.invoice_date:
            raise ValueError("early_payment_date must not be before invoice_date")
        return self


class PayableCreate(PayableBase):
    pass


class PayableRead(PayableBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ------------------------------------------------------------------
# Supplier
# ------------------------------------------------------------------


class SupplierBase(BaseModel):
    name: str
    strategic_importance: float = Field(ge=0, le=1)
    liquidity_risk: float = Field(ge=0, le=1)
    dependency_score: float = Field(ge=0, le=1)


class SupplierCreate(SupplierBase):
    pass


class SupplierRead(SupplierBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ------------------------------------------------------------------
# Obligation
# ------------------------------------------------------------------

ObligationType = Literal["payroll", "tax", "rent", "loan_repayment", "utilities", "other"]


class ObligationBase(BaseModel):
    name: str
    obligation_type: ObligationType
    amount: float = Field(gt=0)
    due_date: dt.date
    # 1 = highest priority (e.g. payroll), 5 = lowest.
    priority: int = Field(ge=1, le=5, default=3)


class ObligationCreate(ObligationBase):
    pass


class ObligationRead(ObligationBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ------------------------------------------------------------------
# FinancingOption
# ------------------------------------------------------------------

FinancingType = Literal["line_of_credit", "invoice_factoring", "term_loan", "overdraft"]


class FinancingOptionBase(BaseModel):
    provider: str
    financing_type: FinancingType
    maximum_amount: float = Field(gt=0)
    annual_interest_rate: float = Field(ge=0)
    available: bool = True


class FinancingOptionCreate(FinancingOptionBase):
    pass


class FinancingOptionRead(FinancingOptionBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ------------------------------------------------------------------
# FinancialState — the module's main contract with the rest of the team
# ------------------------------------------------------------------


class FinancialState(BaseModel):
    """
    Single source of truth for the company's current financial position.

    Member 2 (Forecasting)  consumes: receivables, payables, obligations, current_cash
    Member 3 (Scenario/Risk) consumes: suppliers, payables, obligations, cash_above_reserve
    Member 4 (Optimization)  consumes: this whole object + Member 2/3 outputs

    This object represents CURRENT state only — no forecasting, no
    scenarios, no optimization, no decisions are computed here.
    """

    as_of: dt.date

    # Company-level figures
    currency: str
    current_cash: float
    minimum_cash_reserve: float
    cash_above_reserve: float

    # Aggregates
    total_receivables: float
    total_payables: float
    total_obligations: float
    overdue_payables_count: int
    delayed_receivables_count: int

    # Raw collections for downstream modules
    receivables: list[ReceivableRead]
    payables: list[PayableRead]
    suppliers: list[SupplierRead]
    obligations: list[ObligationRead]
    financing_options: list[FinancingOptionRead]
