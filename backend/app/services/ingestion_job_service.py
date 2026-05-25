from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import logging

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.models.ingestion_job import IngestionJob
from app.schemas.activity_schema import IngestionJobStatusResponse, IngestionJobSubmissionResponse


logger = logging.getLogger(__name__)


class IngestionJobService:
    @staticmethod
    def _settings():
        return get_settings()

    @staticmethod
    def _staging_dir() -> Path:
        settings = IngestionJobService._settings()
        staging_dir = Path(settings.ingestion_staging_dir)
        staging_dir.mkdir(parents=True, exist_ok=True)
        return staging_dir

    @staticmethod
    def _stage_payload(job_id: str, source_file_name: str, payload: bytes) -> str:
        suffix = Path(source_file_name).suffix or ".bin"
        path = IngestionJobService._staging_dir() / f"{job_id}{suffix}"
        path.write_bytes(payload)
        return str(path)

    @staticmethod
    def enqueue_job(
        db: Session,
        *,
        source_type: str,
        source_file_name: str,
        payload: bytes,
    ) -> IngestionJob:
        job_id = uuid4().hex
        payload_path = IngestionJobService._stage_payload(job_id, source_file_name, payload)
        job = IngestionJob(
            job_id=job_id,
            source_type=source_type,
            source_file_name=source_file_name,
            payload_path=payload_path,
            status="queued",
            stage="queued for processing",
            created_at=datetime.now(timezone.utc),
        )
        db.add(job)
        try:
            db.commit()
            db.refresh(job)
            logger.info(
                "Queued ingestion job %s for %s (%s)",
                job.job_id,
                job.source_type,
                job.source_file_name,
            )
        except Exception:
            try:
                Path(payload_path).unlink(missing_ok=True)
            except Exception:
                pass
            raise
        return job

    @staticmethod
    def get_job(db: Session, job_id: str) -> IngestionJob:
        job = db.query(IngestionJob).filter(IngestionJob.job_id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Ingestion job not found")
        return job

    @staticmethod
    def claim_next_job(db: Session) -> IngestionJob | None:
        job = (
            db.query(IngestionJob)
            .filter(IngestionJob.status == "queued")
            .order_by(IngestionJob.created_at.asc())
            .first()
        )
        if not job:
            return None
        job.status = "processing"
        job.stage = "loading staged payload"
        job.started_at = datetime.now(timezone.utc)
        job.attempts += 1
        db.add(job)
        db.commit()
        db.refresh(job)
        logger.info(
            "Claimed ingestion job %s for %s (%s)",
            job.job_id,
            job.source_type,
            job.source_file_name,
        )
        return job

    @staticmethod
    def update_progress(db: Session, job_id: str, progress: dict) -> None:
        job = db.query(IngestionJob).filter(IngestionJob.job_id == job_id).first()
        if not job:
            return
        job.stage = str(progress.get("stage") or job.stage)
        job.processed = int(progress.get("processed", job.processed))
        job.classified = int(progress.get("classified", job.classified))
        job.quarantined = int(progress.get("quarantined", job.quarantined))
        job.escalated = int(progress.get("escalated", job.escalated))
        job.failed = int(progress.get("failed", job.failed))
        job.matched_excel = int(progress.get("matched_excel", job.matched_excel))
        if progress.get("run_id") and not job.run_id:
            job.run_id = progress["run_id"]
        db.add(job)
        db.commit()

    @staticmethod
    def complete_job(db: Session, job_id: str, result: dict) -> None:
        job = db.query(IngestionJob).filter(IngestionJob.job_id == job_id).first()
        if not job:
            return
        job.status = "completed"
        job.stage = "completed"
        job.run_id = result.get("run_id")
        job.processed = int(result.get("processed", job.processed))
        job.classified = int(result.get("classified", job.classified))
        job.quarantined = int(result.get("quarantined", job.quarantined))
        job.escalated = int(result.get("escalated", job.escalated))
        job.failed = int(result.get("failed", job.failed))
        job.matched_excel = int(result.get("matched_excel", job.matched_excel))
        job.elapsed_seconds = float(result.get("elapsed_seconds", job.elapsed_seconds))
        job.manifest_json = result.get("manifest") or {}
        job.error = None
        job.completed_at = datetime.now(timezone.utc)
        db.add(job)
        db.commit()
        logger.info(
            "Completed ingestion job %s run_id=%s processed=%s classified=%s escalated=%s",
            job.job_id,
            job.run_id,
            job.processed,
            job.classified,
            job.escalated,
        )

    @staticmethod
    def fail_job(db: Session, job_id: str, error: str) -> None:
        job = db.query(IngestionJob).filter(IngestionJob.job_id == job_id).first()
        if not job:
            return
        job.status = "failed"
        job.stage = "failed"
        job.error = error
        job.completed_at = datetime.now(timezone.utc)
        db.add(job)
        db.commit()
        logger.error("Failed ingestion job %s: %s", job.job_id, error)

    @staticmethod
    def remove_payload(job: IngestionJob) -> None:
        try:
            Path(job.payload_path).unlink(missing_ok=True)
        except Exception:
            pass

    @staticmethod
    def submission_response(job: IngestionJob) -> IngestionJobSubmissionResponse:
        return IngestionJobSubmissionResponse(
            job_id=job.job_id,
            status=job.status,  # type: ignore[arg-type]
            status_url=f"/api/upload/jobs/{job.job_id}",
            source_type=job.source_type,
            source_file_name=job.source_file_name,
            created_at=job.created_at,
            stage=job.stage,
        )

    @staticmethod
    def status_response(db: Session, job: IngestionJob) -> IngestionJobStatusResponse:
        from app.services.classification_service import ClassificationService

        result = None
        manifest = None
        if job.status == "completed" and job.run_id:
            result = ClassificationService().run_result(db, job.run_id)
            if result:
                manifest = result.manifest
            elif job.manifest_json:
                from app.schemas.activity_schema import RunManifest

                manifest = RunManifest.model_validate(job.manifest_json)

        return IngestionJobStatusResponse(
            job_id=job.job_id,
            status=job.status,  # type: ignore[arg-type]
            source_type=job.source_type,
            source_file_name=job.source_file_name,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            stage=job.stage,
            attempts=job.attempts,
            processed=job.processed,
            classified=job.classified,
            quarantined=job.quarantined,
            escalated=job.escalated,
            failed=job.failed,
            matched_excel=job.matched_excel,
            elapsed_seconds=job.elapsed_seconds,
            run_id=job.run_id,
            manifest=manifest,
            result=result,
            error=job.error,
        )
