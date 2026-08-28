"""
uncertainty.py
==============
CashSurvive AI — Uncertainty Quantification Module

Provides Monte Carlo simulation, confidence-interval estimation, Value-at-Risk
(VaR), and best/likely/worst-case scenario analysis for cash flow and
receivable forecasts. This module has no dependency on the other forecasting
modules — it is a generic statistical toolkit that `cash_forecast.py` and
`receivable_forecast.py` build on top of.

Author: CashSurvive AI Team (Hackathon Build)
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from typing import List, Sequence, Tuple

import numpy as np


# --------------------------------------------------------------------------- #
# Data containers
# --------------------------------------------------------------------------- #

@dataclass
class ForecastUncertainty:
    """
    Holds the uncertainty envelope around a single point forecast.

    Attributes:
        mean: The expected (point) forecast value.
        std_dev: Standard deviation of the simulated outcomes.
        lower_bound: Lower edge of the confidence interval.
        upper_bound: Upper edge of the confidence interval.
        confidence_level: The confidence level used (e.g. 0.90 for 90%).
        var_95: Value at Risk at the 95% level (worst reasonably expected
            shortfall relative to the mean, expressed as a positive number).
    """
    mean: float
    std_dev: float
    lower_bound: float
    upper_bound: float
    confidence_level: float
    var_95: float

    def as_dict(self) -> dict:
        return {
            "mean": round(self.mean, 2),
            "std_dev": round(self.std_dev, 2),
            "lower_bound": round(self.lower_bound, 2),
            "upper_bound": round(self.upper_bound, 2),
            "confidence_level": self.confidence_level,
            "var_95": round(self.var_95, 2),
        }


@dataclass
class ScenarioResult:
    """Best / likely / worst case outcomes for a forecast horizon."""
    best_case: float
    likely_case: float
    worst_case: float
    best_case_label: str = "Optimistic (P90)"
    likely_case_label: str = "Expected (P50)"
    worst_case_label: str = "Conservative (P10)"

    def as_dict(self) -> dict:
        return {
            "best_case": round(self.best_case, 2),
            "likely_case": round(self.likely_case, 2),
            "worst_case": round(self.worst_case, 2),
        }


@dataclass
class SimulationPath:
    """A single simulated trajectory across a forecast horizon."""
    values: List[float] = field(default_factory=list)

    def min_value(self) -> float:
        return min(self.values) if self.values else 0.0

    def ends_negative(self) -> bool:
        return bool(self.values) and self.values[-1] < 0


# --------------------------------------------------------------------------- #
# Core estimator
# --------------------------------------------------------------------------- #

class UncertaintyEstimator:
    """
    Monte Carlo based uncertainty estimator.

    Typical usage:
        estimator = UncertaintyEstimator(seed=42)
        volatility = estimator.estimate_volatility(historical_daily_changes)
        paths = estimator.monte_carlo_cash_paths(
            starting_balance=10_000,
            daily_drift=-150,
            daily_volatility=volatility,
            num_days=30,
            num_simulations=2000,
        )
        envelope = estimator.confidence_interval_from_paths(paths, day_index=29)
    """

    def __init__(self, seed: int | None = 42):
        self._rng = np.random.default_rng(seed)

    # ---------------------- volatility / drift estimation ---------------- #

    @staticmethod
    def estimate_volatility(historical_values: Sequence[float]) -> float:
        """
        Estimate the standard deviation of period-over-period changes in a
        historical series (e.g. daily net cash flow). Falls back to 0 if
        fewer than 2 data points are supplied.
        """
        if len(historical_values) < 2:
            return 0.0
        diffs = np.diff(np.asarray(historical_values, dtype=float))
        return float(np.std(diffs, ddof=1)) if len(diffs) > 1 else float(abs(diffs[0]))

    @staticmethod
    def estimate_drift(historical_values: Sequence[float]) -> float:
        """Average period-over-period change (used as the simulation drift)."""
        if len(historical_values) < 2:
            return 0.0
        diffs = np.diff(np.asarray(historical_values, dtype=float))
        return float(np.mean(diffs))

    # ------------------------------ Monte Carlo ---------------------------- #

    def monte_carlo_cash_paths(
        self,
        starting_balance: float,
        daily_drift: float,
        daily_volatility: float,
        num_days: int,
        num_simulations: int = 1000,
    ) -> np.ndarray:
        """
        Simulate `num_simulations` random-walk cash balance trajectories over
        `num_days`, each step drawn from N(daily_drift, daily_volatility^2).

        Returns:
            A (num_simulations x num_days) numpy array of simulated balances.
        """
        if num_days <= 0:
            raise ValueError("num_days must be positive")
        if daily_volatility < 0:
            raise ValueError("daily_volatility cannot be negative")

        shocks = self._rng.normal(
            loc=daily_drift, scale=max(daily_volatility, 1e-9),
            size=(num_simulations, num_days),
        )
        cumulative = np.cumsum(shocks, axis=1)
        paths = starting_balance + cumulative
        return paths

    def confidence_interval_from_paths(
        self,
        paths: np.ndarray,
        day_index: int,
        confidence_level: float = 0.90,
    ) -> ForecastUncertainty:
        """
        Build a ForecastUncertainty envelope from simulated paths at a given
        day index (0-based).
        """
        if not (0 <= day_index < paths.shape[1]):
            raise IndexError("day_index out of range for simulated paths")

        column = paths[:, day_index]
        mean = float(np.mean(column))
        std_dev = float(np.std(column, ddof=1))

        alpha = 1 - confidence_level
        lower_pct = (alpha / 2) * 100
        upper_pct = (1 - alpha / 2) * 100
        lower_bound = float(np.percentile(column, lower_pct))
        upper_bound = float(np.percentile(column, upper_pct))

        var_95 = self.value_at_risk(column, confidence_level=0.95)

        return ForecastUncertainty(
            mean=mean,
            std_dev=std_dev,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            confidence_level=confidence_level,
            var_95=var_95,
        )

    # -------------------------------- VaR ----------------------------------- #

    @staticmethod
    def value_at_risk(outcomes: Sequence[float], confidence_level: float = 0.95) -> float:
        """
        Historical/simulation-based Value at Risk: the loss relative to the
        mean outcome that is not expected to be exceeded with the given
        confidence level. Returned as a positive number representing the
        magnitude of the potential shortfall.
        """
        if len(outcomes) == 0:
            return 0.0
        arr = np.asarray(outcomes, dtype=float)
        mean = float(np.mean(arr))
        tail_pct = (1 - confidence_level) * 100
        tail_value = float(np.percentile(arr, tail_pct))
        return max(0.0, mean - tail_value)

    # ---------------------------- scenario analysis -------------------------- #

    def scenario_analysis(
        self,
        paths: np.ndarray,
        day_index: int,
    ) -> ScenarioResult:
        """
        Derive best / likely / worst case values at a given day index using
        the P90 / P50 / P10 percentiles of the simulated distribution.
        """
        if not (0 <= day_index < paths.shape[1]):
            raise IndexError("day_index out of range for simulated paths")

        column = paths[:, day_index]
        best = float(np.percentile(column, 90))
        likely = float(np.percentile(column, 50))
        worst = float(np.percentile(column, 10))
        return ScenarioResult(best_case=best, likely_case=likely, worst_case=worst)

    # ---------------------------- shortfall probability ---------------------- #

    @staticmethod
    def probability_of_shortfall(paths: np.ndarray, threshold: float = 0.0) -> np.ndarray:
        """
        For each day in the simulated horizon, compute the fraction of
        simulated paths that fall below `threshold` (default: below zero,
        i.e. running out of cash).

        Returns:
            1D numpy array of length num_days with probabilities in [0, 1].
        """
        return np.mean(paths < threshold, axis=0)

    @staticmethod
    def first_shortfall_day(paths: np.ndarray, threshold: float = 0.0) -> Tuple[float, int | None]:
        """
        Estimate the probability-weighted "runway": the median day index
        (across simulations) at which the balance first dips below
        `threshold`. Returns (probability_ever_shortfall, median_day_or_None).
        """
        num_sims, num_days = paths.shape
        first_days = []
        for row in paths:
            below = np.where(row < threshold)[0]
            if below.size > 0:
                first_days.append(int(below[0]))
        prob_ever = len(first_days) / num_sims
        median_day = int(statistics.median(first_days)) if first_days else None
        return prob_ever, median_day


# --------------------------------------------------------------------------- #
# Standalone demo
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    print("=" * 60)
    print("CashSurvive AI — uncertainty.py demo")
    print("=" * 60)

    # Fake 30 days of historical net daily cash flow
    historical = [200, -150, 300, -400, 100, -50, -300, 250, -100, -200,
                  150, -350, -50, 400, -250, -100, 300, -450, 50, -150,
                  -200, 100, -300, 250, -400, 150, -100, -350, 200, -250]

    estimator = UncertaintyEstimator(seed=7)
    drift = estimator.estimate_drift(historical)
    vol = estimator.estimate_volatility(historical)
    print(f"Estimated daily drift: {drift:.2f}")
    print(f"Estimated daily volatility: {vol:.2f}")

    starting_balance = 15_000.0
    horizon = 30
    paths = estimator.monte_carlo_cash_paths(
        starting_balance=starting_balance,
        daily_drift=drift,
        daily_volatility=vol,
        num_days=horizon,
        num_simulations=5000,
    )

    envelope = estimator.confidence_interval_from_paths(paths, day_index=horizon - 1, confidence_level=0.90)
    print(f"\nDay {horizon} balance forecast (90% CI): {envelope.as_dict()}")

    scenario = estimator.scenario_analysis(paths, day_index=horizon - 1)
    print(f"Scenario analysis at day {horizon}: {scenario.as_dict()}")

    shortfall_probs = estimator.probability_of_shortfall(paths, threshold=0.0)
    print(f"\nProbability of negative balance by day {horizon}: {shortfall_probs[-1] * 100:.1f}%")

    prob_ever, median_day = estimator.first_shortfall_day(paths, threshold=0.0)
    if median_day is not None:
        print(f"Probability of ever going negative within {horizon} days: {prob_ever * 100:.1f}%")
        print(f"Median day of first shortfall (across at-risk simulations): day {median_day + 1}")
    else:
        print("No simulations resulted in a negative balance within the horizon.")
