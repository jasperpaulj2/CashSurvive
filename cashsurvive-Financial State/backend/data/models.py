"""
SQLAlchemy ORM models for the Financial Data & Financial State module.

These map 1:1 onto the tables described in the project spec:
Company, Receivable, Payable, Supplier, Obligation, FinancingOption.

Business-rule validation (ranges, non-negativity, etc.) lives in the
Pydantic schemas (schemas.py), not here. These ORM classes are kept
as plain structural definitions.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from data.database import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    currency: Mapped[str] = mapped_column(String, nullable=False, default="INR")
    current_cash: Mapped[float] = mapped_column(Float, nullable=False)
    minimum_cash_reserve: Mapped[float] = mapped_column(Float, nullable=False)


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    # Normalized 0-1 scores.
    strategic_importance: Mapped[float] = mapped_column(Float, nullable=False)
    liquidity_risk: Mapped[float] = mapped_column(Float, nullable=False)
    dependency_score: Mapped[float] = mapped_column(Float, nullable=False)

    payables: Mapped[list["Payable"]] = relationship(back_populates="supplier")


class Receivable(Base):
    __tablename__ = "receivables"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    expected_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    payment_probability: Mapped[float] = mapped_column(Float, nullable=False)
    # "expected" | "received" | "delayed"
    status: Mapped[str] = mapped_column(String, nullable=False, default="expected")


class Payable(Base):
    __tablename__ = "payables"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    invoice_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    due_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    early_payment_date: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    discount_percent: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    late_penalty_percent: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    # "unpaid" | "paid" | "overdue"
    status: Mapped[str] = mapped_column(String, nullable=False, default="unpaid")

    supplier: Mapped["Supplier"] = relationship(back_populates="payables")


class Obligation(Base):
    __tablename__ = "obligations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    # e.g. "payroll" | "tax" | "rent" | "loan_repayment" | "utilities"
    obligation_type: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    due_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    # 1 (highest) - 5 (lowest), see schemas.py for the documented range.
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=3)


class FinancingOption(Base):
    __tablename__ = "financing_options"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    # e.g. "line_of_credit" | "invoice_factoring" | "term_loan"
    financing_type: Mapped[str] = mapped_column(String, nullable=False)
    maximum_amount: Mapped[float] = mapped_column(Float, nullable=False)
    annual_interest_rate: Mapped[float] = mapped_column(Float, nullable=False)
    available: Mapped[bool] = mapped_column(default=True)
