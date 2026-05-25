from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

from app.config.settings import get_settings

logger = logging.getLogger(__name__)

litellm_completion = None
litellm_acompletion = None
_litellm_loaded = False


def _load_litellm() -> None:
    global litellm_completion, litellm_acompletion, _litellm_loaded
    if _litellm_loaded:
        return
    _litellm_loaded = True
    try:
        from litellm import completion, acompletion
    except Exception:  # pragma: no cover - optional dependency
        litellm_completion = None
        litellm_acompletion = None
        return
    litellm_completion = completion
    litellm_acompletion = acompletion


@dataclass
class LLMResponse:
    provider: str
    model: str
    content: Dict[str, Any]
    raw_text: str = ""


class LLMClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def available(self) -> bool:
        if self.settings.llm_provider == "azure_openai":
            configured = bool(self.settings.llm_api_base_url and self.settings.llm_api_key)
        elif self.settings.llm_provider in {"openai", "openai_compatible"}:
            configured = bool(self.settings.llm_api_key)
        else:
            configured = bool(self.settings.llm_api_key or self.settings.llm_api_base_url)
        if not configured:
            return False
        _load_litellm()
        return litellm_completion is not None

    def summarize_activity(self, payload: Dict[str, Any]) -> LLMResponse:
        prompt = self._build_prompt(payload)
        if not self.available:
            return LLMResponse(
                provider="stub",
                model="local-stub",
                content=self._stub_response(payload),
            )

        response_text = self._chat_completion(prompt)
        parsed = self._parse_json(response_text)
        if parsed is None:
            parsed = self._stub_response(payload)
        return LLMResponse(
            provider=self.settings.llm_provider,
            model=self.settings.llm_model,
            content=parsed,
            raw_text=response_text
        )

    @property
    def available_async(self) -> bool:
        if not self.available:
            return False
        return litellm_acompletion is not None

    async def analyze_record_async(self, record: Dict[str, Any], signals: list) -> LLMResponse:
        """Async version of analyze_record — uses litellm.acompletion for true concurrency."""
        if not self.available_async:
            return LLMResponse(provider="stub", model="local-stub", content=self._stub_combined(record))
        prompt = (
            "You are an enterprise capital labor classification agent. "
            "Analyze this employee activity record and return strictly valid JSON with ALL of these keys: "
            "investment_signals (list of strings), org_context (string), classification_hints (list of strings), "
            "enrichment_notes (string), similar_patterns (list of strings), "
            "precedent_classification (CapEx|OpEx|Review), similarity_score (integer 0-100), "
            "retrieval_notes (string), policy_verdict (capitalize|expense|uncertain), "
            "policy_rationale (string), applicable_rules (list of strings), "
            "confidence_adjustment (integer -20 to 20), summary (string), "
            "risk_flags (list of strings), suggested_tags (list of strings), "
            "evidence_note (string), confidence_notes (list of strings). "
            f"Record: {json.dumps(record, ensure_ascii=True, default=str)} "
            f"Signals: {json.dumps(signals, ensure_ascii=True, default=str)}"
        )
        text = await self._chat_completion_async(prompt)
        parsed = self._parse_json(text)
        return LLMResponse(
            provider=self.settings.llm_provider, model=self.settings.llm_model,
            content=parsed or self._stub_combined(record), raw_text=text
        )

    async def analyze_batch_async(
        self,
        records: list,
        signals_list: list,
        semaphore: "asyncio.Semaphore | None" = None,
    ) -> list:
        """Send multiple records in one API call and return one result dict per record."""
        import asyncio as _asyncio
        n = len(records)
        if not self.available_async or n == 0:
            return [self._stub_combined(r) for r in records]
        prompt = (
            f"You are an enterprise capital labor classification agent. "
            f"Analyze these {n} employee activity records and return a JSON ARRAY of exactly {n} objects "
            "in the same order. Each object must have ALL of these keys: "
            "investment_signals (list), org_context (string), classification_hints (list), "
            "enrichment_notes (string), similar_patterns (list), "
            "precedent_classification (CapEx|OpEx|Review), similarity_score (0-100 integer), "
            "retrieval_notes (string), policy_verdict (capitalize|expense|uncertain), "
            "policy_rationale (string), applicable_rules (list), "
            "confidence_adjustment (-20 to 20 integer), summary (string), "
            "risk_flags (list), suggested_tags (list), "
            "evidence_note (string), confidence_notes (list). "
            f"Records: {json.dumps(records, ensure_ascii=True, default=str)} "
            f"Signals: {json.dumps(signals_list, ensure_ascii=True, default=str)}"
        )
        max_tokens = min(n * 600, 8192)
        _sem = semaphore or _asyncio.Semaphore(1)
        async with _sem:
            text = await self._chat_completion_async(prompt, max_tokens_override=max_tokens)
        parsed = self._parse_json_array(text, n)
        if parsed and len(parsed) == n:
            return parsed
        return [self._stub_combined(r) for r in records]

    def _parse_json_array(self, text: str, expected: int) -> list:
        stripped = text.strip()
        if stripped.startswith("```"):
            stripped = stripped.strip("`")
            if stripped.startswith("json"):
                stripped = stripped[4:]
        start = stripped.find("[")
        if start < 0:
            return []
        depth = 0
        in_string = False
        escape_next = False
        for i, ch in enumerate(stripped[start:], start=start):
            if escape_next:
                escape_next = False
                continue
            if ch == "\\" and in_string:
                escape_next = True
                continue
            if ch == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    try:
                        result = json.loads(stripped[start:i + 1])
                        if isinstance(result, list):
                            return result
                    except json.JSONDecodeError:
                        return []
        return []

    async def _chat_completion_async(self, prompt: str, max_tokens_override: int | None = None) -> str:
        messages = [
            {"role": "system", "content": "Return strictly valid JSON."},
            {"role": "user", "content": prompt},
        ]
        kwargs: Dict[str, Any] = {
            "messages": messages,
            "temperature": self.settings.llm_temperature,
            "max_tokens": max_tokens_override or self.settings.llm_max_tokens,
        }
        if self.settings.llm_provider == "azure_openai":
            kwargs.update({
                "model": f"azure/{self.settings.llm_model}",
                "api_base": self.settings.llm_api_base_url,
                "api_key": self.settings.llm_api_key,
                "api_version": self.settings.llm_api_version,
            })
        elif self.settings.llm_provider in {"openai", "openai_compatible"}:
            kwargs.update({"model": self.settings.llm_model, "api_key": self.settings.llm_api_key})
            if self.settings.llm_api_base_url:
                kwargs["api_base"] = self.settings.llm_api_base_url
        else:
            kwargs.update({
                "model": self.settings.llm_model,
                "api_key": self.settings.llm_api_key or None,
                "api_base": self.settings.llm_api_base_url or None,
            })
        kwargs["timeout"] = self.settings.llm_timeout_seconds
        try:
            response = await litellm_acompletion(**kwargs)
        except Exception as exc:
            logger.warning("Async LLM completion failed (%s): %s", self.settings.llm_provider, exc)
            return ""
        choice = None
        try:
            choice = response.choices[0]
        except Exception:
            choice = None
        if choice is None:
            return ""
        message = getattr(choice, "message", None)
        if message is None and isinstance(choice, dict):
            message = choice.get("message")
        if isinstance(message, dict):
            return str(message.get("content") or "")
        return str(getattr(message, "content", "") or "")

    def analyze_record(self, record: Dict[str, Any], signals: list) -> LLMResponse:
        """Single combined call replacing enrich_context + retrieve_precedents + apply_policy_reasoning + summarize_activity."""
        if not self.available:
            return LLMResponse(provider="stub", model="local-stub", content=self._stub_combined(record))
        prompt = (
            "You are an enterprise capital labor classification agent. "
            "Analyze this employee activity record and return strictly valid JSON with ALL of these keys: "
            "investment_signals (list of strings), org_context (string), classification_hints (list of strings), "
            "enrichment_notes (string), similar_patterns (list of strings), "
            "precedent_classification (CapEx|OpEx|Review), similarity_score (integer 0-100), "
            "retrieval_notes (string), policy_verdict (capitalize|expense|uncertain), "
            "policy_rationale (string), applicable_rules (list of strings), "
            "confidence_adjustment (integer -20 to 20), summary (string), "
            "risk_flags (list of strings), suggested_tags (list of strings), "
            "evidence_note (string), confidence_notes (list of strings). "
            f"Record: {json.dumps(record, ensure_ascii=True, default=str)} "
            f"Signals: {json.dumps(signals, ensure_ascii=True, default=str)}"
        )
        text = self._chat_completion(prompt)
        parsed = self._parse_json(text)
        return LLMResponse(
            provider=self.settings.llm_provider, model=self.settings.llm_model,
            content=parsed or self._stub_combined(record), raw_text=text
        )

    def _stub_combined(self, record: Dict[str, Any]) -> Dict[str, Any]:
        return {
            **self._stub_context(record),
            **self._stub_retrieval(record),
            **self._stub_policy(record),
            **self._stub_response(record),
        }

    def deterministic_skip_combined(self, record: Dict[str, Any]) -> Dict[str, Any]:
        summary = f"{record.get('activity_type') or 'Activity'} in {record.get('team_name') or 'unassigned team'}"
        return {
            "investment_signals": [str(record.get("project_code") or "unknown project")],
            "org_context": f"Activity in {record.get('team_name') or 'unassigned team'}",
            "classification_hints": [str(record.get("activity_type") or "unclassified")],
            "enrichment_notes": "LLM skipped because deterministic policy confidence met the configured threshold.",
            "similar_patterns": [],
            "precedent_classification": "",
            "similarity_score": 0,
            "retrieval_notes": "Precedent retrieval skipped for a high-confidence deterministic record.",
            "policy_verdict": "deterministic",
            "policy_rationale": "Policy-led deterministic rules were authoritative for this record.",
            "applicable_rules": [],
            "confidence_adjustment": 0,
            "summary": summary,
            "risk_flags": [],
            "suggested_tags": [str(record.get("project_code") or "uncategorized")],
            "evidence_note": "LLM provider is configured, but this record did not require an LLM call.",
            "confidence_notes": ["Deterministic classification confidence met or exceeded LLM_SKIP_THRESHOLD."],
        }

    def enrich_context(self, context: Dict[str, Any]) -> LLMResponse:
        """Context Enrichment Agent — extracts investment signals and org context."""
        if not self.available:
            return LLMResponse(provider="stub", model="local-stub", content=self._stub_context(context))
        prompt = (
            "You are an enterprise capital activity context enrichment agent. "
            "Analyze this employee activity record and return strictly valid JSON with keys: "
            "investment_signals (list of strings), org_context (string), "
            "classification_hints (list of strings), enrichment_notes (string). "
            f"Record: {json.dumps(context, ensure_ascii=True, default=str)}"
        )
        text = self._chat_completion(prompt)
        parsed = self._parse_json(text)
        return LLMResponse(
            provider=self.settings.llm_provider, model=self.settings.llm_model,
            content=parsed or self._stub_context(context), raw_text=text
        )

    def retrieve_precedents(self, context: Dict[str, Any]) -> LLMResponse:
        """Semantic Retrieval Agent — finds historical classification precedents."""
        if not self.available:
            return LLMResponse(provider="stub", model="local-stub", content=self._stub_retrieval(context))
        prompt = (
            "You are a semantic precedent retrieval agent for capital labor classification. "
            "Based on this activity context, identify similar historical classification patterns. "
            "Return strictly valid JSON with keys: "
            "similar_patterns (list of strings), precedent_classification (CapEx|OpEx|Review), "
            "similarity_score (integer 0-100), retrieval_notes (string). "
            f"Context: {json.dumps(context, ensure_ascii=True, default=str)}"
        )
        text = self._chat_completion(prompt)
        parsed = self._parse_json(text)
        return LLMResponse(
            provider=self.settings.llm_provider, model=self.settings.llm_model,
            content=parsed or self._stub_retrieval(context), raw_text=text
        )

    def apply_policy_reasoning(self, record: Dict[str, Any], signals: list) -> LLMResponse:
        """Policy & Rules Agent — GAAP/IAS 16 rationale and confidence adjustment."""
        if not self.available:
            return LLMResponse(provider="stub", model="local-stub", content=self._stub_policy(record))
        prompt = (
            "You are a fixed-asset accounting policy agent applying GAAP/IAS 16 capitalization rules. "
            "Determine whether this activity capitalizes as a long-lived asset or is an operating expense. "
            "Return strictly valid JSON with keys: "
            "policy_verdict (capitalize|expense|uncertain), policy_rationale (string), "
            "applicable_rules (list of strings), confidence_adjustment (integer -20 to +20). "
            f"Record: {json.dumps(record, ensure_ascii=True, default=str)} "
            f"Signals: {json.dumps(signals, ensure_ascii=True, default=str)}"
        )
        text = self._chat_completion(prompt)
        parsed = self._parse_json(text)
        return LLMResponse(
            provider=self.settings.llm_provider, model=self.settings.llm_model,
            content=parsed or self._stub_policy(record), raw_text=text
        )

    def _stub_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "investment_signals": [str(context.get("project_code") or "unknown project")],
            "org_context": f"Activity in {context.get('team_name') or 'unassigned team'}",
            "classification_hints": [str(context.get("activity_type") or "unclassified")],
            "enrichment_notes": "",
        }

    def _stub_retrieval(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "similar_patterns": [],
            "precedent_classification": "",
            "similarity_score": 0,
            "retrieval_notes": "",
        }

    def _stub_policy(self, record: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "policy_verdict": "uncertain",
            "policy_rationale": "",
            "applicable_rules": [],
            "confidence_adjustment": 0,
        }

    def _build_prompt(self, payload: Dict[str, Any]) -> str:
        return (
            "You are an enterprise employee activity reasoning agent. "
            "Return JSON with keys summary, risk_flags, suggested_tags, evidence_note, and confidence_notes. "
            "Do not override policy decisions. "
            f"Record: {json.dumps(payload, ensure_ascii=True, default=str)}"
        )

    def _chat_completion(self, prompt: str) -> str:
        messages = [
            {
                "role": "system",
                "content": "Return strictly valid JSON."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        kwargs: Dict[str, Any] = {
            "messages": messages,
            "temperature": self.settings.llm_temperature,
            "max_tokens": self.settings.llm_max_tokens,
        }

        if self.settings.llm_provider == "azure_openai":
            kwargs.update(
                {
                    "model": f"azure/{self.settings.llm_model}",
                    "api_base": self.settings.llm_api_base_url,
                    "api_key": self.settings.llm_api_key,
                    "api_version": self.settings.llm_api_version,
                }
            )
        elif self.settings.llm_provider in {"openai", "openai_compatible"}:
            kwargs.update(
                {
                    "model": self.settings.llm_model,
                    "api_key": self.settings.llm_api_key,
                }
            )
            if self.settings.llm_api_base_url:
                kwargs["api_base"] = self.settings.llm_api_base_url
        else:
            kwargs.update(
                {
                    "model": self.settings.llm_model,
                    "api_key": self.settings.llm_api_key or None,
                    "api_base": self.settings.llm_api_base_url or None,
                }
            )

        kwargs["timeout"] = self.settings.llm_timeout_seconds

        try:
            response = litellm_completion(**kwargs)
        except Exception as exc:
            logger.warning("LLM completion failed (%s): %s", self.settings.llm_provider, exc)
            return ""

        choice = None
        try:
            choice = response.choices[0]
        except Exception:
            choice = None
        if choice is None:
            return ""

        message = getattr(choice, "message", None)
        if message is None and isinstance(choice, dict):
            message = choice.get("message")

        if isinstance(message, dict):
            return str(message.get("content") or "")

        return str(getattr(message, "content", "") or "")

    def _parse_json(self, text: str) -> Optional[Dict[str, Any]]:
        stripped = text.strip()
        if not stripped:
            return None
        if stripped.startswith("```"):
            stripped = stripped.strip("`")
            if stripped.startswith("json"):
                stripped = stripped[4:]
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            # Depth-track braces to find the matching closing } rather than using
            # rfind which breaks when } appears inside string values.
            start = stripped.find("{")
            if start < 0:
                return None
            depth = 0
            in_string = False
            escape_next = False
            for i, ch in enumerate(stripped[start:], start=start):
                if escape_next:
                    escape_next = False
                    continue
                if ch == "\\" and in_string:
                    escape_next = True
                    continue
                if ch == '"':
                    in_string = not in_string
                    continue
                if in_string:
                    continue
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(stripped[start : i + 1])
                        except json.JSONDecodeError:
                            return None
            return None

    def _stub_response(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        summary = f"{payload.get('activity_type') or 'Activity'} in {payload.get('team_name') or 'unassigned team'}"
        return {
            "summary": summary,
            "risk_flags": [],
            "suggested_tags": [str(payload.get("project_code") or "uncategorized")],
            "evidence_note": "",
            "confidence_notes": ["Policy-led deterministic classification remains authoritative."]
        }
