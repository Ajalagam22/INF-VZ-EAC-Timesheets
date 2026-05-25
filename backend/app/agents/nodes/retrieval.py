from __future__ import annotations

import logging
from typing import Any, Dict

from app.agents.llm_client import LLMClient
from app.agents.state import EACAgentState

_llm = LLMClient()
logger = logging.getLogger(__name__)


def retrieval_node(state: EACAgentState) -> Dict[str, Any]:
    """Semantic precedent retrieval — reads from combined LLM cache set by context_node."""
    try:
        context = state["context"]
        provider = context.get("_llmProvider", "stub")
        model = context.get("_llmModel", "")

        retrieval_result = {
            "similar_patterns": context.get("_llmSimilarPatterns", []),
            "precedent_classification": context.get("_llmPrecedentClassification", ""),
            "similarity_score": context.get("_llmSimilarityScore", 0),
            "retrieval_notes": context.get("_llmRetrievalNotes", ""),
            "provider": provider,
            "model": model,
        }

        step = {
            "agent": "Semantic Retrieval Agent",
            "status": "fallback" if provider == "stub" else "completed",
            "provider": provider,
            "summary": "Retrieved similar historical classification precedents from enterprise knowledge base.",
            "output": {
                "precedent_classification": retrieval_result["precedent_classification"],
                "similarity_score": retrieval_result["similarity_score"],
                "patterns_found": len(retrieval_result["similar_patterns"]),
            },
        }
        return {
            "retrieval_result": retrieval_result,
            "steps": state["steps"] + [step],
            "errors": state["errors"],
        }
    except Exception as exc:
        logger.exception("retrieval_node failed: %s", exc)
        step = {
            "agent": "Semantic Retrieval Agent",
            "status": "failed",
            "provider": "error",
            "summary": f"Precedent retrieval failed: {exc}",
            "output": {},
        }
        return {
            "retrieval_result": {},
            "steps": state["steps"] + [step],
            "errors": state["errors"] + [f"retrieval_node: {exc}"],
        }
