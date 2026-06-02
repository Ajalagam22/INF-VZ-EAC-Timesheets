from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.activity_record import ActivityRecord, AuditEvent, BatchRun
from app.models.ingestion_job import IngestionJob
from app.schemas.activity_schema import APIMessage, DraftSubmitRequest, OverrideRequest, RecordUpdateRequest
from app.services.classification_service import ClassificationService
from app.state import progress_store

router = APIRouter()
service = ClassificationService()


@router.get("/records")
def list_records(limit: int = 500, db: Session = Depends(get_db)) -> Dict[str, Any]:
    return {"records": service.list_records(db, limit=limit)}


@router.get("/records/run/{run_id}")
def list_records_by_run(run_id: str, offset: int = 0) -> Dict[str, Any]:
    records = progress_store.get(run_id, offset=offset)
    return {"records": records, "count": len(records)}


@router.get("/runs/latest")
def latest_run(db: Session = Depends(get_db)) -> Dict[str, Any]:
    return {"run": service.latest_run(db)}


@router.get("/summary")
def summary(db: Session = Depends(get_db)) -> Dict[str, Any]:
    return service.summary(db)


@router.get("/drafts")
def weekly_drafts(db: Session = Depends(get_db)) -> Dict[str, Any]:
    return service.weekly_drafts(db)


@router.get("/escalations")
def escalations(db: Session = Depends(get_db)) -> Dict[str, Any]:
    return service.escalations(db)


@router.get("/connectors")
def connector_health(db: Session = Depends(get_db)) -> Dict[str, Any]:
    return service.connector_health(db)


@router.get("/audit/{record_uid}")
def audit_timeline(record_uid: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    return {"events": service.audit_timeline(db, record_uid)}


@router.post("/records/{record_uid}/override")
def override_record(record_uid: str, request: OverrideRequest, db: Session = Depends(get_db)) -> Dict[str, Any]:
    return service.override_record(db, record_uid, request)


@router.patch("/records/{record_uid}")
def update_record(record_uid: str, request: RecordUpdateRequest, db: Session = Depends(get_db)) -> Dict[str, Any]:
    return service.update_record(db, record_uid, request)


@router.post("/drafts/submit")
def submit_draft(request: DraftSubmitRequest, db: Session = Depends(get_db)) -> Dict[str, Any]:
    return service.submit_draft(db, request)

@router.get("/reconciliation")
def reconciliation_report(db: Session = Depends(get_db)) -> Dict[str, Any]:
    return service.reconciliation_report(db)
