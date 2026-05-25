from __future__ import annotations

import logging
from typing import Any, Dict

from app.agents.state import EACAgentState
from app.rules.accounting_rules import evaluate_record

logger = logging.getLogger(__name__)


def policy_node(state: EACAgentState) -> Dict[str, Any]:
    """Applies deterministic accounting rules then overlays LLM policy reasoning."""
    try:
        record = state["record"]
        retrieval = state["retrieval_result"]

        # Deterministic rules first — these are authoritative
        score, signals, evidence = evaluate_record(record)
        context = state["context"]
        provider = context.get("_llmProvider", "stub")
        model = context.get("_llmModel", "")

        policy_result = {
            "score": score,
            "signals": signals,
            "evidence": evidence,
            "policy_verdict": context.get("_llmPolicyVerdict", ""),
            "policy_rationale": context.get("_llmPolicyRationale", ""),
            "applicable_rules": context.get("_llmApplicableRules", []),
            "confidence_adjustment": context.get("_llmConfidenceAdjustment", 0),
            "precedent_classification": retrieval.get("precedent_classification", ""),
            "provider": provider,
            "model": model,
        }

        step = {
            "agent": "Policy & Rules Agent",
            "status": "fallback" if provider == "stub" else "completed",
            "provider": provider,
            "summary": "Fixed-asset accounting rules applied. LLM generated GAAP/IAS 16 policy rationale and confidence adjustment.",
            "output": {
                "score": score,
                "signals_count": len(signals),
                "policy_verdict": policy_result["policy_verdict"],
                "confidence_adjustment": policy_result["confidence_adjustment"],
                "applicable_rules": policy_result["applicable_rules"],
            },
        }
        return {
            "policy_result": policy_result,
            "steps": state["steps"] + [step],
            "errors": state["errors"],
        }
    except Exception as exc:
        logger.exception("policy_node failed: %s", exc)
        step = {
            "agent": "Policy & Rules Agent",
            "status": "failed",
            "provider": "error",
            "summary": f"Policy evaluation failed: {exc}",
            "output": {},
        }
        return {
            "policy_result": {"score": 0, "signals": [], "evidence": "", "confidence_adjustment": 0},
            "steps": state["steps"] + [step],
            "errors": state["errors"] + [f"policy_node: {exc}"],
        }
