from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, Iterable, Iterator, List, Tuple
from uuid import uuid4

from sqlalchemy.orm import Session

from app.audit.audit_service import AuditService
from app.agents.pipeline import AgenticPipeline
from app.connectors.docx.docx_connector import DocxConnector
from app.connectors.excel.excel_connector import ExcelConnector
from app.config.settings import get_settings
from app.models.activity_record import ActivityRecord, BatchRun
from app.schemas.activity_schema import RunManifest
from app.state import progress_store


def _chunks(lst: List[Any], size: int) -> Iterator[List[Any]]:
    for i in range(0, len(lst), size):
        yield lst[i : i + size]


@dataclass
class OrchestrationResult:
    run_id: str
    source_type: str
    source_file_name: str
    records: List[Dict[str, Any]] = field(default_factory=list)
    manifest: RunManifest | None = None
    trace: Dict[str, Any] = field(default_factory=dict)


class FlowOrchestrator:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.audit = AuditService()
        self.agentic_pipeline = AgenticPipeline()
        self.excel_connector = ExcelConnector()
        self.docx_connector = DocxConnector()

    def run_excel(
        self,
        db: Session,
        payload: bytes,
        filename: str,
        progress_callback: Callable[[Dict[str, Any]], None] | None = None,
    ) -> OrchestrationResult:
        return asyncio.run(self._run_pipeline_async(db, payload, filename, source_type="Excel", progress_callback=progress_callback))

    def run_docx_zip(
        self,
        db: Session,
        payload: bytes,
        filename: str,
        progress_callback: Callable[[Dict[str, Any]], None] | None = None,
    ) -> OrchestrationResult:
        return asyncio.run(self._run_pipeline_async(db, payload, filename, source_type="DOCX form", progress_callback=progress_callback))

    async def _run_pipeline_async(
        self,
        db: Session,
        payload: bytes,
        filename: str,
        source_type: str,
        progress_callback: Callable[[Dict[str, Any]], None] | None = None,
    ) -> OrchestrationResult:
        run_id = uuid4().hex
        start = time.time()
        extracted_at = time.time()

        if source_type == "Excel":
            raw_records = self.excel_connector.extract(payload, filename)
            normalized_records = self.excel_connector.normalize(raw_records, filename)
            validation_errors = self.excel_connector.validate(normalized_records)
        else:
            raw_records = self.docx_connector.extract(payload, filename)
            normalized_records = self.docx_connector.normalize(raw_records, filename)
            validation_errors = self.docx_connector.validate(normalized_records)

        extraction_elapsed = time.time() - extracted_at
        classified_records: List[Dict[str, Any]] = []
        matched_excel = self._excel_key_set(db) if source_type != "Excel" else set()
        processed = 0
        escalated = 0
        quarantined = 0

        def emit_progress(stage: str) -> None:
            if not progress_callback:
                return
            progress_callback(
                {
                    "run_id": run_id,
                    "stage": stage,
                    "processed": processed,
                    "classified": len(classified_records),
                    "quarantined": quarantined,
                    "escalated": escalated,
                    "failed": len(validation_errors),
                    "matched_excel": sum(int(record.get("_matchedExcel", 0)) for record in classified_records),
                }
            )

        emit_progress("normalizing records")

        # Quarantine pass — these skip the pipeline entirely
        to_classify: List[Dict[str, Any]] = []
        for record in normalized_records:
            processed += 1
            row_quality = dict(record.get("_rowQuality") or {})
            if row_quality.get("status") == "quarantined":
                quarantined += 1
                quarantined_record = dict(record)
                quarantined_record["_processingStatus"] = "quarantined"
                quarantined_record["_classification"] = "Review"
                quarantined_record["_confidence"] = 0
                quarantined_record["_evidence"] = "Quarantined before classification due to row quality issues."
                quarantined_record["_reviewReason"] = "; ".join(row_quality.get("issues") or ["Row quality checks failed."])
                persisted = self._persist_record(db, run_id, filename, quarantined_record)
                classified_records.append(persisted)
                progress_store.push(run_id, [persisted])
                self.audit.record_event(
                    db,
                    run_id=run_id,
                    record_uid=persisted["_recordUid"],
                    event_type="quarantined",
                    payload={"row_quality": row_quality, "matched_excel": persisted["_matchedExcel"]},
                )
            else:
                to_classify.append(record)

        emit_progress("classifying records")

        # Semaphore caps concurrent LLM calls; process each record as its LLM call finishes
        semaphore = asyncio.Semaphore(self.settings.llm_concurrency)

        async def _classify_one(record: Dict[str, Any]) -> None:
            nonlocal escalated
            llm_data = await self.agentic_pipeline.prefetch_llm(record, source_type, semaphore)
            precomp = llm_data if isinstance(llm_data, dict) else {}
            try:
                classified = self.agentic_pipeline.execute(record, source_type, precomputed_llm=precomp).record
            except Exception as exc:
                classified = dict(record)
                classified["_classification"] = "Review"
                classified["_confidence"] = 0
                classified["_evidence"] = f"Pipeline exception: {exc}"
                classified["_reviewReason"] = "Unhandled pipeline error — manual review required."
                classified["_routingState"] = "review"
                classified["_agentTrace"] = {
                    "provider": "error",
                    "model": "",
                    "steps": [{"agent": "Pipeline", "status": "failed", "summary": str(exc), "provider": "error", "output": {}}],
                }

            if source_type != "Excel" and matched_excel:
                classified["_matchedExcel"] = int(classified["_key"] in matched_excel)
            else:
                classified["_matchedExcel"] = 1 if source_type == "Excel" else 0
            if classified["_classification"] == "Review" or classified["_confidence"] < self.settings.review_threshold:
                escalated += 1

            persisted = self._persist_record(db, run_id, filename, classified)
            classified_records.append(persisted)
            progress_store.push(run_id, [persisted])
            self.audit.record_event(
                db,
                run_id=run_id,
                record_uid=persisted["_recordUid"],
                event_type="classified",
                payload={
                    "classification": persisted["_classification"],
                    "confidence": persisted["_confidence"],
                    "evidence": persisted["_evidence"],
                    "signals": persisted["_signals"],
                    "matched_excel": persisted["_matchedExcel"],
                    "agent_trace": persisted.get("_agentTrace"),
                },
            )
            if len(classified_records) % 10 == 0:
                db.commit()
                emit_progress("classifying records")

        # Fire all records concurrently — each is pushed to the store as soon as its LLM call returns
        _gather_results = await asyncio.gather(*[_classify_one(r) for r in to_classify], return_exceptions=True)
        for _res in _gather_results:
            if isinstance(_res, BaseException):
                logger.error("Classification task raised an unhandled exception: %s", _res, exc_info=_res)
        emit_progress("classifying records")

        if source_type == "Excel":
            self._refresh_docx_matches(db)

        elapsed = time.time() - start
        manifest = RunManifest(
            run_id=run_id,
            source_type=source_type,
            source_file_name=filename,
            records_processed=processed,
            records_classified=len(classified_records),
            records_quarantined=quarantined,
            records_escalated=escalated,
            records_failed=len(validation_errors),
            matched_excel=sum(int(record.get("_matchedExcel", 0)) for record in classified_records),
            elapsed_seconds=round(elapsed, 3),
            agent_timings={
                "extraction": round(extraction_elapsed, 3),
                "validation": round(max(0.0, elapsed - extraction_elapsed), 3),
            },
            errors=validation_errors,
        )
        db.add(
            BatchRun(
                run_id=run_id,
                source_type=source_type,
                source_file_name=filename,
                status="completed",
                records_processed=manifest.records_processed,
                records_classified=manifest.records_classified,
                records_quarantined=manifest.records_quarantined,
                records_escalated=manifest.records_escalated,
                records_failed=manifest.records_failed,
                matched_excel=manifest.matched_excel,
                elapsed_seconds=manifest.elapsed_seconds,
                manifest_json=manifest.model_dump() if hasattr(manifest, "model_dump") else manifest.dict(),
            )
        )
        db.commit()
        emit_progress("completed")
        return OrchestrationResult(
            run_id=run_id,
            source_type=source_type,
            source_file_name=filename,
            records=classified_records,
            manifest=manifest,
            trace=classified_records[0].get("_agentTrace") if classified_records else {},
        )

    def _persist_record(self, db: Session, run_id: str, source_file_name: str, record: Dict[str, Any]) -> Dict[str, Any]:
        record_uid = uuid4().hex
        normalized_at = record.get("_normalizedAt")
        normalized_dt = None
        if isinstance(normalized_at, str) and normalized_at:
            try:
                normalized_dt = datetime.fromisoformat(normalized_at.replace("Z", "+00:00"))
            except ValueError:
                normalized_dt = datetime.utcnow()
        elif isinstance(normalized_at, datetime):
            normalized_dt = normalized_at
        else:
            normalized_dt = datetime.utcnow()

        activity = ActivityRecord(
            record_uid=record_uid,
            run_id=run_id,
            source_type=record.get("_source", "Unknown"),
            source_file_name=source_file_name,
            source_record_id=record.get("_sourceRecordId"),
            source_key=record.get("_key"),
            payload_json=record,
            classification=record.get("_classification", "Review"),
            confidence=int(record.get("_confidence", 0)),
            evidence=record.get("_evidence", ""),
            review_reason=record.get("_reviewReason", ""),
            rule_version=record.get("_ruleVersion", self.settings.rule_version),
            persona=record.get("_persona", self.settings.persona_name),
            normalized_at=normalized_dt,
            override=record.get("_override"),
            override_note=record.get("_overrideNote"),
            extraction_confidence=record.get("_extractionConfidence"),
            matched_excel=int(record.get("_matchedExcel", 0))
        )
        db.add(activity)
        record["_recordUid"] = record_uid
        return record

    def _excel_key_set(self, db: Session) -> set[str]:
        rows = db.query(ActivityRecord.source_key).filter(ActivityRecord.source_type == "Excel").all()
        return {row[0] for row in rows if row and row[0]}

    def _refresh_docx_matches(self, db: Session) -> None:
        excel_keys = self._excel_key_set(db)
        if not excel_keys:
            return
        rows = db.query(ActivityRecord).filter(ActivityRecord.source_type == "DOCX form").all()
        for row in rows:
            matched = int(bool(row.source_key and row.source_key in excel_keys))
            row.matched_excel = matched
            payload = dict(row.payload_json or {})
            payload["_matchedExcel"] = matched
            row.payload_json = payload
            db.add(row)
