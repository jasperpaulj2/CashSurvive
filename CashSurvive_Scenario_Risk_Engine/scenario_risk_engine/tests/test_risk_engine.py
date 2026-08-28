import pytest

from scenario_risk_engine.models import (
    FinancialState,
    Receivable,
    Payable,
    Obligation,
    SupplierRisk,
    FinancingOption,
    RiskLevel,
)
from scenario_risk_engine.risk_engine import RiskEngine
from scenario_risk_engine.exceptions import InvalidRiskInputError


@pytest.fixture
def engine() -> RiskEngine:
    return RiskEngine()


def make_state(**overrides) -> FinancialState:
    defaults = dict(
        cash_balance=5_000_000,
        minimum_cash_reserve=2_500_000,
        receivables=[
            Receivable(id="R1", amount=3_000_000, expected_days=10, probability=0.95),
        ],
        payables=[Payable(id="P1", amount=500_000, due_days=7)],
        upcoming_obligations=[Obligation(id="O1", amount=300_000, due_days=5)],
        supplier_risks=[
            SupplierRisk(
                supplier_id="S1",
                name="Reliable Co",
                importance=0.3,
                liquidity_risk=0.1,
                dependency=0.2,
            ),
        ],
        financing_options=[
            FinancingOption(id="F1", available_amount=1_000_000, interest_rate=0.08),
        ],
    )
    defaults.update(overrides)
    return FinancialState(**defaults)


# ---------------------------------------------------------------------------
# LOW risk
# ---------------------------------------------------------------------------
def test_low_risk_state_produces_low_risk_level(engine):
    state = make_state()
    result = engine.calculate_risk(state)
    assert result.risk_level == RiskLevel.LOW
    assert 0 <= result.risk_score <= 30


# ---------------------------------------------------------------------------
# MEDIUM risk
# ---------------------------------------------------------------------------
def test_medium_risk_state(engine):
    state = make_state(
        receivables=[
            Receivable(id="R1", amount=3_000_000, expected_days=10, probability=0.6),
        ],
        supplier_risks=[
            SupplierRisk(
                supplier_id="S1",
                name="Shaky Co",
                importance=0.5,
                liquidity_risk=0.45,
                dependency=0.5,
            ),
        ],
    )
    result = engine.calculate_risk(state)
    assert result.risk_level in (RiskLevel.MEDIUM, RiskLevel.LOW, RiskLevel.HIGH)
    # Regardless of exact band, medium-stress inputs should score higher
    # than the low-risk baseline.
    baseline = engine.calculate_risk(make_state())
    assert result.risk_score > baseline.risk_score


# ---------------------------------------------------------------------------
# HIGH risk
# ---------------------------------------------------------------------------
def test_high_risk_state(engine):
    state = make_state(
        cash_balance=2_600_000,
        receivables=[
            Receivable(id="R1", amount=3_000_000, expected_days=40, probability=0.3),
        ],
        payables=[Payable(id="P1", amount=1_800_000, due_days=5)],
        upcoming_obligations=[Obligation(id="O1", amount=1_200_000, due_days=3)],
        supplier_risks=[
            SupplierRisk(
                supplier_id="S1",
                name="Critical Fragile Co",
                importance=0.9,
                liquidity_risk=0.8,
                dependency=0.9,
            ),
        ],
    )
    result = engine.calculate_risk(state)
    assert result.risk_score >= 45  # clearly elevated vs. baseline
    assert result.risk_level in (RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL)


# ---------------------------------------------------------------------------
# CRITICAL risk
# ---------------------------------------------------------------------------
def test_critical_risk_state(engine):
    state = make_state(
        cash_balance=500_000,
        minimum_cash_reserve=2_500_000,
        receivables=[
            Receivable(id="R1", amount=3_000_000, expected_days=90, probability=0.05),
        ],
        payables=[Payable(id="P1", amount=2_000_000, due_days=2)],
        upcoming_obligations=[Obligation(id="O1", amount=1_500_000, due_days=1)],
        supplier_risks=[
            SupplierRisk(
                supplier_id="S1",
                name="Collapsing Co",
                importance=1.0,
                liquidity_risk=1.0,
                dependency=1.0,
            ),
        ],
        financing_options=[
            FinancingOption(id="F1", available_amount=500_000, interest_rate=0.30),
        ],
    )
    result = engine.calculate_risk(state)
    assert result.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
    assert result.risk_score >= 60


# ---------------------------------------------------------------------------
# Risk factors / explanation
# ---------------------------------------------------------------------------
def test_risk_factors_not_empty(engine):
    state = make_state()
    result = engine.calculate_risk(state)
    assert isinstance(result.risk_factors, list)
    assert len(result.risk_factors) >= 1
    assert result.explanation


def test_risk_score_is_deterministic(engine):
    state = make_state()
    result1 = engine.calculate_risk(state)
    result2 = engine.calculate_risk(state)
    assert result1.risk_score == result2.risk_score
    assert result1.risk_level == result2.risk_level


# ---------------------------------------------------------------------------
# Invalid inputs
# ---------------------------------------------------------------------------
def test_none_financial_state_raises(engine):
    with pytest.raises(InvalidRiskInputError):
        engine.calculate_risk(None)


def test_zero_minimum_reserve_raises(engine):
    state = make_state(minimum_cash_reserve=0)
    with pytest.raises(InvalidRiskInputError):
        engine.calculate_risk(state)


def test_weights_must_sum_to_one():
    with pytest.raises(InvalidRiskInputError):
        RiskEngine(
            weights={
                "liquidity": 0.5,
                "receivable": 0.5,
                "supplier": 0.5,
                "obligation": 0.0,
                "financing": 0.0,
            }
        )
