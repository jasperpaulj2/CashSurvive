import pytest

from scenario_risk_engine.models import (
    FinancialState,
    Receivable,
    Payable,
    Obligation,
    SupplierRisk,
    FinancingOption,
    ScenarioType,
    LiquidityStatus,
)
from scenario_risk_engine.scenario_engine import ScenarioEngine
from scenario_risk_engine.exceptions import (
    InvalidScenarioError,
    InvalidFinancialStateError,
)


@pytest.fixture
def state() -> FinancialState:
    return FinancialState(
        cash_balance=5_000_000,
        minimum_cash_reserve=2_500_000,
        receivables=[
            Receivable(id="R1", amount=3_000_000, expected_days=10, probability=0.9),
        ],
        payables=[
            Payable(id="P1", amount=1_500_000, due_days=7),
        ],
        upcoming_obligations=[
            Obligation(id="O1", amount=800_000, due_days=5),
        ],
        supplier_risks=[
            SupplierRisk(
                supplier_id="S1",
                name="Supplier One",
                importance=0.9,
                liquidity_risk=0.25,
                dependency=0.8,
            ),
        ],
        financing_options=[
            FinancingOption(id="F1", available_amount=2_000_000, interest_rate=0.09),
        ],
    )


@pytest.fixture
def engine() -> ScenarioEngine:
    return ScenarioEngine()


# ---------------------------------------------------------------------------
# Normal scenario
# ---------------------------------------------------------------------------
def test_normal_scenario_matches_baseline_projection(engine, state):
    scenario = engine.generate_normal_scenario(state)
    result = engine.evaluate_scenario(state, scenario)

    expected_cash = (
        state.cash_balance
        + state.receivables[0].amount * state.receivables[0].probability
        - state.payables[0].amount
        - state.upcoming_obligations[0].amount
    )
    assert result.projected_cash == pytest.approx(expected_cash, abs=0.01)
    assert result.cash_impact == pytest.approx(0.0, abs=0.01)
    assert result.affected_items == []


# ---------------------------------------------------------------------------
# Receivable delay
# ---------------------------------------------------------------------------
def test_receivable_delay_reduces_projected_cash(engine, state):
    scenario = engine.generate_receivable_delay_scenario(state, delay_days=15)
    assert scenario.scenario_type == ScenarioType.RECEIVABLE_DELAY

    result = engine.evaluate_scenario(state, scenario)
    normal_result = engine.evaluate_scenario(
        state, engine.generate_normal_scenario(state)
    )

    assert result.projected_cash < normal_result.projected_cash
    assert result.cash_impact < 0
    assert "R1" in result.affected_items


def test_receivable_delay_invalid_days_raises(engine, state):
    with pytest.raises(InvalidScenarioError):
        engine.generate_receivable_delay_scenario(state, delay_days=0)


def test_receivable_delay_unknown_id_raises(engine, state):
    with pytest.raises(InvalidScenarioError):
        engine.generate_receivable_delay_scenario(
            state, delay_days=10, receivable_id="DOES-NOT-EXIST"
        )


# ---------------------------------------------------------------------------
# Cash shock
# ---------------------------------------------------------------------------
def test_cash_shock_reduces_projected_cash_by_expense(engine, state):
    scenario = engine.generate_cash_shock_scenario(
        state, unexpected_expense=1_000_000
    )
    result = engine.evaluate_scenario(state, scenario)
    normal_result = engine.evaluate_scenario(
        state, engine.generate_normal_scenario(state)
    )

    assert result.projected_cash == pytest.approx(
        normal_result.projected_cash - 1_000_000, abs=0.01
    )
    assert result.cash_impact == pytest.approx(-1_000_000, abs=0.01)


def test_cash_shock_negative_expense_raises(engine, state):
    with pytest.raises(InvalidScenarioError):
        engine.generate_cash_shock_scenario(state, unexpected_expense=-100)


def test_cash_shock_default_uses_config_fraction(engine, state):
    scenario = engine.generate_cash_shock_scenario(state)
    assert scenario.parameters["unexpected_expense"] > 0


# ---------------------------------------------------------------------------
# Supplier stress
# ---------------------------------------------------------------------------
def test_supplier_stress_increases_supplier_liquidity_risk(engine, state):
    scenario = engine.generate_supplier_stress_scenario(
        state, supplier_id="S1", liquidity_risk_increase=0.5
    )
    result = engine.evaluate_scenario(state, scenario)
    normal_result = engine.evaluate_scenario(
        state, engine.generate_normal_scenario(state)
    )

    assert result.risk_score > normal_result.risk_score
    assert "S1" in result.affected_items


def test_supplier_stress_unknown_supplier_raises(engine, state):
    with pytest.raises(InvalidScenarioError):
        engine.generate_supplier_stress_scenario(state, supplier_id="NOPE")


# ---------------------------------------------------------------------------
# Financing shock
# ---------------------------------------------------------------------------
def test_financing_shock_increases_financing_risk(engine, state):
    scenario = engine.generate_financing_shock_scenario(
        state, interest_rate_change=0.10
    )
    result = engine.evaluate_scenario(state, scenario)
    normal_result = engine.evaluate_scenario(
        state, engine.generate_normal_scenario(state)
    )

    assert result.risk_score > normal_result.risk_score
    assert "F1" in result.affected_items


def test_financing_shock_no_options_raises(engine):
    empty_state = FinancialState(
        cash_balance=1_000_000, minimum_cash_reserve=500_000
    )
    with pytest.raises(InvalidScenarioError):
        engine.generate_financing_shock_scenario(empty_state, interest_rate_change=0.05)


# ---------------------------------------------------------------------------
# generate_all_scenarios / evaluate_all
# ---------------------------------------------------------------------------
def test_generate_all_scenarios_returns_expected_count(engine, state):
    scenarios = engine.generate_all_scenarios(state)
    types = {s.scenario_type for s in scenarios}
    assert ScenarioType.NORMAL in types
    assert ScenarioType.RECEIVABLE_DELAY in types
    assert ScenarioType.CASH_SHOCK in types
    assert ScenarioType.SUPPLIER_STRESS in types
    assert ScenarioType.FINANCING_SHOCK in types


def test_evaluate_all_returns_matching_length(engine, state):
    scenarios = engine.generate_all_scenarios(state)
    results = engine.evaluate_all(state, scenarios)
    assert len(results) == len(scenarios)


# ---------------------------------------------------------------------------
# Invalid financial state
# ---------------------------------------------------------------------------
def test_zero_minimum_reserve_raises(engine):
    bad_state = FinancialState(cash_balance=1_000_000, minimum_cash_reserve=0)
    with pytest.raises(InvalidFinancialStateError):
        engine.generate_normal_scenario(bad_state)


def test_negative_cash_balance_raises_on_construction():
    with pytest.raises(InvalidFinancialStateError):
        FinancialState(cash_balance=-1, minimum_cash_reserve=100)


def test_liquidity_status_negative_when_cash_shock_large(engine, state):
    scenario = engine.generate_cash_shock_scenario(
        state, unexpected_expense=10_000_000
    )
    result = engine.evaluate_scenario(state, scenario)
    assert result.liquidity_status in (
        LiquidityStatus.NEGATIVE,
        LiquidityStatus.BELOW_MINIMUM,
    )
