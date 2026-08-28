"""
forecast_to_scenario.py
=======================
Adapter connecting Member 1 Financial State to Member 3 (Scenario & Risk Engine).

Transforms Member 1 Pydantic FinancialState into Member 3 FinancialState
dataclass models required by ScenarioEngine, RiskEngine, and ShockDetector.
"""

from __future__ import annotations

import datetime as dt
from typing import Optional

import integration._path_setup  # noqa: F401

from data.schemas import FinancialState as M1FinancialState
from scenario_risk_engine.models import (
    FinancialState as M3FinancialState,
    Receivable as M3Receivable,
    Payable as M3Payable,
    Obligation as M3Obligation,
    SupplierRisk as M3SupplierRisk,
    FinancingOption as M3FinancingOption,
)


def convert_financial_state_to_scenario_model(
    financial_state: M1FinancialState,
    as_of: Optional[dt.date] = None,
) -> M3FinancialState:
    """
    Transforms Member 1 FinancialState Pydantic model into Member 3
    FinancialState dataclass expected by ScenarioEngine and RiskEngine.
    """
    as_of = as_of or financial_state.as_of

    # Convert Receivables (only include expected or delayed receivables)
    receivables = []
    for r in financial_state.receivables:
        if r.status in ("expected", "delayed"):
            expected_days = max(0, (r.expected_date - as_of).days)
            receivables.append(
                M3Receivable(
                    id=f"AR-{r.id}",
                    amount=float(r.amount),
                    expected_days=expected_days,
                    probability=float(r.payment_probability),
                    description=f"Receivable from {r.customer} (status: {r.status})",
                )
            )

    # Convert Payables (only unpaid and overdue payables)
    payables = []
    for p in financial_state.payables:
        if p.status in ("unpaid", "overdue"):
            due_days = max(0, (p.due_date - as_of).days)
            payables.append(
                M3Payable(
                    id=f"AP-{p.id}",
                    amount=float(p.amount),
                    due_days=due_days,
                    description=f"Payable to Supplier {p.supplier_id} (status: {p.status})",
                )
            )

    # Convert Obligations
    obligations = []
    for o in financial_state.obligations:
        due_days = max(0, (o.due_date - as_of).days)
        obligations.append(
            M3Obligation(
                id=f"OBL-{o.id}",
                amount=float(o.amount),
                due_days=due_days,
                description=f"{o.name} ({o.obligation_type})",
            )
        )

    # Convert Suppliers
    supplier_risks = []
    for s in financial_state.suppliers:
        supplier_risks.append(
            M3SupplierRisk(
                supplier_id=f"SUP-{s.id}",
                name=s.name,
                importance=float(s.strategic_importance),
                liquidity_risk=float(s.liquidity_risk),
                dependency=float(s.dependency_score),
            )
        )

    # Convert Financing Options (available ones)
    financing_options = []
    for f in financial_state.financing_options:
        if f.available:
            financing_options.append(
                M3FinancingOption(
                    id=f"FIN-{f.id}",
                    available_amount=float(f.maximum_amount),
                    interest_rate=float(f.annual_interest_rate),
                    description=f"{f.provider} ({f.financing_type})",
                )
            )

    return M3FinancialState(
        cash_balance=float(financial_state.current_cash),
        minimum_cash_reserve=float(financial_state.minimum_cash_reserve),
        receivables=receivables,
        payables=payables,
        upcoming_obligations=obligations,
        supplier_risks=supplier_risks,
        financing_options=financing_options,
        as_of=as_of.isoformat() if as_of else None,
    )
