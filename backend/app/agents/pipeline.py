from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.agents.graph import eac_graph
from app.agents.llm_client import LLMClient, LLMResponse
from app.agents.state import EACAgentState
from app.config.settings import get_settings
from app.rules.accounting_rules import evaluate_record
from app.schemas.agent_schema import AgentStep, AgentTrace
from app.utils.confidence_scoring import derive_confidence

logger = logging.getLogger(__name__)
_llm = LLMClient()


@dataclass
class AgenticPipelineResult:
    record: Dict[str, Any]
    trace: AgentTrace


class AgenticPipeline:
    async def prefetch_llm(
        self,
        record: Dict[str, Any],
        source_type: str,
        semaphore: Optional[asyncio.Semaphore] = None,
    ) -> Dict[str, Any]:
        """Async-fetch the combined LLM analysis for one record, respecting the shared semaphore."""
        _sem = semaphore or asyncio.Semaphore(1)
        async with _sem:
            score, signals, _ = evaluate_record(record)
            conf = derive_confidence(score, signals, source_type)
            threshold = get_settings().llm_skip_threshold
            if threshold > 0 and conf >= threshold:
                return {"content": _llm.deterministic_skip_combined(record), "provider": "deterministic", "model": "rules-only"}
            response = await _llm.analyze_record_async(record, signals)
            return {"content": response.content, "provider": response.provider, "model": response.model}

    async def prefetch_llm_batch(
        self,
        records: List[Dict[str, Any]],
        source_type: str,
        semaphore: Optional[asyncio.Semaphore] = None,
    ) -> List[Dict[str, Any]]:
        """Send a batch of records in one LLM call. High-confidence records skip LLM individually."""
        threshold = get_settings().llm_skip_threshold
        need_llm: List[int] = []
        results: List[Dict[str, Any]] = []
        signals_map: Dict[int, list] = {}

        for i, record in enumerate(records):
            score, signals, _ = evaluate_record(record)
            conf = derive_confidence(score, signals, source_type)
            signals_map[i] = signals
            if threshold > 0 and conf >= threshold:
                results.append({"content": _llm.deterministic_skip_combined(record), "provider": "deterministic", "model": "rules-only", "_idx": i})
            else:
                need_llm.append(i)
                results.append(None)  # placeholder

        if need_llm:
            batch_records = [records[i] for i in need_llm]
            batch_signals = [signals_map[i] for i in need_llm]
            batch_contents = await _llm.analyze_batch_async(batch_records, batch_signals, semaphore)
            for j, i in enumerate(need_llm):
                content = batch_contents[j] if j < len(batch_contents) else _llm._stub_combined(records[i])
                results[i] = {"content": content, "provider": _llm.settings.llm_provider, "model": _llm.settings.llm_model}

        return results

    def execute(self, record: Dict[str, Any], source_type: str, precomputed_llm: Optional[Dict[str, Any]] = None) -> AgenticPipelineResult:
        initial_state: EACAgentState = {
            "record": record,
            "source_type": source_type,
            "context": {},
            "retrieval_result": {},
            "policy_result": {},
            "classified_record": {},
            "routing_decision": "",
            "steps": [],
            "errors": [],
            "precomputed_llm": precomputed_llm or {},
        }

        try:
            final_state = eac_graph.invoke(initial_state)
        except Exception as exc:
            logger.exception("eac_graph.invoke failed: %s", exc)
            fallback = dict(record)
            fallback["_classification"] = "Review"
            fallback["_confidence"] = 0
            fallback["_evidence"] = f"Agent pipeline failed: {exc}"
            fallback["_reviewReason"] = "Pipeline exception — manual review required."
            fallback["_routingState"] = "review"
            error_step = AgentStep(
                agent="Pipeline",
                status="failed",
                summary=f"Graph invocation failed: {exc}",
                provider="error",
                output={},
            )
            trace = AgentTrace(provider="error", model="", steps=[error_step])
            fallback["_agentTrace"] = trace.model_dump() if hasattr(trace, "model_dump") else trace.dict()
            return AgenticPipelineResult(record=fallback, trace=trace)

        steps = [
            AgentStep(
                agent=s.get("agent", ""),
                status=s.get("status", "completed"),
                summary=s.get("summary", ""),
                provider=s.get("provider", ""),
                output=s.get("output", {}),
            )
            for s in final_state.get("steps", [])
        ]

        classified = final_state.get("classified_record", record)
        provider = next((s.get("provider", "") for s in final_state.get("steps", []) if s.get("provider") not in ("", "deterministic", "stub")), "stub")
        model = classified.get("_llmModel", "")

        trace = AgentTrace(provider=provider, model=model, steps=steps)
        # Write the assembled trace unless the node already set a non-null one
        if not classified.get("_agentTrace"):
            classified["_agentTrace"] = trace.model_dump() if hasattr(trace, "model_dump") else trace.dict()

        return AgenticPipelineResult(record=classified, trace=trace)
