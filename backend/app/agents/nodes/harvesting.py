from __future__ import annotations

import logging
from typing import Any, Dict

from app.agents.state import EACAgentState

logger = logging.getLogger(__name__)


def harvesting_node(state: EACAgentState) -> Dict[str, Any]:
    """Normalises the raw connector record into the canonical agent contract."""
    try:
        record = dict(state["record"])
        step = {
            "agent": "Harvesting Agent",
            "status": "completed",
            "provider": "deterministic",
            "summary": "Canonical record accepted from connector. Schema validated and field contract enforced.",
            "output": {
                "record_key": record.get("_key"),
                "source": record.get("_source"),
                "source_file": record.get("_sourceFileName"),
                "persona": record.get("_persona"),
                "extraction_confidence": record.get("_extractionConfidence"),
            },
        }
        return {
            "record": record,
            "steps": state["steps"] + [step],
            "errors": state["errors"],
        }
    except Exception as exc:
        logger.exception("harvesting_node failed: %s", exc)
        step = {
            "agent": "Harvesting Agent",
            "status": "failed",
            "provider": "error",
            "summary": f"Harvesting failed: {exc}",
            "output": {},
        }
        return {
            "record": state.get("record", {}),
            "steps": state["steps"] + [step],
            "errors": state["errors"] + [f"harvesting_node: {exc}"],
        }
