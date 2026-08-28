"""
receivable_forecast.py
=======================
CashSurvive AI — Accounts Receivable Forecasting Module

Models outstanding customer invoices and predicts *when* and *how much* cash
they will bring in, based on each customer's historical payment behavior.
Produces an aging report, a per-customer risk score, and a day-by-day
expected collections schedule (with uncertainty bands via uncertainty.py)
that `cash_forecast.py` consumes as an inflow source.

Author: CashSurvive AI Team (Hackathon Build)
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
from typing import Dict, List, Optional

import numpy as np

from uncertainty import UncertaintyEstimator, ForecastUncertainty


# --------------------------------------------------------------------------- #
# Data model
# --------------------------------------------------------------------------- #

class InvoiceStatus(str, Enum):
    OPEN = "open"
    PAID = "paid"
    OVERDUE = "overdue"
    WRITTEN_OFF = "written_off"


@dataclass
class Invoice:
    """A single customer invoice."""
    invoice_id: str
    customer_id: str
    amount: float
    issue_date: date
    due_date: date
    status: InvoiceStatus = InvoiceStatus.OPEN
    paid_date: Optional[date] = None

    def days_until_due(self, as_of: date) -> int:
        return (self.due_date - as_of).days

    def days_overdue(self, as_of: date) -> int:
        return max(0, (as_of - self.due_date).days)

    def is_outstanding(self) -> bool:
        return self.status in (InvoiceStatus.OPEN, InvoiceStatus.OVERDUE)


@dataclass
class CustomerProfile:
    """Derived payment-behavior statistics for one customer."""
    customer_id: str
    avg_days_to_pay: float
    std_days_to_pay: float
    on_time_rate: float          # fraction of past invoices paid by due date
    num_paid_invoices: int
    risk_score: float            # 0 (safe) - 100 (high risk of late/non-payment)

    def as_dict(self) -> dict:
        return {
            "customer_id": self.customer_id,
            "avg_days_to_pay": round(self.avg_days_to_pay, 1),
            "std_days_to_pay": round(self.std_days_to_pay, 1),
            "on_time_rate": round(self.on_time_rate, 3),
            "num_paid_invoices": self.num_paid_invoices,
            "risk_score": round(self.risk_score, 1),
        }


@dataclass
class CollectionForecastDay:
    """Expected receivable inflow for a single future date."""
    forecast_date: date
    expected_amount: float
    uncertainty: Optional[ForecastUncertainty] = None
    contributing_invoices: List[str] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Forecaster
# --------------------------------------------------------------------------- #

class ReceivableForecaster:
    """
    Predicts collection timing/amounts for outstanding invoices using
    historical, paid-invoice payment behavior per customer.

    Usage:
        forecaster = ReceivableForecaster()
        forecaster.load_invoices(invoice_list)
        forecaster.build_customer_profiles()
        schedule = forecaster.forecast_collections(horizon_days=30)
        aging = forecaster.aging_report()
    """

    # Default assumption for customers with no payment history yet.
    DEFAULT_AVG_DAYS_TO_PAY = 15.0
    DEFAULT_STD_DAYS_TO_PAY = 7.0

    def __init__(self, as_of: Optional[date] = None):
        self.as_of: date = as_of or date.today()
        self.invoices: List[Invoice] = []
        self.customer_profiles: Dict[str, CustomerProfile] = {}
        self._estimator = UncertaintyEstimator()

    # ------------------------------- loading -------------------------------- #

    def load_invoices(self, invoices: List[Invoice]) -> None:
        """Load (or replace) the working set of invoices."""
        self.invoices = list(invoices)
        self._auto_flag_overdue()

    def add_invoice(self, invoice: Invoice) -> None:
        self.invoices.append(invoice)
        self._auto_flag_overdue()

    def _auto_flag_overdue(self) -> None:
        for inv in self.invoices:
            if inv.status == InvoiceStatus.OPEN and inv.due_date < self.as_of:
                inv.status = InvoiceStatus.OVERDUE

    # ------------------------- customer profile building ---------------------- #

    def build_customer_profiles(self) -> Dict[str, CustomerProfile]:
        """
        Compute per-customer average days-to-pay, variability, and an on-time
        payment rate from historical *paid* invoices. Customers with no paid
        history get conservative default assumptions.
        """
        by_customer: Dict[str, List[Invoice]] = {}
        for inv in self.invoices:
            by_customer.setdefault(inv.customer_id, []).append(inv)

        profiles: Dict[str, CustomerProfile] = {}
        for customer_id, invs in by_customer.items():
            paid = [i for i in invs if i.status == InvoiceStatus.PAID and i.paid_date]

            if paid:
                days_to_pay = [(i.paid_date - i.issue_date).days for i in paid]
                on_time_flags = [1.0 if i.paid_date <= i.due_date else 0.0 for i in paid]
                avg_days = statistics.mean(days_to_pay)
                std_days = statistics.pstdev(days_to_pay) if len(days_to_pay) > 1 else self.DEFAULT_STD_DAYS_TO_PAY
                on_time_rate = statistics.mean(on_time_flags)
                num_paid = len(paid)
            else:
                avg_days = self.DEFAULT_AVG_DAYS_TO_PAY
                std_days = self.DEFAULT_STD_DAYS_TO_PAY
                on_time_rate = 0.5  # unknown -> neutral assumption
                num_paid = 0

            risk_score = self._compute_risk_score(
                avg_days_to_pay=avg_days,
                on_time_rate=on_time_rate,
                num_paid_invoices=num_paid,
                current_overdue_days=max(
                    (i.days_overdue(self.as_of) for i in invs if i.is_outstanding()),
                    default=0,
                ),
            )

            profiles[customer_id] = CustomerProfile(
                customer_id=customer_id,
                avg_days_to_pay=avg_days,
                std_days_to_pay=std_days,
                on_time_rate=on_time_rate,
                num_paid_invoices=num_paid,
                risk_score=risk_score,
            )

        self.customer_profiles = profiles
        return profiles

    @staticmethod
    def _compute_risk_score(
        avg_days_to_pay: float,
        on_time_rate: float,
        num_paid_invoices: int,
        current_overdue_days: int,
    ) -> float:
        """
        Blend several signals into a 0-100 risk score (higher = riskier):
          - Poor on-time history increases risk.
          - Long average days-to-pay increases risk.
          - Currently overdue invoices increase risk sharply.
          - Thin payment history increases uncertainty-driven risk.
        """
        on_time_penalty = (1 - on_time_rate) * 40          # up to 40 pts
        slowness_penalty = min(avg_days_to_pay / 60 * 25, 25)  # up to 25 pts
        overdue_penalty = min(current_overdue_days / 30 * 25, 25)  # up to 25 pts
        thin_history_penalty = 10 if num_paid_invoices < 3 else 0  # up to 10 pts

        score = on_time_penalty + slowness_penalty + overdue_penalty + thin_history_penalty
        return max(0.0, min(100.0, score))

    # ------------------------------ prediction -------------------------------- #

    def predict_collection_date(self, invoice: Invoice) -> date:
        """
        Predict the expected collection date for a single outstanding
        invoice using its customer's historical average days-to-pay,
        anchored to the invoice's issue date (falls back to due date logic
        if that predicted date has already passed).
        """
        profile = self.customer_profiles.get(invoice.customer_id)
        if profile is None:
            avg_days = self.DEFAULT_AVG_DAYS_TO_PAY
        else:
            avg_days = profile.avg_days_to_pay

        predicted = invoice.issue_date + timedelta(days=round(avg_days))

        # If the model predicts a date in the past relative to "as_of" but the
        # invoice is still outstanding, push the estimate to "as_of + a short
        # buffer" since the customer is clearly running late.
        if predicted < self.as_of and invoice.is_outstanding():
            buffer_days = max(3, round((profile.std_days_to_pay if profile else self.DEFAULT_STD_DAYS_TO_PAY) / 2))
            predicted = self.as_of + timedelta(days=buffer_days)

        return predicted

    # ------------------------------ forecasting -------------------------------- #

    def forecast_collections(
        self,
        horizon_days: int = 30,
        num_simulations: int = 2000,
        confidence_level: float = 0.90,
    ) -> List[CollectionForecastDay]:
        """
        Build a day-by-day expected receivable inflow schedule for the next
        `horizon_days`, including a Monte Carlo confidence band per day that
        accounts for payment-timing variability across customers.

        Returns:
            List of CollectionForecastDay, one per day in the horizon,
            ordered chronologically.
        """
        if not self.customer_profiles:
            self.build_customer_profiles()

        outstanding = [inv for inv in self.invoices if inv.is_outstanding()]
        horizon_end = self.as_of + timedelta(days=horizon_days)

        # Point estimate: bucket invoices into their predicted collection day.
        buckets: Dict[date, List[Invoice]] = {
            self.as_of + timedelta(days=d): [] for d in range(1, horizon_days + 1)
        }
        for inv in outstanding:
            predicted = self.predict_collection_date(inv)
            if self.as_of < predicted <= horizon_end:
                buckets.setdefault(predicted, []).append(inv)
            elif predicted <= self.as_of:
                # Treat as collectible "tomorrow" if the model predicts it's
                # already due.
                buckets.setdefault(self.as_of + timedelta(days=1), []).append(inv)

        # Monte Carlo: for each outstanding invoice, simulate its payment day
        # via a normal distribution around the customer's avg/std days-to-pay,
        # weighted by on_time_rate as a simple non-payment discount.
        rng = self._estimator._rng
        sims = np.zeros((num_simulations, horizon_days))

        for inv in outstanding:
            profile = self.customer_profiles.get(inv.customer_id)
            avg_days = profile.avg_days_to_pay if profile else self.DEFAULT_AVG_DAYS_TO_PAY
            std_days = max(profile.std_days_to_pay if profile else self.DEFAULT_STD_DAYS_TO_PAY, 1.0)
            collection_prob = 0.5 + 0.5 * (profile.on_time_rate if profile else 0.5)  # 0.5-1.0

            days_from_issue = rng.normal(loc=avg_days, scale=std_days, size=num_simulations)
            offsets = (
                np.array([(inv.issue_date + timedelta(days=int(round(d))) - self.as_of).days for d in days_from_issue])
            )
            offsets = np.clip(offsets, 1, horizon_days)

            will_pay = rng.random(num_simulations) < collection_prob
            for sim_idx in range(num_simulations):
                if will_pay[sim_idx]:
                    day_idx = int(offsets[sim_idx]) - 1
                    sims[sim_idx, day_idx] += inv.amount

        cumulative_sims = np.cumsum(sims, axis=1)

        schedule: List[CollectionForecastDay] = []
        for d in range(1, horizon_days + 1):
            forecast_date = self.as_of + timedelta(days=d)
            expected_amount = sum(inv.amount for inv in buckets.get(forecast_date, []))
            envelope = self._estimator.confidence_interval_from_paths(
                cumulative_sims, day_index=d - 1, confidence_level=confidence_level
            )
            schedule.append(
                CollectionForecastDay(
                    forecast_date=forecast_date,
                    expected_amount=expected_amount,
                    uncertainty=envelope,
                    contributing_invoices=[inv.invoice_id for inv in buckets.get(forecast_date, [])],
                )
            )

        return schedule

    # ------------------------------ aging report -------------------------------- #

    def aging_report(self) -> Dict[str, float]:
        """
        Bucket outstanding invoice amounts by days overdue:
        current, 1-30, 31-60, 61-90, 90+.
        """
        buckets = {"current": 0.0, "1-30": 0.0, "31-60": 0.0, "61-90": 0.0, "90+": 0.0}
        for inv in self.invoices:
            if not inv.is_outstanding():
                continue
            overdue = inv.days_overdue(self.as_of)
            if overdue == 0:
                buckets["current"] += inv.amount
            elif overdue <= 30:
                buckets["1-30"] += inv.amount
            elif overdue <= 60:
                buckets["31-60"] += inv.amount
            elif overdue <= 90:
                buckets["61-90"] += inv.amount
            else:
                buckets["90+"] += inv.amount
        return {k: round(v, 2) for k, v in buckets.items()}

    def total_outstanding(self) -> float:
        return round(sum(inv.amount for inv in self.invoices if inv.is_outstanding()), 2)

    def days_sales_outstanding(self, period_days: int = 90, credit_sales: Optional[float] = None) -> float:
        """
        Classic DSO = (Accounts Receivable / Total Credit Sales) * Number of Days.
        If `credit_sales` isn't supplied, it's inferred as the sum of all
        invoices issued within the trailing `period_days`.
        """
        if credit_sales is None:
            window_start = self.as_of - timedelta(days=period_days)
            credit_sales = sum(
                inv.amount for inv in self.invoices if window_start <= inv.issue_date <= self.as_of
            )
        if not credit_sales:
            return 0.0
        return round((self.total_outstanding() / credit_sales) * period_days, 1)

    def high_risk_customers(self, threshold: float = 60.0) -> List[CustomerProfile]:
        """Return customer profiles at or above the given risk threshold."""
        if not self.customer_profiles:
            self.build_customer_profiles()
        return sorted(
            (p for p in self.customer_profiles.values() if p.risk_score >= threshold),
            key=lambda p: p.risk_score,
            reverse=True,
        )


# --------------------------------------------------------------------------- #
# Standalone demo
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    today = date(2026, 8, 28)

    demo_invoices = [
        # Customer A: reliable, pays ~10 days after issue
        Invoice("INV-001", "cust_A", 5000, date(2026, 7, 1), date(2026, 7, 20), InvoiceStatus.PAID, date(2026, 7, 12)),
        Invoice("INV-002", "cust_A", 4200, date(2026, 7, 15), date(2026, 8, 4), InvoiceStatus.PAID, date(2026, 7, 24)),
        Invoice("INV-003", "cust_A", 6100, date(2026, 8, 20), date(2026, 9, 9)),
        # Customer B: slow payer, often late
        Invoice("INV-004", "cust_B", 3000, date(2026, 6, 1), date(2026, 6, 21), InvoiceStatus.PAID, date(2026, 7, 5)),
        Invoice("INV-005", "cust_B", 2800, date(2026, 7, 1), date(2026, 7, 21), InvoiceStatus.PAID, date(2026, 8, 2)),
        Invoice("INV-006", "cust_B", 3500, date(2026, 7, 25), date(2026, 8, 14)),
        # Customer C: brand new, no history
        Invoice("INV-007", "cust_C", 9000, date(2026, 8, 15), date(2026, 9, 4)),
    ]

    forecaster = ReceivableForecaster(as_of=today)
    forecaster.load_invoices(demo_invoices)
    profiles = forecaster.build_customer_profiles()

    print("=" * 60)
    print("CashSurvive AI — receivable_forecast.py demo")
    print("=" * 60)

    print("\nCustomer payment profiles:")
    for p in profiles.values():
        print(f"  {p.as_dict()}")

    print(f"\nTotal outstanding: ${forecaster.total_outstanding():,.2f}")
    print(f"Aging report: {forecaster.aging_report()}")
    print(f"DSO (90-day window): {forecaster.days_sales_outstanding()} days")

    high_risk = forecaster.high_risk_customers(threshold=40)
    print(f"\nHigh-risk customers (score >= 40): {[c.customer_id for c in high_risk]}")

    schedule = forecaster.forecast_collections(horizon_days=14, num_simulations=1000)
    print("\n14-day collection forecast:")
    for day in schedule:
        band = day.uncertainty
        band_str = f"[{band.lower_bound:,.0f} - {band.upper_bound:,.0f}]" if band else "n/a"
        print(f"  {day.forecast_date}  expected=${day.expected_amount:>9,.2f}  cumulative 90% CI={band_str}")
