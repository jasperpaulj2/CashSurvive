"""
scenario_to_risk.py
===================
Adapter coordinating Scenario Generation and Risk Evaluation (Member 3).

Executes:
1. Baseline risk evaluation via RiskEngine
2. Standard stress scenarios generation via ScenarioEngine
3. Scenario evaluation (cash impact, liquidity status, and scenario risk)
4. Optional shock detection between two financial state snapshots via ShockDetector
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import integration._path_setup  # noqa: F401

from scenario_risk_engine.models import (
    FinancialState as M3FinancialState,
    Scenario,
    ScenarioResult,
    RiskResult,
    ShockEvent,
)
from scenario_risk_engine.scenario_engine import ScenarioEngine
from scenario_risk_engine.risk_engine import RiskEngine
from scenario_risk_engine.shock_detector import ShockDetector


def run_scenario_and_risk_analysis(
    m3_state: M3FinancialState,
    custom_scenarios: Optional[List[Scenario]] = None,
    previous_state: Optional[M3FinancialState] = None,
) -> Dict[str, Any]:
    """
    Runs the full scenario and risk analysis suite against a Member 3 FinancialState:
    - Calculates baseline risk
    - Generates and evaluates all stress scenarios
    - Detects shocks if a previous state snapshot was provided
    """
    risk_engine = RiskEngine()
    scenario_engine = ScenarioEngine(risk_engine=risk_engine)

    # 1. Baseline Risk Evaluation
    baseline_risk: RiskResult = risk_engine.calculate_risk(m3_state)

    # 2. Scenarios Generation & Evaluation
    if custom_scenarios:
        scenarios = custom_scenarios
    else:
        scenarios = scenario_engine.generate_all_scenarios(m3_state)

    scenario_results: List[ScenarioResult] = scenario_engine.evaluate_all(
        m3_state, scenarios
    )

    # Combine scenario definition + evaluation results for a rich view
    scenarios_output: List[Dict[str, Any]] = []
    for scn, res in zip(scenarios, scenario_results):
        scenarios_output.append({
            "scenario_id": res.scenario_id,
            "name": scn.name,
            "scenario_type": scn.scenario_type.value if hasattr(scn.scenario_type, "value") else str(scn.scenario_type),
            "severity": scn.severity.value if hasattr(scn.severity, "value") else str(scn.severity),
            "projected_cash": res.projected_cash,
            "cash_impact": res.cash_impact,
            "liquidity_ratio": res.liquidity_ratio,
            "liquidity_status": res.liquidity_status.value if hasattr(res.liquidity_status, "value") else str(res.liquidity_status),
            "risk_score": res.risk_score,
            "risk_level": res.risk_level.value if hasattr(res.risk_level, "value") else str(res.risk_level),
            "affected_items": res.affected_items,
            "description": res.description or scn.description,
            "parameters": scn.parameters,
        })

    # 3. Shock Detection (if previous state available)
    shock_events_output: Optional[List[Dict[str, Any]]] = None
    reoptimization_required = False
    if previous_state is not None:
        detector = ShockDetector()
        shocks: List[ShockEvent] = detector.detect_changes(previous_state, m3_state)
        shock_events_output = [s.to_dict() for s in shocks]
        reoptimization_required = any(s.reoptimize for s in shocks)

    return {
        "baseline_risk": baseline_risk.to_dict(),
        "scenarios": scenarios_output,
        "shocks": shock_events_output,
        "reoptimization_required": reoptimization_required,
    }
