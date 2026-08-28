"""
cash_forecast.py
=================
CashSurvive AI — Cash Flow Forecasting Engine

The top-level orchestrator of the forecasting package. Combines:
  - known/recurring cash outflows (payroll, rent, subscriptions, loan
    payments, etc.),
  - one-off scheduled transactions,
  - predicted receivable inflows from `receivable_forecast.py`, and
  - Monte Carlo uncertainty bands from `uncertainty.py`

into a single day-by-day projected cash balance, a "runway" estimate (days
until the business runs out of cash), and shortfall alerts/recommendations.

Author: CashSurvive AI Team (Hackathon Build)
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
from typing import Dict, List, Optional

from receivable_forecast import ReceivableForecaster, CollectionForecastDay
from uncertainty import UncertaintyEstimator, ForecastUncertainty, ScenarioResult


# --------------------------------------------------------------------------- #
# Data model
# --------------------------------------------------------------------------- #

class RecurrenceType(str, Enum):
    ONE_TIME = "one_time"
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"


@dataclass
class CashFlowItem:
    """
    A known or recurring cash movement. Positive `amount` = inflow,
    negative `amount` = outflow.

    Examples:
        Payroll:      CashFlowItem("Payroll", -42000, start_date, RecurrenceType.BIWEEKLY)
        Rent:         CashFlowItem("Office rent", -6000, start_date, RecurrenceType.MONTHLY)
        SaaS revenue: CashFlowItem("Subscription revenue", 1800, start_date, RecurrenceType.DAILY)
    """
    label: str
    amount: float
    start_date: date
    recurrence: RecurrenceType = RecurrenceType.ONE_TIME
    end_date: Optional[date] = None

    def occurs_on(self, day: date) -> bool:
        if day < self.start_date:
            return False
        if self.end_date and day > self.end_date:
            return False

        if self.recurrence == RecurrenceType.ONE_TIME:
            return day == self.start_date
        if self.recurrence == RecurrenceType.DAILY:
            return True
        if self.recurrence == RecurrenceType.WEEKLY:
            return (day - self.start_date).days % 7 == 0
        if self.recurrence == RecurrenceType.BIWEEKLY:
            return (day - self.start_date).days % 14 == 0
        if self.recurrence == RecurrenceType.MONTHLY:
            return day.day == self.start_date.day
        return False


@dataclass
class DayProjection:
    """Projected cash position for a single day of the forecast horizon."""
    forecast_date: date
    scheduled_net: float          # known inflows/outflows applied that day
    receivable_inflow: float      # predicted AR collections applied that day
    projected_balance: float      # running balance after this day (point estimate)
    uncertainty: Optional[ForecastUncertainty] = None
    is_shortfall: bool = False
    line_items: List[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        d = {
            "date": self.forecast_date.isoformat(),
            "scheduled_net": round(self.scheduled_net, 2),
            "receivable_inflow": round(self.receivable_inflow, 2),
            "projected_balance": round(self.projected_balance, 2),
            "is_shortfall": self.is_shortfall,
            "line_items": self.line_items,
        }
        if self.uncertainty:
            d["uncertainty"] = self.uncertainty.as_dict()
        return d


@dataclass
class ForecastSummary:
    """High-level takeaways from a completed forecast run."""
    starting_balance: float
    ending_balance: float
    lowest_balance: float
    lowest_balance_date: date
    runway_days: Optional[int]           # None if never goes negative in horizon
    probability_of_shortfall: float       # 0-1, from Monte Carlo
    scenario: ScenarioResult
    recommendations: List[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "starting_balance": round(self.starting_balance, 2),
            "ending_balance": round(self.ending_balance, 2),
            "lowest_balance": round(self.lowest_balance, 2),
            "lowest_balance_date": self.lowest_balance_date.isoformat(),
            "runway_days": self.runway_days,
            "probability_of_shortfall_pct": round(self.probability_of_shortfall * 100, 1),
            "scenario": self.scenario.as_dict(),
            "recommendations": self.recommendations,
        }


# --------------------------------------------------------------------------- #
# Core engine
# --------------------------------------------------------------------------- #

class CashFlowForecaster:
    """
    Orchestrates a full cash flow forecast: recurring/scheduled items +
    receivables + uncertainty modeling.

    Usage:
        cff = CashFlowForecaster(starting_balance=25000, as_of=date.today())
        cff.add_cash_flow_item(CashFlowItem("Payroll", -18000, next_friday, RecurrenceType.BIWEEKLY))
        cff.add_cash_flow_item(CashFlowItem("Rent", -4000, first_of_month, RecurrenceType.MONTHLY))
        cff.attach_receivables(receivable_forecaster)
        projections = cff.forecast(horizon_days=60)
        summary = cff.summarize(projections)
    """

    def __init__(
        self,
        starting_balance: float,
        as_of: Optional[date] = None,
        historical_daily_net: Optional[List[float]] = None,
    ):
        self.starting_balance = starting_balance
        self.as_of = as_of or date.today()
        self.cash_flow_items: List[CashFlowItem] = []
        self.receivable_forecaster: Optional[ReceivableForecaster] = None
        self.historical_daily_net = historical_daily_net or []
        self._estimator = UncertaintyEstimator()

    # ------------------------------- setup ----------------------------------- #

    def add_cash_flow_item(self, item: CashFlowItem) -> None:
        self.cash_flow_items.append(item)

    def add_cash_flow_items(self, items: List[CashFlowItem]) -> None:
        self.cash_flow_items.extend(items)

    def attach_receivables(self, receivable_forecaster: ReceivableForecaster) -> None:
        """Wire in a populated ReceivableForecaster to source AR inflows."""
        self.receivable_forecaster = receivable_forecaster

    # ------------------------------ scheduled net ----------------------------- #

    def _scheduled_net_for_day(self, day: date) -> tuple[float, List[str]]:
        net = 0.0
        items_hit = []
        for item in self.cash_flow_items:
            if item.occurs_on(day):
                net += item.amount
                items_hit.append(f"{item.label}: {item.amount:+,.2f}")
        return net, items_hit

    # -------------------------------- forecast ------------------------------- #

    def forecast(
        self,
        horizon_days: int = 30,
        num_simulations: int = 2000,
        confidence_level: float = 0.90,
    ) -> List[DayProjection]:
        """
        Build the day-by-day projected cash balance for the next
        `horizon_days`, blending deterministic scheduled items with
        predicted receivable inflows, plus a Monte Carlo uncertainty band
        that captures both AR timing risk and unmodeled day-to-day noise.
        """
        if horizon_days <= 0:
            raise ValueError("horizon_days must be positive")

        # 1. Predicted receivable inflows, if attached.
        receivable_schedule: Dict[date, CollectionForecastDay] = {}
        if self.receivable_forecaster is not None:
            for day_forecast in self.receivable_forecaster.forecast_collections(
                horizon_days=horizon_days,
                num_simulations=num_simulations,
                confidence_level=confidence_level,
            ):
                receivable_schedule[day_forecast.forecast_date] = day_forecast

        # 2. Deterministic day-by-day walk (point estimates).
        projections: List[DayProjection] = []
        running_balance = self.starting_balance
        for offset in range(1, horizon_days + 1):
            day = self.as_of + timedelta(days=offset)
            scheduled_net, line_items = self._scheduled_net_for_day(day)
            receivable_inflow = receivable_schedule.get(day)
            receivable_amount = receivable_inflow.expected_amount if receivable_inflow else 0.0

            running_balance += scheduled_net + receivable_amount
            projections.append(
                DayProjection(
                    forecast_date=day,
                    scheduled_net=scheduled_net,
                    receivable_inflow=receivable_amount,
                    projected_balance=running_balance,
                    is_shortfall=running_balance < 0,
                    line_items=line_items,
                )
            )

        # 3. Monte Carlo uncertainty layer around the deterministic path.
        residual_vol = self._estimator.estimate_volatility(self.historical_daily_net) if self.historical_daily_net else 0.0
        # Even with no historical data, assume some baseline noise proportional
        # to the average scheduled cash movement so the band isn't degenerate.
        avg_abs_scheduled = (
            np.mean([abs(p.scheduled_net) for p in projections]) if projections else 0.0
        )
        baseline_noise = max(residual_vol, avg_abs_scheduled * 0.15, 50.0)

        sims = self._estimator.monte_carlo_cash_paths(
            starting_balance=0.0,        # noise only; deterministic path added back below
            daily_drift=0.0,
            daily_volatility=baseline_noise,
            num_days=horizon_days,
            num_simulations=num_simulations,
        )

        deterministic_path = np.array([p.projected_balance for p in projections])
        combined_paths = sims + deterministic_path  # broadcast noise onto point estimates

        for idx, proj in enumerate(projections):
            proj.uncertainty = self._estimator.confidence_interval_from_paths(
                combined_paths, day_index=idx, confidence_level=confidence_level
            )

        self._last_combined_paths = combined_paths  # cached for summarize()
        return projections

    # -------------------------------- summary --------------------------------- #

    def summarize(self, projections: List[DayProjection]) -> ForecastSummary:
        """Distill a completed forecast run into headline metrics + advice."""
        if not projections:
            raise ValueError("No projections to summarize; call forecast() first.")

        ending_balance = projections[-1].projected_balance
        lowest = min(projections, key=lambda p: p.projected_balance)
        shortfall_days = [p for p in projections if p.is_shortfall]
        runway_days = (shortfall_days[0].forecast_date - self.as_of).days if shortfall_days else None

        combined_paths = getattr(self, "_last_combined_paths", None)
        if combined_paths is not None:
            shortfall_probs = self._estimator.probability_of_shortfall(combined_paths, threshold=0.0)
            probability_of_shortfall = float(shortfall_probs[-1])
            scenario = self._estimator.scenario_analysis(combined_paths, day_index=len(projections) - 1)
        else:
            probability_of_shortfall = 1.0 if shortfall_days else 0.0
            scenario = ScenarioResult(best_case=ending_balance, likely_case=ending_balance, worst_case=ending_balance)

        recommendations = self._build_recommendations(
            runway_days=runway_days,
            lowest_balance=lowest.projected_balance,
            probability_of_shortfall=probability_of_shortfall,
        )

        return ForecastSummary(
            starting_balance=self.starting_balance,
            ending_balance=ending_balance,
            lowest_balance=lowest.projected_balance,
            lowest_balance_date=lowest.forecast_date,
            runway_days=runway_days,
            probability_of_shortfall=probability_of_shortfall,
            scenario=scenario,
            recommendations=recommendations,
        )

    @staticmethod
    def _build_recommendations(
        runway_days: Optional[int],
        lowest_balance: float,
        probability_of_shortfall: float,
    ) -> List[str]:
        recs: List[str] = []

        if runway_days is not None:
            if runway_days <= 7:
                recs.append(
                    f"CRITICAL: Projected cash shortfall in {runway_days} day(s). "
                    "Accelerate receivable collections and delay non-essential outflows immediately."
                )
            elif runway_days <= 30:
                recs.append(
                    f"WARNING: Projected shortfall in {runway_days} days. "
                    "Consider a short-term line of credit or renegotiating payment terms with vendors."
                )
            else:
                recs.append(
                    f"Cash shortfall projected in {runway_days} days — "
                    "still time to adjust spending or follow up on outstanding invoices."
                )
        elif lowest_balance < 0.15 * max(lowest_balance, 1):
            # (kept simple/defensive; primary signal is runway_days above)
            pass

        if probability_of_shortfall > 0.5:
            recs.append(
                f"High risk: {probability_of_shortfall * 100:.0f}% of simulated scenarios "
                "end in a negative balance. Treat the runway estimate as optimistic."
            )
        elif probability_of_shortfall > 0.2:
            recs.append(
                f"Moderate risk: {probability_of_shortfall * 100:.0f}% of simulated scenarios "
                "show a cash shortfall. Build a buffer before committing to large expenses."
            )

        if runway_days is None and probability_of_shortfall <= 0.2:
            recs.append("Cash position looks stable over the forecast horizon. No immediate action needed.")

        recs.append("Follow up with high-risk customers identified in the receivables aging report to pull forward collections.")

        return recs


# --------------------------------------------------------------------------- #
# Standalone demo
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    from receivable_forecast import Invoice, InvoiceStatus

    today = date(2026, 8, 28)

    # --- Set up receivables ---------------------------------------------------
    invoices = [
        Invoice("INV-101", "cust_A", 5000, date(2026, 7, 1), date(2026, 7, 20), InvoiceStatus.PAID, date(2026, 7, 12)),
        Invoice("INV-102", "cust_A", 4200, date(2026, 7, 15), date(2026, 8, 4), InvoiceStatus.PAID, date(2026, 7, 24)),
        Invoice("INV-103", "cust_A", 6100, date(2026, 8, 20), date(2026, 9, 9)),
        Invoice("INV-104", "cust_B", 3000, date(2026, 6, 1), date(2026, 6, 21), InvoiceStatus.PAID, date(2026, 7, 5)),
        Invoice("INV-105", "cust_B", 2800, date(2026, 7, 1), date(2026, 7, 21), InvoiceStatus.PAID, date(2026, 8, 2)),
        Invoice("INV-106", "cust_B", 3500, date(2026, 7, 25), date(2026, 8, 14)),
        Invoice("INV-107", "cust_C", 9000, date(2026, 8, 15), date(2026, 9, 4)),
    ]
    ar_forecaster = ReceivableForecaster(as_of=today)
    ar_forecaster.load_invoices(invoices)
    ar_forecaster.build_customer_profiles()

    # --- Set up recurring cash flow items --------------------------------------
    cff = CashFlowForecaster(starting_balance=20000.0, as_of=today)
    cff.add_cash_flow_items([
        CashFlowItem("Payroll", -18000, date(2026, 9, 4), RecurrenceType.BIWEEKLY),
        CashFlowItem("Office rent", -4500, date(2026, 9, 1), RecurrenceType.MONTHLY),
        CashFlowItem("SaaS tooling", -600, date(2026, 9, 1), RecurrenceType.MONTHLY),
        CashFlowItem("Retainer client revenue", 1200, date(2026, 8, 29), RecurrenceType.WEEKLY),
        CashFlowItem("Marketing spend", -800, date(2026, 9, 5), RecurrenceType.WEEKLY),
    ])
    cff.attach_receivables(ar_forecaster)

    print("=" * 60)
    print("CashSurvive AI — cash_forecast.py demo")
    print("=" * 60)

    horizon = 45
    projections = cff.forecast(horizon_days=horizon, num_simulations=3000)

    print(f"\nDay-by-day projection (first 10 of {horizon} days):")
    for p in projections[:10]:
        ci = p.uncertainty
        ci_str = f"[{ci.lower_bound:,.0f}, {ci.upper_bound:,.0f}]" if ci else "n/a"
        flag = "  <-- SHORTFALL" if p.is_shortfall else ""
        print(f"  {p.forecast_date}  balance=${p.projected_balance:>10,.2f}  90% CI={ci_str}{flag}")

    summary = cff.summarize(projections)
    print("\nForecast summary:")
    for k, v in summary.as_dict().items():
        print(f"  {k}: {v}")
