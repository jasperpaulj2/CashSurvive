"""
financial_to_forecast.py
========================
Adapter connecting Member 1 (Financial State) to Member 2 (Forecasting Engine).

Transforms Member 1 FinancialState into:
1. Member 2 Invoice objects for ReceivableForecaster
2. Member 2 CashFlowItem objects for CashFlowForecaster
"""

from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List, Optional

import integration._path_setup  # noqa: F401

from data.schemas import FinancialState, PayableRead, ObligationRead, ReceivableRead
from receivable_forecast import (
    Invoice,
    InvoiceStatus,
    ReceivableForecaster,
    CustomerProfile,
)
from cash_forecast import (
    CashFlowForecaster,
    CashFlowItem,
    DayProjection,
    ForecastSummary,
    RecurrenceType,
)


def convert_receivables_to_invoices(
    financial_state: FinancialState,
    as_of: Optional[dt.date] = None,
) -> List[Invoice]:
    """
    Convert Member 1 receivables to Member 2 Invoice domain models.
    """
    as_of = as_of or financial_state.as_of
    invoices: List[Invoice] = []

    for index, r in enumerate(financial_state.receivables, start=1):
        # Infer an issue date (30 days before expected date)
        issue_date = r.expected_date - dt.timedelta(days=30)
        due_date = r.expected_date

        if r.status == "received":
            status = InvoiceStatus.PAID
            paid_date = r.expected_date
        elif r.status == "delayed":
            status = InvoiceStatus.OVERDUE
            paid_date = None
        else:
            # Expected
            if due_date < as_of:
                status = InvoiceStatus.OVERDUE
            else:
                status = InvoiceStatus.OPEN
            paid_date = None

        invoice = Invoice(
            invoice_id=f"AR-{r.id if hasattr(r, 'id') and r.id is not None else index:04d}",
            customer_id=r.customer,
            amount=float(r.amount),
            issue_date=issue_date,
            due_date=due_date,
            status=status,
            paid_date=paid_date,
        )
        invoices.append(invoice)

    return invoices


def convert_payables_and_obligations_to_cash_flow_items(
    financial_state: FinancialState,
) -> List[CashFlowItem]:
    """
    Convert Member 1 payables and obligations to Member 2 CashFlowItem outflows.
    """
    items: List[CashFlowItem] = []

    # Payables (unpaid or overdue represent future or immediate outflows)
    for p in financial_state.payables:
        if p.status in ("unpaid", "overdue"):
            items.append(
                CashFlowItem(
                    label=f"Payable #{p.id} (Supplier {p.supplier_id})",
                    amount=-float(p.amount),  # Outflow is negative
                    start_date=p.due_date,
                    recurrence=RecurrenceType.ONE_TIME,
                )
            )

    # Obligations (payroll, tax, rent, debt repayments, etc.)
    for o in financial_state.obligations:
        items.append(
            CashFlowItem(
                label=f"Obligation: {o.name} ({o.obligation_type})",
                amount=-float(o.amount),  # Outflow is negative
                start_date=o.due_date,
                recurrence=RecurrenceType.ONE_TIME,
            )
        )

    return items


def build_receivable_forecaster(
    financial_state: FinancialState,
    as_of: Optional[dt.date] = None,
) -> ReceivableForecaster:
    """
    Build and populate a Member 2 ReceivableForecaster from Member 1 FinancialState.
    """
    as_of = as_of or financial_state.as_of
    invoices = convert_receivables_to_invoices(financial_state, as_of=as_of)
    forecaster = ReceivableForecaster(as_of=as_of)
    forecaster.load_invoices(invoices)
    forecaster.build_customer_profiles()
    return forecaster


def build_cash_flow_forecaster(
    financial_state: FinancialState,
    as_of: Optional[dt.date] = None,
    historical_daily_net: Optional[List[float]] = None,
) -> CashFlowForecaster:
    """
    Build and configure a Member 2 CashFlowForecaster with attached receivables.
    """
    as_of = as_of or financial_state.as_of
    cff = CashFlowForecaster(
        starting_balance=float(financial_state.current_cash),
        as_of=as_of,
        historical_daily_net=historical_daily_net,
    )
    items = convert_payables_and_obligations_to_cash_flow_items(financial_state)
    cff.add_cash_flow_items(items)

    ar_forecaster = build_receivable_forecaster(financial_state, as_of=as_of)
    cff.attach_receivables(ar_forecaster)

    return cff


def run_forecasting(
    financial_state: FinancialState,
    horizon_days: int = 30,
    num_simulations: int = 2000,
    confidence_level: float = 0.90,
    as_of: Optional[dt.date] = None,
    historical_daily_net: Optional[List[float]] = None,
) -> Dict[str, Any]:
    """
    Execute the complete forecasting package (AR + Cash Flow + Monte Carlo)
    and return a clean, serializable dictionary of results.
    """
    as_of = as_of or financial_state.as_of
    cff = build_cash_flow_forecaster(
        financial_state,
        as_of=as_of,
        historical_daily_net=historical_daily_net,
    )

    projections: List[DayProjection] = cff.forecast(
        horizon_days=horizon_days,
        num_simulations=num_simulations,
        confidence_level=confidence_level,
    )
    summary: ForecastSummary = cff.summarize(projections)

    ar_forecaster = cff.receivable_forecaster
    aging = ar_forecaster.aging_report() if ar_forecaster else {}
    dso = ar_forecaster.days_sales_outstanding() if ar_forecaster else 0.0
    profiles = (
        [p.as_dict() for p in ar_forecaster.customer_profiles.values()]
        if ar_forecaster
        else []
    )
    high_risk = (
        [p.as_dict() for p in ar_forecaster.high_risk_customers(threshold=40.0)]
        if ar_forecaster
        else []
    )

    return {
        "summary": summary.as_dict(),
        "projections": [p.as_dict() for p in projections],
        "receivable_aging": aging,
        "days_sales_outstanding": dso,
        "customer_profiles": profiles,
        "high_risk_customers": high_risk,
    }
