from __future__ import annotations

import logging
from typing import Any, Dict

from app.agents.llm_client import LLMClient
from app.agents.state import EACAgentState
from app.config.settings import get_settings
from app.rules.accounting_rules import evaluate_record
from app.utils.confidence_scoring import derive_confidence

_llm = LLMClient()
logger = logging.getLogger(__name__)

CONTEXT_FIELDS = (
    "_key", "_source", "_sourceFileName", "_persona",
    "employee_id", "full_name", "job_title", "job_family", "team_name",
    "org_unit", "manager_id", "week_start_date", "week_end_date",
    "actual_working_days", "meeting_count", "ticket_count", "email_volume",
    "code_commit_count", "system_activity_score", "project_code",
    "project_name", "activity_type", "hours_allocated", "submission_notes",
)


def context_node(state: EACAgentState) -> Dict[str, Any]:
    """Single combined LLM call for context, retrieval, policy, and evidence — cached in context for downstream nodes.
    Skips LLM entirely when deterministic confidence already exceeds llm_skip_threshold."""
    try:
        record = state["record"]
        raw_context = {f: record.get(f) for f in CONTEXT_FIELDS}

        score, signals, _ = evaluate_record(record)
        det_confidence = derive_confidence(score, signals, state.get("source_type", ""))

        precomp = state.get("precomputed_llm") or {}
        if precomp:
            # Async pre-fetch already happened in the orchestrator — use it directly
            c = precomp.get("content", {})
            llm_provider = precomp.get("provider", "stub")
            llm_model = precomp.get("model", "")
            skip_llm = llm_provider in {"stub", "deterministic"}
        else:
            # Fallback sync path (no pre-fetch — single-record calls or tests)
            threshold = get_settings().llm_skip_threshold
            skip_llm = threshold > 0 and det_confidence >= threshold
            if skip_llm:
                from app.agents.llm_client import LLMResponse
                llm_response = LLMResponse(provider="deterministic", model="rules-only", content=_llm.deterministic_skip_combined(raw_context))
            else:
                llm_response = _llm.analyze_record(raw_context, signals)
            c = llm_response.content
            llm_provider = llm_response.provider
            llm_model = llm_response.model

        enriched_context = {
            **raw_context,
            # context enrichment fields
            "_llmInvestmentSignals": c.get("investment_signals", []),
            "_llmOrgContext": c.get("org_context", ""),
            "_llmClassificationHints": c.get("classification_hints", []),
            "_llmEnrichmentNotes": c.get("enrichment_notes", ""),
            # retrieval fields — read by retrieval_node
            "_llmSimilarPatterns": c.get("similar_patterns", []),
            "_llmPrecedentClassification": c.get("precedent_classification", ""),
            "_llmSimilarityScore": c.get("similarity_score", 0),
            "_llmRetrievalNotes": c.get("retrieval_notes", ""),
            # policy fields — read by policy_node
            "_llmPolicyVerdict": c.get("policy_verdict", ""),
            "_llmPolicyRationale": c.get("policy_rationale", ""),
            "_llmApplicableRules": c.get("applicable_rules", []),
            "_llmConfidenceAdjustment": max(-20, min(20, int(c.get("confidence_adjustment", 0)))),
            # evidence fields — read by classification_node
            "_llmSummary": c.get("summary", ""),
            "_llmRiskFlags": c.get("risk_flags", []),
            "_llmSuggestedTags": c.get("suggested_tags", []),
            "_llmEvidenceNote": c.get("evidence_note", ""),
            "_llmConfidenceNotes": c.get("confidence_notes", []),
            # provider metadata
            "_llmProvider": llm_provider,
            "_llmModel": llm_model,
        }

        step = {
            "agent": "Context Enrichment Agent",
            "status": "fallback" if llm_provider == "stub" else "completed",
            "provider": llm_provider,
            "summary": (
                f"High-confidence record (score {det_confidence}) — LLM skipped, deterministic rules authoritative."
                if skip_llm else
                "Activity, project, and financial context built. Combined LLM call produced investment signals, precedents, policy rationale, and evidence."
            ),
            "output": {
                "investment_signals": c.get("investment_signals", []),
                "classification_hints": c.get("classification_hints", []),
                "provider": llm_provider,
                "model": llm_model,
            },
        }
        return {
            "context": enriched_context,
            "steps": state["steps"] + [step],
            "errors": state["errors"],
        }
    except Exception as exc:
        logger.exception("context_node failed: %s", exc)
        step = {
            "agent": "Context Enrichment Agent",
            "status": "failed",
            "provider": "error",
            "summary": f"Context enrichment failed: {exc}",
            "output": {},
        }
        return {
            "context": {},
            "steps": state["steps"] + [step],
            "errors": state["errors"] + [f"context_node: {exc}"],
        }
