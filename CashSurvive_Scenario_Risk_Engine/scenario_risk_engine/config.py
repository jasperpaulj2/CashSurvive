"""
config.py
=========
Centralised configuration for the Scenario & Risk Engine.

Every "magic number" used anywhere in this module lives here so that the
behaviour of the engine can be tuned without touching business logic.

Nothing in this file is company-specific. All values are ratios,
percentages, or generic financial rules of thumb that apply to any
financial state supplied by Member 1 / Member 2.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Risk factor weights
# ---------------------------------------------------------------------------
# Must sum to 1.0. Used by RiskEngine to combine the five risk factors into
# a single 0-100 risk_score.
RISK_WEIGHTS = {
    "liquidity": 0.35,
    "receivable": 0.20,
    "supplier": 0.20,
    "obligation": 0.15,
    "financing": 0.10,
}

# ---------------------------------------------------------------------------
# Risk level bands (inclusive lower bound, inclusive upper bound)
# ---------------------------------------------------------------------------
RISK_LEVELS = {
    "LOW": (0, 30),
    "MEDIUM": (31, 60),
    "HIGH": (61, 80),
    "CRITICAL": (81, 100),
}

# ---------------------------------------------------------------------------
# Liquidity risk calculation
# ---------------------------------------------------------------------------
# liquidity_ratio = projected_cash / minimum_cash_reserve
# A ratio at or above TARGET_LIQUIDITY_RATIO is considered fully safe (risk=0).
# A ratio at or below 0 is maximally risky (risk=100).
TARGET_LIQUIDITY_RATIO = 1.5

# liquidity_status thresholds, expressed as multiples of minimum_cash_reserve
LIQUIDITY_STATUS_TIGHT_MULTIPLIER = 1.5  # below this -> "TIGHT"

# ---------------------------------------------------------------------------
# Financing risk calculation
# ---------------------------------------------------------------------------
# A "normal" baseline interest rate used to judge how stressed a financing
# option is. Any rate above this baseline contributes to financing risk.
BASE_FINANCING_RATE = 0.08  # 8%

# ---------------------------------------------------------------------------
# Scenario default parameters (used by generate_all_scenarios when the
# caller does not supply explicit parameters). These are all *relative*
# defaults, never absolute company figures.
# ---------------------------------------------------------------------------
DEFAULT_SCENARIO_PARAMS = {
    "receivable_delay_days": 15,
    # unexpected_expense is expressed as a fraction of current cash balance
    "cash_shock_fraction_of_cash": 0.20,
    "supplier_liquidity_risk_increase": 0.30,
    "financing_interest_rate_change": 0.03,  # +3 percentage points
}

# How much a receivable's collection probability degrades per day of delay.
# probability_reduction = min(RECEIVABLE_DELAY_MAX_PROB_DROP,
#                              delay_days * RECEIVABLE_DELAY_PROB_DROP_PER_DAY)
RECEIVABLE_DELAY_PROB_DROP_PER_DAY = 0.02
RECEIVABLE_DELAY_MAX_PROB_DROP = 0.6
MIN_RECEIVABLE_PROBABILITY = 0.05

# ---------------------------------------------------------------------------
# Shock detector thresholds (material-change detection)
# ---------------------------------------------------------------------------
THRESHOLDS = {
    # Cash balance drop, expressed as a fraction of the previous cash balance
    "cash_change": 0.10,
    # Receivable considered materially delayed if expected_days increases by
    # at least this many days
    "receivable_delay_days": 7,
    # Receivable considered materially riskier if probability drops by at
    # least this much (absolute, e.g. 0.20 == 20 percentage points)
    "receivable_probability_drop": 0.15,
    # Generic risk_score delta (0-100 scale) considered material
    "risk_score_change": 15,
    # Financing rate increase (absolute, e.g. 0.02 == +2 percentage points)
    "financing_rate_change": 0.02,
    # Supplier liquidity_risk increase (absolute, 0-1 scale)
    "supplier_risk_change": 0.15,
    # New obligation considered a shock if its amount exceeds this fraction
    # of the current cash balance
    "new_obligation_fraction_of_cash": 0.15,
}

# Minimum epsilon to avoid division-by-zero in ratio calculations
EPSILON = 1e-9
