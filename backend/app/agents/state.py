from __future__ import annotations

from typing import Any, Dict, List, TypedDict


class EACAgentState(TypedDict):
    record: Dict[str, Any]
    source_type: str
    context: Dict[str, Any]
    retrieval_result: Dict[str, Any]
    policy_result: Dict[str, Any]
    classified_record: Dict[str, Any]
    routing_decision: str
    reconciliation_result: Dict[str, Any]
    steps: List[Dict[str, Any]]
    errors: List[str]
    precomputed_llm: Dict[str, Any]  # pre-fetched async; empty dict = call LLM normally
