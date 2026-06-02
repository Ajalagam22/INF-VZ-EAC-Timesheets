from __future__ import annotations

import logging
from typing import Any, Dict

from app.agents.state import EACAgentState

logger = logging.getLogger(__name__)


def reconciliation_node(state: EACAgentState) -> Dict[str, Any]:
    """Stamps each approved record with cost-centre reconciliation metadata for downstream aggregation."""
    try:
        classified = state.get("classified_record") or {}
        routing_decision = state.get("routing_decision", "review")

        cost_center = (
            classified.get("org_unit")
            or classified.get("team_name")
            or "Unassigned"
        )
        classification = classified.get("_classification", "Review")
        hours = float(classified.get("hours_allocated") or 0)
        confidence = int(classified.get("_confidence", 0))

        # Baseline: 100% OpEx. Any CapEx hour is a capitalisation recovery.
        capex_hours = hours if classification == "CapEx" else 0.0
        delta_hours = capex_hours  # recovery vs all-OpEx baseline

        included = routing_decision == "approved"
        flagged = (not included) or confidence < 50 or delta_hours > 20

        reconciliation_result = {
            "cost_center": cost_center,
            "routing_decision": routing_decision,
            "included_in_reconciliation": included,
            "baseline_opex_hours": hours,
            "classified_capex_hours": capex_hours,
            "capitalisation_delta_hours": delta_hours,
            "flagged": flagged,
        }

        step = {
            "agent": "Reconciliation & Reporting Agent",
            "status": "completed",
            "provider": "deterministic",
            "summary": (
                f"Record stamped for reconciliation. Cost centre: {cost_center}. "
                f"Routing: {routing_decision}. CapEx delta: +{delta_hours:.1f}h vs baseline."
            ),
            "output": reconciliation_result,
        }

        return {
            "classified_record": {**classified, "_reconciliation": reconciliation_result},
            "reconciliation_result": reconciliation_result,
            "steps": state["steps"] + [step],
            "errors": state["errors"],
        }
    except Exception as exc:
        logger.exception("reconciliation_node failed: %s", exc)
        step = {
            "agent": "Reconciliation & Reporting Agent",
            "status": "failed",
            "provider": "error",
            "summary": f"Reconciliation stamp failed: {exc}",
            "output": {},
        }
        return {
            "classified_record": state.get("classified_record", {}),
            "reconciliation_result": {},
            "steps": state["steps"] + [step],
            "errors": state["errors"] + [f"reconciliation_node: {exc}"],
        }
