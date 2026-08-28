# CashSurvive AI — Member 3: Scenario & Risk Engine

**Autonomous Working-Capital Management Under Financial and Supply-Chain
Constraints**

This module is Member 3's independently-runnable backend component for
**CashSurvive AI**. It answers one question:

> *What could happen to the company's financial position, how serious
> would the impact be, and has the situation changed enough to require
> re-optimization?*

It does **not** build the frontend, forecasting engine, optimization
engine, database, or chatbot — those belong to other team members.

---

## What's inside

| Component | File | Purpose |
|---|---|---|
| **Scenario Engine** | `scenario_engine.py` | Generates and evaluates 5 forward-looking stress scenarios |
| **Risk Engine** | `risk_engine.py` | Transparent, configurable, weighted 0–100 risk scoring (no ML, no randomness) |
| **Shock Detector** | `shock_detector.py` | Compares two financial snapshots and flags material changes requiring re-optimization |
| **Models** | `models.py` | `FinancialState`, `Scenario`, `ScenarioResult`, `RiskResult`, `ShockEvent`, etc. |
| **Config** | `config.py` | All weights and thresholds — nothing hard-coded elsewhere |
| **Exceptions** | `exceptions.py` | `InvalidFinancialStateError`, `InvalidScenarioError`, `InvalidRiskInputError` |
| **Demo** | `demo.py` | Full runnable walk-through using fictional company data |
| **Tests** | `tests/` | 36 unit tests covering all three engines and invalid-input handling |

---

## Folder structure

```text
scenario_risk_engine/
│
├── __init__.py
├── models.py
├── scenario_engine.py
├── risk_engine.py
├── shock_detector.py
├── config.py
├── exceptions.py
├── demo.py
│
└── tests/
    ├── __init__.py
    ├── test_scenario_engine.py
    ├── test_risk_engine.py
    └── test_shock_detector.py

README.md
requirements.txt
```

---

## Installation

```bash
pip install -r requirements.txt
```

The only dependency is `pytest` (for running the test suite). The module
itself uses only the Python standard library — no external runtime
dependency at all.

Run everything from the **parent directory** of `scenario_risk_engine/`
(i.e. treat `scenario_risk_engine` as an installed/importable package).

---

## Running the demo

```bash
python -m scenario_risk_engine.demo
```

This walks through the full pipeline using realistic **fictional** company
data (no real company data is used anywhere):

```text
CURRENT STATE
      │
SCENARIOS
      │
RISK ANALYSIS
      │
SHOCK DETECTION
      │
REOPTIMIZATION TRIGGER
```

### Example output (abridged)

```text
==============================================================================
STEP 0: CURRENT STATE
==============================================================================
Cash balance:          5,000,000.00
Minimum cash reserve:  2,500,000.00
...
Baseline risk score:   17.4 (LOW)

==============================================================================
STEP 2: RECEIVABLE DELAY SCENARIO (15 days)
==============================================================================
Scenario:         Receivable Delay (15d)
Projected cash:   3,500,000.00
Cash impact:      -900,000.00
Liquidity ratio:  1.4
Liquidity status: TIGHT
Risk score:       25.73 (LOW)
Affected items:   ['REC-CUSTA']

==============================================================================
STEP 6: SHOCK DETECTION
==============================================================================
[ DETECTED] cash_shock         severity=MEDIUM   - Cash balance dropped 10.0% ...
[ DETECTED] receivable_delay   severity=HIGH     - Expected receivable timing ...
[no change] financing_shock    severity=LOW      - No material financing cost change detected
[no change] supplier_shock     severity=LOW      - No material supplier risk change detected
[no change] obligation_shock   severity=LOW      - No new material obligations detected

==============================================================================
STEP 7: REOPTIMIZATION TRIGGER
==============================================================================
Reoptimization required: TRUE
```

---

## Running the tests

```bash
pytest
# or, from the parent directory:
pytest scenario_risk_engine/tests -v
```

All 36 tests pass:

```text
36 passed in 0.06s
```

Test coverage includes:
- Scenario Engine: normal, receivable delay, cash shock, supplier stress,
  financing shock, plus invalid-input handling
- Risk Engine: low / medium / high / critical risk states, determinism,
  invalid-input handling, weight validation
- Shock Detector: no material change, receivable/cash/financing/supplier/
  obligation shocks, invalid-input handling

---

## How it works

### 1. Scenario Engine
Each scenario is produced by applying a deterministic transformation to a
**copy** of the input `FinancialState` (the original is never mutated),
then projecting cash and risk from that adjusted state:

- **NORMAL** — baseline, no changes
- **RECEIVABLE_DELAY** — pushes `expected_days` out and reduces
  `probability` for the targeted receivable(s), scaled by `delay_days`
- **CASH_SHOCK** — injects a new unexpected `Obligation`
- **SUPPLIER_STRESS** — raises a supplier's `liquidity_risk`, and flags
  other highly-dependent suppliers as indirectly affected
- **FINANCING_SHOCK** — raises `interest_rate` on financing option(s)

`generate_all_scenarios()` builds the standard set using config-driven
defaults (e.g. the most critical supplier by `importance × dependency` is
auto-selected for the supplier-stress scenario).

`evaluate_scenario()` returns a `ScenarioResult` with `projected_cash`,
`cash_impact` (delta vs. baseline), `liquidity_ratio`, `liquidity_status`,
and a full `risk_score` / `risk_level` from the Risk Engine.

### 2. Risk Engine
A weighted sum of five deterministic, explainable 0–100 factors:

| Factor | Weight (default) | Driven by |
|---|---|---|
| Liquidity | 0.35 | `projected_cash / minimum_cash_reserve` vs. target ratio |
| Receivable | 0.20 | amount-weighted `(1 − probability)` across receivables |
| Supplier | 0.20 | worst-case `liquidity_risk × (importance + dependency)/2` |
| Obligation | 0.15 | `(obligations + payables) / cash_balance` |
| Financing | 0.10 | worst-case rate increase vs. `BASE_FINANCING_RATE` |

Risk levels: `0–30 LOW`, `31–60 MEDIUM`, `61–80 HIGH`, `81–100 CRITICAL`
(configurable in `config.py`). `risk_factors` lists plain-English
explanations for every factor that is significantly elevated.

### 3. Shock Detector
Compares a `previous_state` and `current_state` and runs five independent
detectors (cash, receivable, financing, supplier, obligation), each with
its own configurable threshold in `config.py`. Tiny changes never trigger
`reoptimize=True` — only changes that cross a meaningful, tunable
threshold do.

```python
detector = ShockDetector()
events = detector.detect_changes(previous_state, current_state)
reoptimize = detector.any_reoptimization_required(previous_state, current_state)
```

---

## Integration instructions

### For Member 1 (Financial State provider)
Send data shaped like `FinancialState` (see `models.py`). You can either:

1. Construct the dataclasses directly:
   ```python
   from scenario_risk_engine import FinancialState, Receivable, Payable, Obligation, SupplierRisk, FinancingOption
   state = FinancialState(cash_balance=..., minimum_cash_reserve=..., receivables=[...], ...)
   ```
2. Or send a plain dict (e.g. from an API payload) and use the tolerant
   constructor:
   ```python
   from scenario_risk_engine import FinancialState
   state = FinancialState.from_dict(payload_dict)
   ```
   Only `cash_balance` and `minimum_cash_reserve` are required; all other
   lists default to empty and can be added incrementally as your module
   matures. Extra/unexpected fields in nested items will raise
   `InvalidFinancialStateError` with a clear message — no silent failures.

### For Member 2 (Forecast engine)
Forecast output (e.g. predicted delay days, predicted receivable
probability shifts) maps directly onto scenario parameters:

```python
from scenario_risk_engine import ScenarioEngine
engine = ScenarioEngine()
scenario = engine.generate_receivable_delay_scenario(
    state, delay_days=forecast.predicted_delay_days
)
result = engine.evaluate_scenario(state, scenario)
```

If your forecasts produce a *new* financial state snapshot (rather than a
scenario parameter), feed both the old and new snapshots into
`ShockDetector.detect_changes()` to see whether the forecast update is
material enough to matter.

### For Member 4 (Optimization engine)
Consume the structured outputs — all are dataclasses with `.to_dict()`
for trivial JSON serialization over an API boundary:

```python
from scenario_risk_engine import ScenarioEngine, RiskEngine, ShockDetector

scenario_engine = ScenarioEngine()
shock_detector = ShockDetector()

scenarios = scenario_engine.generate_all_scenarios(current_state)
results = scenario_engine.evaluate_all(current_state, scenarios)

reoptimize = shock_detector.any_reoptimization_required(previous_state, current_state)

if reoptimize:
    # Hand off: current_state, results (List[ScenarioResult]),
    # and the ShockEvent list to your optimizer.
    ...
```

`ScenarioResult`, `RiskResult`, and `ShockEvent` all expose `.to_dict()`
for direct JSON serialization when this module is wrapped in an API layer.

---

## Design principles followed

- No frontend, database, auth, payments, optimization, or LLM chatbot code
- No hard-coded company-specific financial values inside engine logic
  (the fictional numbers live only in `demo.py` and tests)
- No machine learning / no randomness — every score is derived
  deterministically from the input data
- All thresholds and weights centralized in `config.py`
- Type hints and docstrings throughout
- Structured Python objects (not printed text) as the module's real output
- Fully covered by unit tests, runnable with plain `pytest`
