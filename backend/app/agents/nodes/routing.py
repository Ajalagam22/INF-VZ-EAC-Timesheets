from __future__ import annotations

import logging
from typing import Any, Dict

from app.agents.state import EACAgentState
from app.config.settings import get_settings

logger = logging.getLogger(__name__)


def routing_node(state: EACAgentState) -> Dict[str, Any]:
    """Routes the record to the review queue or the output queue based on confidence."""
    try:
        classified = state["classified_record"]

        # BUG #2: guard against empty classified_record (e.g. classification node failed)
        if not classified:
            step = {
                "agent": "Confidence Routing Agent",
                "status": "failed",
                "provider": "deterministic",
                "summary": "classified_record was empty — routing to review.",
                "output": {"routing_decision": "review"},
            }
            return {
                "classified_record": classified,
                "routing_decision": "review",
                "steps": state["steps"] + [step],
                "errors": state["errors"] + ["routing_node: classified_record empty"],
            }

        # BUG #8: read settings at call time so config changes take effect without restart
        threshold = get_settings().review_threshold

        # Use deterministic _confidence for routing — not the LLM-adjusted value
        confidence = int(classified.get("_confidence", 0))
        classification = classified.get("_classification", "Review")

        if classification == "Review" or confidence < threshold:
            decision = "review"
        else:
            decision = "approved"

        classified["_routingState"] = decision

        step = {
            "agent": "Confidence Routing Agent",
            "status": "completed",
            "provider": "deterministic",
            "summary": f"Record routed to '{decision}' queue. Confidence {confidence} vs threshold {threshold}.",
            "output": {
                "routing_decision": decision,
                "confidence": confidence,
                "threshold": threshold,
                "classification": classification,
            },
        }
        return {
            "classified_record": classified,
            "routing_decision": decision,
            "steps": state["steps"] + [step],
            "errors": state["errors"],
        }
    except Exception as exc:
        logger.exception("routing_node failed: %s", exc)
        step = {
            "agent": "Confidence Routing Agent",
            "status": "failed",
            "provider": "error",
            "summary": f"Routing failed: {exc}",
            "output": {"routing_decision": "review"},
        }
        return {
            "classified_record": state.get("classified_record", {}),
            "routing_decision": "review",
            "steps": state["steps"] + [step],
            "errors": state["errors"] + [f"routing_node: {exc}"],
        }
