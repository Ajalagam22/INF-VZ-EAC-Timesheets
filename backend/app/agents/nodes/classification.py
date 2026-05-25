from __future__ import annotations

import logging
from typing import Any, Dict

from app.agents.state import EACAgentState
from app.classifiers.hybrid_classifier import HybridClassifier

_classifier = HybridClassifier()
logger = logging.getLogger(__name__)


def classification_node(state: EACAgentState) -> Dict[str, Any]:
    """Deterministic classification with LLM-generated evidence language."""
    try:
        record = state["record"]
        policy = state["policy_result"]
        context = state["context"]
        source_type = state["source_type"]

        # Merge all agent outputs into the record before classifying
        enriched = {
            **record,
            "_llmInvestmentSignals": context.get("_llmInvestmentSignals", []),
            "_llmClassificationHints": context.get("_llmClassificationHints", []),
            "_llmPolicyVerdict": policy.get("policy_verdict", ""),
            "_llmPolicyRationale": policy.get("policy_rationale", ""),
            "_llmConfidenceAdjustment": policy.get("confidence_adjustment", 0),
            "_llmApplicableRules": policy.get("applicable_rules", []),
        }

        classified = _classifier.classify(enriched, source_type)

        # Store LLM confidence adjustment separately — _confidence stays as the deterministic
        # result used by routing; _confidenceAdjusted is informational only.
        adj = int(policy.get("confidence_adjustment", 0))
        classified["_confidenceAdjusted"] = max(0, min(100, int(classified["_confidence"]) + adj))

        # Enrich evidence with policy rationale
        if policy.get("policy_rationale"):
            classified["_evidence"] = f"{classified['_evidence']}; {policy['policy_rationale']}"

        # Read evidence fields from combined LLM cache set by context_node — no extra API call
        if context.get("_llmEvidenceNote"):
            classified["_evidence"] = f"{classified['_evidence']}; {context['_llmEvidenceNote']}"
        classified["_llmProvider"] = context.get("_llmProvider", "stub")
        classified["_llmModel"] = context.get("_llmModel", "")
        classified["_llmSummary"] = context.get("_llmSummary", "")
        classified["_llmRiskFlags"] = context.get("_llmRiskFlags", [])
        classified["_llmEvidenceNote"] = context.get("_llmEvidenceNote", "")
        classified["_llmConfidenceNotes"] = context.get("_llmConfidenceNotes", [])

        step = {
            "agent": "Classification Agent",
            "status": "completed",
            "provider": "deterministic",
            "summary": "Final CapEx / OpEx / Review decision produced. Deterministic rules authoritative; LLM evidence enriched.",
            "output": {
                "classification": classified.get("_classification"),
                "confidence": classified.get("_confidence"),
                "confidence_adjusted": classified.get("_confidenceAdjusted"),
                "rule_version": classified.get("_ruleVersion"),
                "evidence_preview": (classified.get("_evidence") or "")[:120],
            },
        }
        return {
            "classified_record": classified,
            "steps": state["steps"] + [step],
            "errors": state["errors"],
        }
    except Exception as exc:
        logger.exception("classification_node failed: %s", exc)
        step = {
            "agent": "Classification Agent",
            "status": "failed",
            "provider": "error",
            "summary": f"Classification failed: {exc}",
            "output": {},
        }
        fallback = dict(state["record"])
        fallback["_classification"] = "Review"
        fallback["_confidence"] = 0
        fallback["_confidenceAdjusted"] = 0
        fallback["_evidence"] = f"Classification node error: {exc}"
        return {
            "classified_record": fallback,
            "steps": state["steps"] + [step],
            "errors": state["errors"] + [f"classification_node: {exc}"],
        }
