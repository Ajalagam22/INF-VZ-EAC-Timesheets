from __future__ import annotations

from typing import Any, Dict, List

from app.config.settings import get_settings

SETTINGS = get_settings()


def derive_confidence(score: int, signals: List[Dict[str, Any]], source_type: str) -> int:
    distance = abs(score - 50)
    confidence = max(40, min(98, round(42 + distance * 1.08 + len(signals) * 3)))
    if any(signal.get("impact", 0) > 0 for signal in signals) and any(signal.get("impact", 0) < 0 for signal in signals):
        confidence -= 10
    if source_type.lower() == "docx form":
        confidence -= 4
    return max(36, min(98, confidence))


def routing_state(classification: str, confidence: int) -> str:
    if classification == "Review" or confidence < SETTINGS.review_threshold:
        return "Review"
    return classification
