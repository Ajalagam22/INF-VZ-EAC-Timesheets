from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Tuple

from app.config.settings import get_settings
from app.rules.accounting_rules import RULE_VERSION, classify_score, evaluate_record
from app.utils.confidence_scoring import derive_confidence, routing_state


class HybridClassifier:
    def __init__(self) -> None:
        self.settings = get_settings()

    def classify(self, record: Dict[str, Any], source_type: str) -> Dict[str, Any]:
        score, signals, evidence = evaluate_record(record)
        classification = classify_score(score, self.settings.review_threshold)
        confidence = derive_confidence(score, signals, source_type)
        final_classification = routing_state(classification, confidence)
        review_reason = (
            "Conflicting CapEx and OpEx signals require domain lead review."
            if final_classification == "Review" and any(signal["impact"] > 0 for signal in signals) and any(signal["impact"] < 0 for signal in signals)
            else "Confidence below routing threshold; hold for human review."
            if final_classification == "Review"
            else "Ready for output queue."
        )

        return {
            **record,
            "_classification": final_classification,
            "_confidence": confidence,
            "_evidence": evidence,
            "_reviewReason": review_reason,
            "_signals": signals,
            "_ruleVersion": RULE_VERSION,
            "_persona": record.get("_persona", self.settings.persona_name),
            "_normalizedAt": record.get("_normalizedAt", datetime.now(timezone.utc).isoformat()),
            "_override": record.get("_override"),
            "_overrideNote": record.get("_overrideNote"),
            "_llmProvider": record.get("_llmProvider"),
            "_llmModel": record.get("_llmModel"),
            "_llmSummary": record.get("_llmSummary"),
            "_llmRiskFlags": record.get("_llmRiskFlags", []),
            "_llmSuggestedTags": record.get("_llmSuggestedTags", []),
            "_llmEvidenceNote": record.get("_llmEvidenceNote", ""),
            "_llmConfidenceNotes": record.get("_llmConfidenceNotes", []),
            "_routingState": record.get("_routingState")
        }
