"""
Populates the SQLite database with realistic demo data for ONE
fictional company, in INR, sized for the other team members to build
forecasting / scenario / optimization logic on top of.

Run with:  python -m data.seed_data
"""

from __future__ import annotations

import datetime as dt

from data.database import SessionLocal, init_db
from data.schemas import (
    CompanyCreate,
    FinancingOptionCreate,
    ObligationCreate,
    PayableCreate,
    ReceivableCreate,
    SupplierCreate,
)
from data.repository import (
    create_company,
    create_financing_option,
    create_obligation,
    create_payable,
    create_receivable,
    create_supplier,
)

TODAY = dt.date.today()


def seed() -> None:
    init_db()
    db = SessionLocal()

    try:
        # --- Company ------------------------------------------------
        create_company(
            db,
            CompanyCreate(
                name="Aarav Textiles Pvt Ltd",
                currency="INR",
                current_cash=5_000_000,       # ₹50,00,000
                minimum_cash_reserve=2_000_000,  # ₹20,00,000
            ),
        )

        # --- Suppliers ------------------------------------------------
        supplier_a = create_supplier(
            db,
            SupplierCreate(
                name="Supplier A - Raw Cotton Co",
                strategic_importance=0.9,
                liquidity_risk=0.2,
                dependency_score=0.8,
            ),
        )
        supplier_b = create_supplier(
            db,
            SupplierCreate(
                name="Supplier B - Dye Chemicals Ltd",
                strategic_importance=0.5,
                liquidity_risk=0.6,
                dependency_score=0.4,
            ),
        )
        supplier_c = create_supplier(
            db,
            SupplierCreate(
                name="Supplier C - Packaging Solutions",
                strategic_importance=0.3,
                liquidity_risk=0.3,
                dependency_score=0.2,
            ),
        )

        # --- Receivables ------------------------------------------------
        create_receivable(
            db,
            ReceivableCreate(
                customer="ABC Ltd",
                amount=3_000_000,
                expected_date=TODAY + dt.timedelta(days=15),
                payment_probability=0.9,
                status="expected",
            ),
        )
        create_receivable(
            db,
            ReceivableCreate(
                customer="PQR Ltd",
                amount=1_500_000,
                expected_date=TODAY + dt.timedelta(days=30),
                payment_probability=0.75,
                status="expected",
            ),
        )
        create_receivable(
            db,
            ReceivableCreate(
                customer="LMN Ltd",
                amount=1_000_000,
                expected_date=TODAY - dt.timedelta(days=5),
                payment_probability=0.5,
                status="delayed",
            ),
        )

        # --- Payables ------------------------------------------------
        create_payable(
            db,
            PayableCreate(
                supplier_id=supplier_a.id,
                amount=1_000_000,
                invoice_date=TODAY - dt.timedelta(days=20),
                due_date=TODAY + dt.timedelta(days=10),
                early_payment_date=TODAY + dt.timedelta(days=3),
                discount_percent=2.0,
                late_penalty_percent=1.5,
                status="unpaid",
            ),
        )
        create_payable(
            db,
            PayableCreate(
                supplier_id=supplier_b.id,
                amount=600_000,
                invoice_date=TODAY - dt.timedelta(days=40),
                due_date=TODAY - dt.timedelta(days=5),
                early_payment_date=None,
                discount_percent=0.0,
                late_penalty_percent=2.5,
                status="overdue",
            ),
        )
        create_payable(
            db,
            PayableCreate(
                supplier_id=supplier_c.id,
                amount=1_200_000,
                invoice_date=TODAY - dt.timedelta(days=10),
                due_date=TODAY + dt.timedelta(days=20),
                early_payment_date=TODAY + dt.timedelta(days=5),
                discount_percent=1.0,
                late_penalty_percent=1.0,
                status="unpaid",
            ),
        )

        # --- Obligations ------------------------------------------------
        create_obligation(
            db,
            ObligationCreate(
                name="Monthly Payroll",
                obligation_type="payroll",
                amount=900_000,
                due_date=TODAY + dt.timedelta(days=5),
                priority=1,
            ),
        )
        create_obligation(
            db,
            ObligationCreate(
                name="GST Payment",
                obligation_type="tax",
                amount=350_000,
                due_date=TODAY + dt.timedelta(days=12),
                priority=1,
            ),
        )
        create_obligation(
            db,
            ObligationCreate(
                name="Office Rent",
                obligation_type="rent",
                amount=200_000,
                due_date=TODAY + dt.timedelta(days=8),
                priority=2,
            ),
        )

        # --- Financing options ------------------------------------------------
        create_financing_option(
            db,
            FinancingOptionCreate(
                provider="HDFC Bank",
                financing_type="line_of_credit",
                maximum_amount=3_000_000,
                annual_interest_rate=0.12,
                available=True,
            ),
        )
        create_financing_option(
            db,
            FinancingOptionCreate(
                provider="KredX Invoice Factoring",
                financing_type="invoice_factoring",
                maximum_amount=2_000_000,
                annual_interest_rate=0.15,
                available=True,
            ),
        )

        print("Seed data inserted successfully.")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
