from __future__ import annotations

import threading

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.activity_schema import IngestionJobStatusResponse, IngestionJobSubmissionResponse
from app.services.ingestion_job_service import IngestionJobService
from app.workers.ingestion_worker import _process_job

router = APIRouter()


@router.post("/excel", response_model=IngestionJobSubmissionResponse, status_code=202)
def upload_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> IngestionJobSubmissionResponse:
    payload = file.file.read()
    job = IngestionJobService.enqueue_job(
        db,
        source_type="Excel",
        source_file_name=file.filename or "EAC_Dataset.xlsx",
        payload=payload,
    )
    db.close()
    threading.Thread(target=_process_job, args=(job.job_id,), daemon=True).start()
    return IngestionJobService.submission_response(job)


@router.post("/forms", response_model=IngestionJobSubmissionResponse, status_code=202)
def upload_forms(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> IngestionJobSubmissionResponse:
    filename = file.filename or "sample_forms.zip"
    lowered = filename.lower()
    if not (lowered.endswith(".docx") or lowered.endswith(".zip")):
        raise HTTPException(status_code=400, detail="Upload a single .docx file or a .zip containing DOCX files.")
    payload = file.file.read()
    job = IngestionJobService.enqueue_job(
        db,
        source_type="DOCX form",
        source_file_name=filename,
        payload=payload,
    )
    db.close()
    threading.Thread(target=_process_job, args=(job.job_id,), daemon=True).start()
    return IngestionJobService.submission_response(job)


@router.get("/jobs/{job_id}", response_model=IngestionJobStatusResponse)
def ingestion_job_status(job_id: str, db: Session = Depends(get_db)) -> IngestionJobStatusResponse:
    job = IngestionJobService.get_job(db, job_id)
    return IngestionJobService.status_response(db, job)
