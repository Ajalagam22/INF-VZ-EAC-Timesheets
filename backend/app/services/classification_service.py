from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.audit.audit_service import AuditService
from app.database.session import session_scope
from app.models.activity_record import ActivityRecord, AuditEvent, BatchRun
from app.orchestrator.flow_orchestrator import FlowOrchestrator
from app.schemas.activity_schema import DraftSubmitRequest, IngestionResponse, OverrideRequest, RecordUpdateRequest, RunManifest


class ClassificationService:
    def __init__(self) -> None:
        self.orchestrator = FlowOrchestrator()
        self.audit = AuditService()

    def ingest_excel_file(self, upload: UploadFile) -> IngestionResponse:
        return self._ingest(upload, source_type="Excel")

    def ingest_docx_zip(self, upload: UploadFile) -> IngestionResponse:
        return self._ingest(upload, source_type="DOCX form")

    def ingest_excel_bytes(
        self,
        payload: bytes,
        source_file_name: str,
        progress_callback: Any | None = None,
    ) -> IngestionResponse:
        return self._ingest_bytes(
            payload,
            source_type="Excel",
            source_file_name=source_file_name,
            progress_callback=progress_callback,
        )

    def ingest_docx_bytes(
        self,
        payload: bytes,
        source_file_name: str,
        progress_callback: Any | None = None,
    ) -> IngestionResponse:
        return self._ingest_bytes(
            payload,
            source_type="DOCX form",
            source_file_name=source_file_name,
            progress_callback=progress_callback,
        )

    def _ingest(self, upload: UploadFile, source_type: str) -> IngestionResponse:
        payload = upload.file.read()
        default_name = "Test data May 22.xlsx" if source_type == "Excel" else "sample_timesheets.zip"
        source_file_name = upload.filename or default_name
        return self._ingest_bytes(payload, source_type=source_type, source_file_name=source_file_name)

    def _ingest_bytes(
        self,
        payload: bytes,
        source_type: str,
        source_file_name: str,
        progress_callback: Any | None = None,
    ) -> IngestionResponse:
        with session_scope() as db:
            result = (
                self.orchestrator.run_excel(
                    db,
                    payload,
                    source_file_name,
                    progress_callback=progress_callback,
                )
                if source_type == "Excel"
                else self.orchestrator.run_docx_zip(
                    db,
                    payload,
                    source_file_name,
                    progress_callback=progress_callback,
                )
            )
            manifest = result.manifest or RunManifest(
                run_id=result.run_id,
                source_type=result.source_type,
                source_file_name=result.source_file_name
            )
            return IngestionResponse(
                run_id=result.run_id,
                source_type=result.source_type,
                source_file_name=result.source_file_name,
                processed=manifest.records_processed,
                classified=manifest.records_classified,
                quarantined=manifest.records_quarantined,
                escalated=manifest.records_escalated,
                failed=manifest.records_failed,
                matched_excel=manifest.matched_excel,
                elapsed_seconds=manifest.elapsed_seconds,
                records=result.records,
                manifest=manifest,
                agent_trace=[result.trace] if result.trace else []
            )

    def run_result(self, db: Session, run_id: str) -> Optional[IngestionResponse]:
        row = db.query(BatchRun).filter(BatchRun.run_id == run_id).first()
        if not row:
            return None
        records = [
            self._serialize_record(record)
            for record in db.query(ActivityRecord)
            .filter(ActivityRecord.run_id == run_id)
            .order_by(ActivityRecord.created_at.asc())
            .all()
        ]
        manifest_data = dict(row.manifest_json or {})
        if manifest_data:
            manifest = RunManifest.model_validate(manifest_data)
        else:
            manifest = RunManifest(
                run_id=row.run_id,
                source_type=row.source_type,
                source_file_name=row.source_file_name,
                records_processed=row.records_processed,
                records_classified=row.records_classified,
                records_quarantined=getattr(row, "records_quarantined", 0) or 0,
                records_escalated=row.records_escalated,
                records_failed=row.records_failed,
                matched_excel=row.matched_excel,
                elapsed_seconds=row.elapsed_seconds,
                agent_timings={},
                errors=[]
            )
        return IngestionResponse(
            run_id=row.run_id,
            source_type=row.source_type,
            source_file_name=row.source_file_name,
            processed=row.records_processed,
            classified=row.records_classified,
            quarantined=getattr(row, "records_quarantined", 0) or 0,
            escalated=row.records_escalated,
            failed=row.records_failed,
            matched_excel=row.matched_excel,
            elapsed_seconds=row.elapsed_seconds,
            records=records,
            manifest=manifest,
            agent_trace=[records[0].get("_agentTrace")] if records and records[0].get("_agentTrace") else [],
        )

    def list_records(self, db: Session, limit: int = 500) -> List[Dict[str, Any]]:
        # Return records from the most recent batch run per source type
        # so repeated uploads don't accumulate duplicates in the UI
        latest_runs: Dict[str, str] = {}
        for batch in (
            db.query(BatchRun)
            .order_by(BatchRun.created_at.desc())
            .all()
        ):
            if batch.source_type not in latest_runs:
                latest_runs[batch.source_type] = batch.run_id

        if latest_runs:
            rows = (
                db.query(ActivityRecord)
                .filter(ActivityRecord.run_id.in_(latest_runs.values()))
                .order_by(ActivityRecord.created_at.desc())
                .limit(limit)
                .all()
            )
        else:
            rows = (
                db.query(ActivityRecord)
                .order_by(ActivityRecord.created_at.desc())
                .limit(limit)
                .all()
            )
        return [self._serialize_record(row) for row in rows]

    def latest_run(self, db: Session) -> Optional[Dict[str, Any]]:
        row = db.query(BatchRun).order_by(BatchRun.created_at.desc()).first()
        if not row:
            return None
        result = self.run_result(db, row.run_id)
        return result.model_dump() if result else {
            "run_id": row.run_id,
            "source_type": row.source_type,
            "source_file_name": row.source_file_name,
            "records_processed": row.records_processed,
            "records_classified": row.records_classified,
            "records_escalated": row.records_escalated,
            "records_failed": row.records_failed,
            "matched_excel": row.matched_excel,
            "elapsed_seconds": row.elapsed_seconds,
            "manifest": row.manifest_json
        }

    def override_record(self, db: Session, record_uid: str, request: OverrideRequest) -> Dict[str, Any]:
        row = db.query(ActivityRecord).filter(ActivityRecord.record_uid == record_uid).first()
        if not row:
            raise HTTPException(status_code=404, detail="Record not found")
        if request.classification is None:
            row.override = None
            row.override_note = None
        else:
            row.override = request.classification
            row.override_note = request.note
        db.add(row)
        self.audit.record_event(
            db,
            run_id=row.run_id,
            record_uid=row.record_uid,
            event_type="override",
            payload={"classification": row.override, "note": row.override_note}
        )
        db.commit()
        db.refresh(row)
        return self._serialize_record(row)

    def update_record(self, db: Session, record_uid: str, request: RecordUpdateRequest) -> Dict[str, Any]:
        row = db.query(ActivityRecord).filter(ActivityRecord.record_uid == record_uid).first()
        if not row:
            raise HTTPException(status_code=404, detail="Record not found")

        payload = dict(row.payload_json or {})
        changes: Dict[str, Any] = {}
        fields_set = getattr(request, "model_fields_set", set())

        if "classification" in fields_set:
            row.override = request.classification
            row.override_note = request.note if request.classification else None
            changes["classification"] = request.classification
        if "project_code" in fields_set and request.project_code is not None:
            previous = payload.get("project_code")
            payload["project_code"] = request.project_code
            changes["project_code"] = {"from": previous, "to": request.project_code}
        attendance_changed = False
        for field in ("holiday_days", "pto_days", "sick_days"):
            if field in fields_set and getattr(request, field) is not None:
                previous = payload.get(field)
                value = getattr(request, field)
                payload[field] = value
                changes[field] = {"from": previous, "to": value}
                attendance_changed = True
        if attendance_changed:
            standard_days = float(payload.get("standard_days") or 0)
            if standard_days:
                previous = payload.get("actual_working_days")
                actual_working_days = max(
                    0,
                    standard_days
                    - float(payload.get("holiday_days") or 0)
                    - float(payload.get("pto_days") or 0)
                    - float(payload.get("sick_days") or 0),
                )
                payload["actual_working_days"] = actual_working_days
                changes["actual_working_days"] = {"from": previous, "to": actual_working_days}
        if "submission_notes" in fields_set and request.submission_notes is not None:
            previous = payload.get("submission_notes")
            payload["submission_notes"] = request.submission_notes
            changes["submission_notes"] = {"from": previous, "to": request.submission_notes}

        row.payload_json = payload
        db.add(row)
        self.audit.record_event(
            db,
            run_id=row.run_id,
            record_uid=row.record_uid,
            event_type="employee_review_update",
            payload={"changes": changes, "note": request.note}
        )
        db.commit()
        db.refresh(row)
        return self._serialize_record(row)

    def submit_draft(self, db: Session, request: DraftSubmitRequest) -> Dict[str, Any]:
        rows = (
            db.query(ActivityRecord)
            .filter(ActivityRecord.record_uid.in_(request.record_uids))
            .all()
            if request.record_uids
            else []
        )
        for row in rows:
            self.audit.record_event(
                db,
                run_id=row.run_id,
                record_uid=row.record_uid,
                event_type="employee_review_submit",
                payload={"note": request.note, "final_classification": self._effective_classification(row)}
            )
        db.commit()
        return {"submitted": len(rows), "record_uids": [row.record_uid for row in rows]}

    def audit_timeline(self, db: Session, record_uid: str) -> List[Dict[str, Any]]:
        return self.audit.timeline(db, record_uid)

    def summary(self, db: Session) -> Dict[str, Any]:
        records = self._latest_rows(db)
        reporting_records = self._reporting_rows(records)
        total = len(reporting_records)
        capex = sum(1 for row in reporting_records if self._effective_classification(row) == "CapEx")
        opex = sum(1 for row in reporting_records if self._effective_classification(row) == "OpEx")
        review = sum(1 for row in reporting_records if self._effective_classification(row) == "Review")
        overrides = sum(1 for row in reporting_records if row.override)
        total_hours = sum(self._hours(row) for row in reporting_records)
        capex_hours = sum(self._hours(row) for row in reporting_records if self._effective_classification(row) == "CapEx")
        opex_hours = sum(self._hours(row) for row in reporting_records if self._effective_classification(row) == "OpEx")
        review_hours = sum(self._hours(row) for row in reporting_records if self._effective_classification(row) == "Review")
        docs = [row for row in records if row.source_type == "DOCX form"]
        matched_docs = sum(1 for row in docs if row.matched_excel)
        return {
            "total": total,
            "capex": capex,
            "opex": opex,
            "review": review,
            "overrides": overrides,
            "total_hours": round(total_hours, 2),
            "capex_hours": round(capex_hours, 2),
            "opex_hours": round(opex_hours, 2),
            "review_hours": round(review_hours, 2),
            "capitalisation_pct": round((capex_hours / total_hours) * 100, 1) if total_hours else 0,
            "baseline_capex_pct": 0,
            "shift_delta_hours": round(capex_hours, 2),
            "estimated_recovery_usd": round(capex_hours * 125, 2),
            "docx_records": len(docs),
            "docx_matched_excel": matched_docs,
            "docx_match_pct": round((matched_docs / len(docs)) * 100, 1) if docs else 0,
        }

    def weekly_drafts(self, db: Session) -> Dict[str, Any]:
        rows = [
            row for row in self._reporting_rows(self._latest_rows(db))
            if self._effective_classification(row) in {"CapEx", "OpEx"} and (row.confidence >= 70 or row.override)
        ]
        drafts: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            payload = dict(row.payload_json or {})
            key = f"{payload.get('employee_id')}::{payload.get('week_start_date')}"
            draft = drafts.setdefault(
                key,
                {
                    "employee_id": payload.get("employee_id"),
                    "employee_name": payload.get("full_name"),
                    "job_title": payload.get("job_title"),
                    "job_family": payload.get("job_family"),
                    "team_name": payload.get("team_name"),
                    "manager_id": payload.get("manager_id"),
                    "week_start": payload.get("week_start_date"),
                    "week_end": payload.get("week_end_date"),
                    "holiday_days": float(payload.get("holiday_days") or 0),
                    "pto_days": float(payload.get("pto_days") or 0),
                    "sick_days": float(payload.get("sick_days") or 0),
                    "actual_working_days": float(payload.get("actual_working_days") or 0),
                    "total_hours": 0.0,
                    "capex_hours": 0.0,
                    "opex_hours": 0.0,
                    "capitalisation_pct": 0.0,
                    "baseline_capex_pct": 0,
                    "line_items": [],
                },
            )
            hours = self._hours(row)
            classification = self._effective_classification(row)
            for field in ("holiday_days", "pto_days", "sick_days", "actual_working_days"):
                draft[field] = max(float(draft.get(field) or 0), float(payload.get(field) or 0))
            draft["total_hours"] += hours
            if classification == "CapEx":
                draft["capex_hours"] += hours
            else:
                draft["opex_hours"] += hours
            draft["line_items"].append(self._line_item(row))
        for draft in drafts.values():
            total_hours = draft["total_hours"]
            draft["capitalisation_pct"] = round((draft["capex_hours"] / total_hours) * 100, 1) if total_hours else 0
            draft["shift_delta"] = round(draft["capex_hours"], 2)
            draft["estimated_recovery_usd"] = round(draft["capex_hours"] * 125, 2)
            for field in ("total_hours", "capex_hours", "opex_hours"):
                draft[field] = round(draft[field], 2)
        return {"drafts": sorted(drafts.values(), key=lambda item: (item["week_start"] or "", item["employee_name"] or ""))}

    def escalations(self, db: Session) -> Dict[str, Any]:
        rows = [
            row for row in self._reporting_rows(self._latest_rows(db))
            if self._effective_classification(row) == "Review" or (not row.override and row.confidence < 70)
        ]
        by_manager: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            payload = dict(row.payload_json or {})
            manager_id = str(payload.get("manager_id") or "Unassigned")
            bucket = by_manager.setdefault(manager_id, {"manager_id": manager_id, "records": [], "hours": 0.0})
            bucket["records"].append(self._serialize_record(row))
            bucket["hours"] += self._hours(row)
        for bucket in by_manager.values():
            bucket["hours"] = round(bucket["hours"], 2)
        return {"escalations": sorted(by_manager.values(), key=lambda item: item["manager_id"])}

    def connector_health(self, db: Session) -> Dict[str, Any]:
        runs = db.query(BatchRun).order_by(BatchRun.created_at.desc()).all()
        latest: Dict[str, BatchRun] = {}
        for run in runs:
            latest.setdefault(run.source_type, run)
        return {
            "connectors": [
                {
                    "source_type": source_type,
                    "source_file_name": run.source_file_name,
                    "records_processed": run.records_processed,
                    "records_classified": run.records_classified,
                    "records_failed": run.records_failed,
                    "records_escalated": run.records_escalated,
                    "matched_excel": run.matched_excel,
                    "elapsed_seconds": run.elapsed_seconds,
                    "created_at": run.created_at.isoformat() if run.created_at else None,
                }
                for source_type, run in latest.items()
            ]
        }


    def reconciliation_report(self, db: Session) -> Dict[str, Any]:
        rows = self._reporting_rows(self._latest_rows(db))

        cost_centers: Dict[str, Dict[str, Any]] = {}
        all_employees: set = set()

        for row in rows:
            payload = dict(row.payload_json or {})
            cost_center = payload.get("org_unit") or payload.get("team_name") or "Unassigned"
            employee_id = str(payload.get("employee_id") or "Unknown")
            classification = self._effective_classification(row)
            hours = self._hours(row)
            confidence = int(row.confidence or 0)
            routing = payload.get("_routingState") or (
                "approved" if classification != "Review" and confidence >= 70 else "review"
            )

            all_employees.add(employee_id)

            cc = cost_centers.setdefault(
                cost_center,
                {
                    "cost_center": cost_center,
                    "employee_ids": set(),
                    "total_hours": 0.0,
                    "capex_hours": 0.0,
                    "opex_hours": 0.0,
                    "review_hours": 0.0,
                    "completed_records": 0,
                    "outstanding_records": 0,
                    "flagged_employees": set(),
                    "employees": {},
                },
            )

            cc["employee_ids"].add(employee_id)
            cc["total_hours"] += hours
            if classification == "CapEx":
                cc["capex_hours"] += hours
            elif classification == "OpEx":
                cc["opex_hours"] += hours
            else:
                cc["review_hours"] += hours

            if routing == "approved":
                cc["completed_records"] += 1
            else:
                cc["outstanding_records"] += 1
                cc["flagged_employees"].add(employee_id)

            emp = cc["employees"].setdefault(
                employee_id,
                {
                    "employee_id": employee_id,
                    "full_name": payload.get("full_name") or employee_id,
                    "job_title": payload.get("job_title") or "",
                    "total_hours": 0.0,
                    "capex_hours": 0.0,
                    "opex_hours": 0.0,
                    "review_hours": 0.0,
                    "record_count": 0,
                    "flagged": False,
                },
            )
            emp["total_hours"] += hours
            if classification == "CapEx":
                emp["capex_hours"] += hours
            elif classification == "OpEx":
                emp["opex_hours"] += hours
            else:
                emp["review_hours"] += hours
            emp["record_count"] += 1
            if routing != "approved":
                emp["flagged"] = True

        result_cost_centers = []
        total_capex_hours = 0.0
        total_hours_all = 0.0

        for cc in cost_centers.values():
            total_hours = cc["total_hours"]
            capex_hours = round(cc["capex_hours"], 2)
            opex_hours = round(cc["opex_hours"], 2)
            capex_pct = round((capex_hours / total_hours) * 100, 1) if total_hours else 0.0
            total_capex_hours += capex_hours
            total_hours_all += total_hours

            employees_serialized = sorted(
                [
                    {
                        "employee_id": emp["employee_id"],
                        "full_name": emp["full_name"],
                        "job_title": emp["job_title"],
                        "total_hours": round(emp["total_hours"], 2),
                        "capex_hours": round(emp["capex_hours"], 2),
                        "opex_hours": round(emp["opex_hours"], 2),
                        "capex_pct": round((emp["capex_hours"] / emp["total_hours"]) * 100, 1) if emp["total_hours"] else 0.0,
                        "delta_hours": round(emp["capex_hours"], 2),
                        "review_hours": round(emp["review_hours"], 2),
                        "record_count": emp["record_count"],
                        "flagged": emp["flagged"],
                    }
                    for emp in cc["employees"].values()
                ],
                key=lambda e: e["total_hours"],
                reverse=True,
            )

            result_cost_centers.append(
                {
                    "cost_center": cc["cost_center"],
                    "employee_count": len(cc["employee_ids"]),
                    "completed_records": cc["completed_records"],
                    "outstanding_records": cc["outstanding_records"],
                    "total_hours": round(total_hours, 2),
                    "capex_hours": capex_hours,
                    "opex_hours": opex_hours,
                    "review_hours": round(cc["review_hours"], 2),
                    "baseline_opex_hours": round(total_hours, 2),
                    "capitalisation_delta_hours": round(capex_hours, 2),
                    "capitalisation_pct": capex_pct,
                    "flagged_employee_count": len(cc["flagged_employees"]),
                    "employees": employees_serialized,
                }
            )

        result_cost_centers.sort(key=lambda c: c["total_hours"], reverse=True)

        return {
            "total_employees_processed": len(all_employees),
            "total_cost_centers": len(result_cost_centers),
            "total_hours": round(total_hours_all, 2),
            "total_capex_hours": round(total_capex_hours, 2),
            "total_capex_pct": round((total_capex_hours / total_hours_all) * 100, 1) if total_hours_all else 0.0,
            "total_baseline_delta_hours": round(total_capex_hours, 2),
            "cost_centers": result_cost_centers,
        }

    def _latest_rows(self, db: Session) -> List[ActivityRecord]:
        latest_runs: Dict[str, str] = {}
        for batch in db.query(BatchRun).order_by(BatchRun.created_at.desc()).all():
            if batch.source_type not in latest_runs:
                latest_runs[batch.source_type] = batch.run_id
        query = db.query(ActivityRecord)
        if latest_runs:
            query = query.filter(ActivityRecord.run_id.in_(latest_runs.values()))
        return query.order_by(ActivityRecord.created_at.desc()).all()

    def _reporting_rows(self, records: List[ActivityRecord]) -> List[ActivityRecord]:
        return [
            row for row in records
            if row.source_type == "Excel" or (row.source_type == "DOCX form" and not row.matched_excel)
        ]

    def _effective_classification(self, row: ActivityRecord) -> str:
        return row.override or row.classification

    def _hours(self, row: ActivityRecord) -> float:
        payload = dict(row.payload_json or {})
        try:
            return float(payload.get("hours_allocated") or 0)
        except (TypeError, ValueError):
            return 0.0

    def _line_item(self, row: ActivityRecord) -> Dict[str, Any]:
        payload = dict(row.payload_json or {})
        return {
            "record_uid": row.record_uid,
            "project_code": payload.get("project_code"),
            "project_name": payload.get("project_name"),
            "activity_type": payload.get("activity_type"),
            "hours": self._hours(row),
            "classification": self._effective_classification(row),
            "confidence": row.confidence,
            "evidence_summary": row.evidence,
            "signals": payload.get("_signals", []),
            "source": row.source_type,
        }

    def _serialize_record(self, row: ActivityRecord) -> Dict[str, Any]:
        payload = dict(row.payload_json or {})
        payload.update(
            {
                "_id": row.record_uid,
                "_recordUid": row.record_uid,
                "_classification": row.classification,
                "_confidence": row.confidence,
                "_evidence": row.evidence,
                "_reviewReason": row.review_reason,
                "_source": row.source_type,
                "_sourceRecordId": row.source_record_id,
                "_ruleVersion": row.rule_version,
                "_persona": row.persona,
                "_normalizedAt": row.normalized_at.isoformat() if row.normalized_at else None,
                "_override": row.override,
                "_overrideNote": row.override_note,
                "_matchedExcel": row.matched_excel,
                "_extractionConfidence": row.extraction_confidence,
                "_sourceFileName": row.source_file_name
            }
        )
        return payload
