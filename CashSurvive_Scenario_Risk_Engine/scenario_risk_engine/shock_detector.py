"""
shock_detector.py
==================
Compares a previous FinancialState against a current FinancialState and
determines whether a material change occurred that warrants
re-optimization by Member 4's optimization engine.

All thresholds are configurable in config.py -- tiny, immaterial changes
never trigger reoptimize=True.
"""

from __future__ import annotations

import uuid
from typing import Dict, List

from .config import THRESHOLDS, EPSILON
from .exceptions import InvalidFinancialStateError
from .models import FinancialState, ShockEvent, Severity


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


class ShockDetector:
    """Detects material changes between two FinancialState snapshots."""

    def __init__(self, thresholds: Dict[str, float] = None) -> None:
        self.thresholds = thresholds or THRESHOLDS

    # ------------------------------------------------------------------
    def detect_changes(
        self, previous_state: FinancialState, current_state: FinancialState
    ) -> List[ShockEvent]:
        """Run every shock detector and return the full list of
        ShockEvent objects (both detected and not-detected), so callers
        can inspect the complete picture."""
        self._validate(previous_state, current_state)
        return [
            self._detect_cash_shock(previous_state, current_state),
            self._detect_receivable_shock(previous_state, current_state),
            self._detect_financing_shock(previous_state, current_state),
            self._detect_supplier_shock(previous_state, current_state),
            self._detect_obligation_shock(previous_state, current_state),
        ]

    def any_reoptimization_required(
        self, previous_state: FinancialState, current_state: FinancialState
    ) -> bool:
        """Convenience helper for Member 4: True if any detected shock
        requires re-optimization."""
        events = self.detect_changes(previous_state, current_state)
        return any(e.reoptimize for e in events)

    # ------------------------------------------------------------------
    # Individual detectors
    # ------------------------------------------------------------------
    def _detect_cash_shock(
        self, previous: FinancialState, current: FinancialState
    ) -> ShockEvent:
        prev_cash = previous.cash_balance
        curr_cash = current.cash_balance
        drop = prev_cash - curr_cash
        drop_fraction = drop / max(prev_cash, EPSILON)

        detected = drop_fraction >= self.thresholds["cash_change"]
        severity = (
            Severity.CRITICAL
            if drop_fraction >= self.thresholds["cash_change"] * 3
            else Severity.HIGH
            if drop_fraction >= self.thresholds["cash_change"] * 2
            else Severity.MEDIUM
            if detected
            else Severity.LOW
        )
        reason = (
            f"Cash balance dropped {drop_fraction * 100:.1f}% "
            f"({prev_cash:,.2f} -> {curr_cash:,.2f})"
            if detected
            else "Cash balance change within normal tolerance"
        )
        return ShockEvent(
            event_id=_new_id("shock-cash"),
            shock_type="cash_shock",
            severity=severity,
            detected=detected,
            reason=reason,
            changes={
                "previous_cash": prev_cash,
                "current_cash": curr_cash,
                "drop_fraction": round(drop_fraction, 4),
            },
            reoptimize=detected,
        )

    def _detect_receivable_shock(
        self, previous: FinancialState, current: FinancialState
    ) -> ShockEvent:
        prev_by_id = {r.id: r for r in previous.receivables}
        curr_by_id = {r.id: r for r in current.receivables}

        material_changes = []
        for rid, curr_r in curr_by_id.items():
            prev_r = prev_by_id.get(rid)
            if prev_r is None:
                continue  # new receivable, not a shock by itself
            delay = curr_r.expected_days - prev_r.expected_days
            prob_drop = prev_r.probability - curr_r.probability
            if (
                delay >= self.thresholds["receivable_delay_days"]
                or prob_drop >= self.thresholds["receivable_probability_drop"]
            ):
                material_changes.append(
                    {
                        "receivable_id": rid,
                        "delay_days": delay,
                        "probability_drop": round(prob_drop, 3),
                    }
                )

        detected = len(material_changes) > 0
        max_delay = max(
            (c["delay_days"] for c in material_changes), default=0
        )
        severity = (
            Severity.CRITICAL
            if max_delay >= self.thresholds["receivable_delay_days"] * 3
            else Severity.HIGH
            if max_delay >= self.thresholds["receivable_delay_days"] * 2
            else Severity.MEDIUM
            if detected
            else Severity.LOW
        )
        reason = (
            "Expected receivable timing and/or collection probability "
            "changed materially for: "
            + ", ".join(c["receivable_id"] for c in material_changes)
            if detected
            else "No material receivable timing/probability change detected"
        )
        return ShockEvent(
            event_id=_new_id("shock-receivable"),
            shock_type="receivable_delay",
            severity=severity,
            detected=detected,
            reason=reason,
            changes={"receivables": material_changes},
            reoptimize=detected,
        )

    def _detect_financing_shock(
        self, previous: FinancialState, current: FinancialState
    ) -> ShockEvent:
        prev_by_id = {f.id: f for f in previous.financing_options}
        curr_by_id = {f.id: f for f in current.financing_options}

        material_changes = []
        for fid, curr_f in curr_by_id.items():
            prev_f = prev_by_id.get(fid)
            if prev_f is None:
                continue
            rate_change = curr_f.interest_rate - prev_f.interest_rate
            if rate_change >= self.thresholds["financing_rate_change"]:
                material_changes.append(
                    {
                        "financing_id": fid,
                        "rate_change": round(rate_change, 4),
                    }
                )

        detected = len(material_changes) > 0
        max_change = max(
            (c["rate_change"] for c in material_changes), default=0
        )
        severity = (
            Severity.CRITICAL
            if max_change >= self.thresholds["financing_rate_change"] * 3
            else Severity.HIGH
            if max_change >= self.thresholds["financing_rate_change"] * 2
            else Severity.MEDIUM
            if detected
            else Severity.LOW
        )
        reason = (
            "Financing cost increased materially for: "
            + ", ".join(c["financing_id"] for c in material_changes)
            if detected
            else "No material financing cost change detected"
        )
        return ShockEvent(
            event_id=_new_id("shock-financing"),
            shock_type="financing_shock",
            severity=severity,
            detected=detected,
            reason=reason,
            changes={"financing_options": material_changes},
            reoptimize=detected,
        )

    def _detect_supplier_shock(
        self, previous: FinancialState, current: FinancialState
    ) -> ShockEvent:
        prev_by_id = {s.supplier_id: s for s in previous.supplier_risks}
        curr_by_id = {s.supplier_id: s for s in current.supplier_risks}

        material_changes = []
        for sid, curr_s in curr_by_id.items():
            prev_s = prev_by_id.get(sid)
            if prev_s is None:
                continue
            risk_change = curr_s.liquidity_risk - prev_s.liquidity_risk
            if risk_change >= self.thresholds["supplier_risk_change"]:
                material_changes.append(
                    {
                        "supplier_id": sid,
                        "name": curr_s.name,
                        "risk_change": round(risk_change, 3),
                    }
                )

        detected = len(material_changes) > 0
        max_change = max(
            (c["risk_change"] for c in material_changes), default=0
        )
        severity = (
            Severity.CRITICAL
            if max_change >= self.thresholds["supplier_risk_change"] * 3
            else Severity.HIGH
            if max_change >= self.thresholds["supplier_risk_change"] * 2
            else Severity.MEDIUM
            if detected
            else Severity.LOW
        )
        reason = (
            "Supplier liquidity risk increased materially for: "
            + ", ".join(c["name"] for c in material_changes)
            if detected
            else "No material supplier risk change detected"
        )
        return ShockEvent(
            event_id=_new_id("shock-supplier"),
            shock_type="supplier_shock",
            severity=severity,
            detected=detected,
            reason=reason,
            changes={"suppliers": material_changes},
            reoptimize=detected,
        )

    def _detect_obligation_shock(
        self, previous: FinancialState, current: FinancialState
    ) -> ShockEvent:
        prev_ids = {o.id for o in previous.upcoming_obligations}
        new_obligations = [
            o for o in current.upcoming_obligations if o.id not in prev_ids
        ]
        threshold_amount = (
            current.cash_balance
            * self.thresholds["new_obligation_fraction_of_cash"]
        )
        material_new = [
            o for o in new_obligations if o.amount >= threshold_amount
        ]

        detected = len(material_new) > 0
        max_amount = max((o.amount for o in material_new), default=0)
        severity = (
            Severity.CRITICAL
            if max_amount >= threshold_amount * 3
            else Severity.HIGH
            if max_amount >= threshold_amount * 2
            else Severity.MEDIUM
            if detected
            else Severity.LOW
        )
        reason = (
            "New large obligation(s) appeared: "
            + ", ".join(f"{o.id} ({o.amount:,.2f})" for o in material_new)
            if detected
            else "No new material obligations detected"
        )
        return ShockEvent(
            event_id=_new_id("shock-obligation"),
            shock_type="obligation_shock",
            severity=severity,
            detected=detected,
            reason=reason,
            changes={
                "new_obligations": [
                    {"id": o.id, "amount": o.amount} for o in material_new
                ]
            },
            reoptimize=detected,
        )

    # ------------------------------------------------------------------
    @staticmethod
    def _validate(previous: FinancialState, current: FinancialState) -> None:
        if previous is None or current is None:
            raise InvalidFinancialStateError(
                "Both previous_state and current_state must be provided"
            )
