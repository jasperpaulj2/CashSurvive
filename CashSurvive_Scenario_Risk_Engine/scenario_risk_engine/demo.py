"""
demo.py
=======
Complete, runnable demonstration of Member 3's Scenario & Risk Engine.

Run with:

    python -m scenario_risk_engine.demo

This uses a realistic *fictional* company (no real company data) and walks
through the full pipeline:

    CURRENT STATE -> SCENARIOS -> RISK ANALYSIS -> SHOCK DETECTION
    -> REOPTIMIZATION TRIGGER

Member 4's optimization engine will consume the final REOPTIMIZATION
REQUIRED signal (and the underlying ScenarioResult/RiskResult/ShockEvent
objects) -- this module does NOT perform any optimization itself.
"""

from __future__ import annotations

from scenario_risk_engine.models import (
    FinancialState,
    Receivable,
    Payable,
    Obligation,
    SupplierRisk,
    FinancingOption,
)
from scenario_risk_engine.scenario_engine import ScenarioEngine
from scenario_risk_engine.risk_engine import RiskEngine
from scenario_risk_engine.shock_detector import ShockDetector


def _line(char: str = "-", width: int = 78) -> None:
    print(char * width)


def _header(title: str) -> None:
    print()
    _line("=")
    print(title)
    _line("=")


def build_fictional_company_state() -> FinancialState:
    """A realistic fictional mid-size trading company."""
    return FinancialState(
        cash_balance=5_000_000,  # Rs. 50L
        minimum_cash_reserve=2_500_000,  # Rs. 25L
        receivables=[
            Receivable(
                id="REC-CUSTA",
                amount=3_000_000,  # Rs. 30L
                expected_days=10,
                probability=0.90,
                description="Customer A - trade receivable",
            ),
        ],
        payables=[
            Payable(
                id="PAY-SUPA",
                amount=1_500_000,  # Rs. 15L
                due_days=7,
                description="Supplier A - raw materials",
            ),
            Payable(
                id="PAY-SUPB",
                amount=1_000_000,  # Rs. 10L
                due_days=20,
                description="Supplier B - packaging",
            ),
        ],
        upcoming_obligations=[
            Obligation(
                id="OBL-PAYROLL",
                amount=800_000,
                due_days=5,
                description="Monthly payroll",
            ),
        ],
        supplier_risks=[
            SupplierRisk(
                supplier_id="SUP-A",
                name="Supplier A",
                importance=0.9,
                liquidity_risk=0.25,
                dependency=0.8,
            ),
            SupplierRisk(
                supplier_id="SUP-B",
                name="Supplier B",
                importance=0.5,
                liquidity_risk=0.15,
                dependency=0.4,
            ),
        ],
        financing_options=[
            FinancingOption(
                id="FIN-LOC",
                available_amount=2_000_000,
                interest_rate=0.09,
                description="Line of credit",
            ),
        ],
    )


def main() -> None:
    scenario_engine = ScenarioEngine()
    risk_engine = RiskEngine()
    shock_detector = ShockDetector()

    # ------------------------------------------------------------------
    _header("STEP 0: CURRENT STATE")
    state = build_fictional_company_state()
    print(f"Cash balance:          {state.cash_balance:,.2f}")
    print(f"Minimum cash reserve:  {state.minimum_cash_reserve:,.2f}")
    print(f"Receivables:           {len(state.receivables)}")
    print(f"Payables:              {len(state.payables)}")
    print(f"Upcoming obligations:  {len(state.upcoming_obligations)}")
    print(f"Suppliers tracked:     {len(state.supplier_risks)}")
    print(f"Financing options:     {len(state.financing_options)}")

    baseline_risk = risk_engine.calculate_risk(state)
    print()
    print(f"Baseline risk score:   {baseline_risk.risk_score} "
          f"({baseline_risk.risk_level.value})")

    # ------------------------------------------------------------------
    _header("STEP 1: NORMAL SCENARIO")
    normal = scenario_engine.generate_normal_scenario(state)
    normal_result = scenario_engine.evaluate_scenario(state, normal)
    _print_scenario_result("Normal", normal_result)

    # ------------------------------------------------------------------
    _header("STEP 2: RECEIVABLE DELAY SCENARIO (15 days)")
    delay_scn = scenario_engine.generate_receivable_delay_scenario(
        state, delay_days=15
    )
    delay_result = scenario_engine.evaluate_scenario(state, delay_scn)
    _print_scenario_result("Receivable Delay (15d)", delay_result)

    # ------------------------------------------------------------------
    _header("STEP 3: CASH SHOCK SCENARIO")
    cash_shock_scn = scenario_engine.generate_cash_shock_scenario(
        state, unexpected_expense=1_200_000
    )
    cash_shock_result = scenario_engine.evaluate_scenario(
        state, cash_shock_scn
    )
    _print_scenario_result("Cash Shock", cash_shock_result)

    # Bonus scenarios for completeness (supplier stress + financing shock)
    supplier_scn = scenario_engine.generate_supplier_stress_scenario(
        state, supplier_id="SUP-A"
    )
    supplier_result = scenario_engine.evaluate_scenario(state, supplier_scn)
    _print_scenario_result("Supplier Stress (Supplier A)", supplier_result)

    financing_scn = scenario_engine.generate_financing_shock_scenario(state)
    financing_result = scenario_engine.evaluate_scenario(state, financing_scn)
    _print_scenario_result("Financing Shock", financing_result)

    # ------------------------------------------------------------------
    _header("STEP 4: RISK ANALYSIS SUMMARY (ALL SCENARIOS)")
    all_scenarios = scenario_engine.generate_all_scenarios(state)
    all_results = scenario_engine.evaluate_all(state, all_scenarios)
    for scn, res in zip(all_scenarios, all_results):
        print(f"- {scn.name:<32} risk={res.risk_score:>6.2f} "
              f"({res.risk_level.value:<8}) "
              f"liquidity={res.liquidity_status.value}")

    # ------------------------------------------------------------------
    _header("STEP 5: SIMULATE A CHANGE IN FINANCIAL CONDITIONS")
    new_state = state.copy()
    # Customer A's payment slips and becomes less certain.
    for r in new_state.receivables:
        if r.id == "REC-CUSTA":
            r.expected_days += 15
            r.probability = 0.50
    # Cash balance drops due to the delay + an unbudgeted spend.
    new_state.cash_balance -= 500_000
    print("Previous cash balance:  {:,.2f}".format(state.cash_balance))
    print("New cash balance:       {:,.2f}".format(new_state.cash_balance))
    print("Receivable REC-CUSTA:   expected_days "
          f"{state.receivables[0].expected_days} -> "
          f"{new_state.receivables[0].expected_days}, "
          f"probability {state.receivables[0].probability} -> "
          f"{new_state.receivables[0].probability}")

    # ------------------------------------------------------------------
    _header("STEP 6: SHOCK DETECTION")
    shock_events = shock_detector.detect_changes(state, new_state)
    for event in shock_events:
        flag = "DETECTED" if event.detected else "no change"
        print(f"[{flag:>9}] {event.shock_type:<18} "
              f"severity={event.severity.value:<8} - {event.reason}")

    # ------------------------------------------------------------------
    _header("STEP 7: REOPTIMIZATION TRIGGER")
    reoptimize = shock_detector.any_reoptimization_required(state, new_state)
    print()
    print("CURRENT STATE")
    print("      |")
    print("SCENARIOS")
    print("      |")
    print("RISK ANALYSIS")
    print("      |")
    print("SHOCK DETECTION")
    print("      |")
    print("REOPTIMIZATION TRIGGER")
    print()
    print(f"Reoptimization required: {str(reoptimize).upper()}")
    print()
    print("(Member 4's optimization engine would be invoked here with the")
    print(" updated FinancialState, ScenarioResults, and ShockEvents.)")


def _print_scenario_result(label: str, result) -> None:
    print(f"Scenario:         {label}")
    print(f"Projected cash:   {result.projected_cash:,.2f}")
    print(f"Cash impact:      {result.cash_impact:,.2f}")
    print(f"Liquidity ratio:  {result.liquidity_ratio}")
    print(f"Liquidity status: {result.liquidity_status.value}")
    print(f"Risk score:       {result.risk_score} ({result.risk_level.value})")
    print(f"Affected items:   {result.affected_items}")
    print()


if __name__ == "__main__":
    main()
