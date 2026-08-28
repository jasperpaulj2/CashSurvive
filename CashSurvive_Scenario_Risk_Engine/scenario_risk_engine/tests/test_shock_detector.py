import pytest

from scenario_risk_engine.models import (
    FinancialState,
    Receivable,
    Payable,
    Obligation,
    SupplierRisk,
    FinancingOption,
)
from scenario_risk_engine.shock_detector import ShockDetector
from scenario_risk_engine.exceptions import InvalidFinancialStateError


@pytest.fixture
def detector() -> ShockDetector:
    return ShockDetector()


def make_state(**overrides) -> FinancialState:
    defaults = dict(
        cash_balance=5_000_000,
        minimum_cash_reserve=2_500_000,
        receivables=[
            Receivable(id="R1", amount=3_000_000, expected_days=10, probability=0.9),
        ],
        payables=[Payable(id="P1", amount=1_500_000, due_days=7)],
        upcoming_obligations=[Obligation(id="O1", amount=800_000, due_days=5)],
        supplier_risks=[
            SupplierRisk(
                supplier_id="S1",
                name="Supplier One",
                importance=0.7,
                liquidity_risk=0.2,
                dependency=0.5,
            ),
        ],
        financing_options=[
            FinancingOption(id="F1", available_amount=2_000_000, interest_rate=0.08),
        ],
    )
    defaults.update(overrides)
    return FinancialState(**defaults)


# ---------------------------------------------------------------------------
# No material change
# ---------------------------------------------------------------------------
def test_no_material_change_detected(detector):
    previous = make_state()
    current = previous.copy()
    # Trivial change well below all thresholds.
    current.cash_balance -= 1_000  # tiny fraction of 5,000,000

    events = detector.detect_changes(previous, current)
    assert all(not e.detected for e in events)
    assert not detector.any_reoptimization_required(previous, current)


# ---------------------------------------------------------------------------
# Receivable shock
# ---------------------------------------------------------------------------
def test_receivable_shock_detected_on_delay(detector):
    previous = make_state()
    current = previous.copy()
    current.receivables[0].expected_days += 15  # well above threshold
    current.receivables[0].probability = 0.5

    events = detector.detect_changes(previous, current)
    receivable_event = next(e for e in events if e.shock_type == "receivable_delay")
    assert receivable_event.detected is True
    assert receivable_event.reoptimize is True


def test_receivable_shock_not_detected_for_small_delay(detector):
    previous = make_state()
    current = previous.copy()
    current.receivables[0].expected_days += 1  # below threshold (7 days)
    current.receivables[0].probability -= 0.02  # below threshold (0.15)

    events = detector.detect_changes(previous, current)
    receivable_event = next(e for e in events if e.shock_type == "receivable_delay")
    assert receivable_event.detected is False


# ---------------------------------------------------------------------------
# Cash shock
# ---------------------------------------------------------------------------
def test_cash_shock_detected_on_large_drop(detector):
    previous = make_state()
    current = previous.copy()
    current.cash_balance = previous.cash_balance * 0.7  # 30% drop

    events = detector.detect_changes(previous, current)
    cash_event = next(e for e in events if e.shock_type == "cash_shock")
    assert cash_event.detected is True
    assert cash_event.reoptimize is True


# ---------------------------------------------------------------------------
# Financing shock
# ---------------------------------------------------------------------------
def test_financing_shock_detected_on_rate_increase(detector):
    previous = make_state()
    current = previous.copy()
    current.financing_options[0].interest_rate += 0.05  # above 0.02 threshold

    events = detector.detect_changes(previous, current)
    financing_event = next(e for e in events if e.shock_type == "financing_shock")
    assert financing_event.detected is True
    assert financing_event.reoptimize is True


# ---------------------------------------------------------------------------
# Supplier shock
# ---------------------------------------------------------------------------
def test_supplier_shock_detected_on_risk_increase(detector):
    previous = make_state()
    current = previous.copy()
    current.supplier_risks[0].liquidity_risk += 0.4  # above 0.15 threshold

    events = detector.detect_changes(previous, current)
    supplier_event = next(e for e in events if e.shock_type == "supplier_shock")
    assert supplier_event.detected is True
    assert supplier_event.reoptimize is True


# ---------------------------------------------------------------------------
# Obligation shock
# ---------------------------------------------------------------------------
def test_obligation_shock_detected_on_new_large_obligation(detector):
    previous = make_state()
    current = previous.copy()
    current.upcoming_obligations.append(
        Obligation(id="OBL-NEW", amount=2_000_000, due_days=1)
    )

    events = detector.detect_changes(previous, current)
    obligation_event = next(e for e in events if e.shock_type == "obligation_shock")
    assert obligation_event.detected is True
    assert obligation_event.reoptimize is True


def test_small_new_obligation_not_flagged(detector):
    previous = make_state()
    current = previous.copy()
    current.upcoming_obligations.append(
        Obligation(id="OBL-SMALL", amount=1_000, due_days=1)
    )

    events = detector.detect_changes(previous, current)
    obligation_event = next(e for e in events if e.shock_type == "obligation_shock")
    assert obligation_event.detected is False


# ---------------------------------------------------------------------------
# Invalid inputs
# ---------------------------------------------------------------------------
def test_none_states_raise(detector):
    with pytest.raises(InvalidFinancialStateError):
        detector.detect_changes(None, make_state())
    with pytest.raises(InvalidFinancialStateError):
        detector.detect_changes(make_state(), None)


def test_any_reoptimization_required_true_when_any_shock(detector):
    previous = make_state()
    current = previous.copy()
    current.cash_balance = previous.cash_balance * 0.5

    assert detector.any_reoptimization_required(previous, current) is True


def test_any_reoptimization_required_false_when_no_shock(detector):
    previous = make_state()
    current = previous.copy()

    assert detector.any_reoptimization_required(previous, current) is False
