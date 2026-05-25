from __future__ import annotations

import logging
import time
from pathlib import Path

from app.database.session import session_scope
from app.services.classification_service import ClassificationService
from app.services.ingestion_job_service import IngestionJobService

logger = logging.getLogger(__name__)


def _configure_logging() -> None:
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        )
    else:
        root.setLevel(logging.INFO)


def _process_job(job_id: str) -> None:
    service = ClassificationService()
    with session_scope() as db:
        job = IngestionJobService.get_job(db, job_id)
        job.status = "processing"
        job.stage = "loading staged payload"
        db.add(job)

    payload_path = Path(job.payload_path)
    payload = payload_path.read_bytes()

    def _progress(update: dict) -> None:
        try:
            with session_scope() as db:
                IngestionJobService.update_progress(db, job_id, update)
        except Exception:
            pass

    try:
        result = (
            service.ingest_excel_bytes(payload, job.source_file_name, progress_callback=_progress)
            if job.source_type == "Excel"
            else service.ingest_docx_bytes(payload, job.source_file_name, progress_callback=_progress)
        )
        with session_scope() as db:
            IngestionJobService.complete_job(
                db,
                job_id,
                {
                    "run_id": result.run_id,
                    "processed": result.manifest.records_processed,
                    "classified": result.manifest.records_classified,
                    "quarantined": result.manifest.records_quarantined,
                    "escalated": result.manifest.records_escalated,
                    "failed": result.manifest.records_failed,
                    "matched_excel": result.manifest.matched_excel,
                    "elapsed_seconds": result.manifest.elapsed_seconds,
                    "manifest": result.manifest.model_dump() if hasattr(result.manifest, "model_dump") else result.manifest.dict(),
                },
            )
    except Exception as exc:
        logger.exception("Ingestion job %s failed", job_id)
        with session_scope() as db:
            IngestionJobService.fail_job(db, job_id, str(exc))
    finally:
        try:
            payload_path.unlink(missing_ok=True)
        except Exception:
            logger.warning("Failed to remove staged payload for job %s", job_id, exc_info=True)


def run_worker(poll_seconds: int = 2) -> None:
    logger.info("Ingestion worker starting with poll interval=%ss", poll_seconds)
    empty_polls = 0
    while True:
        with session_scope() as db:
            job = IngestionJobService.claim_next_job(db)
        if not job:
            empty_polls += 1
            if empty_polls == 1 or empty_polls % max(1, int(30 / max(1, poll_seconds))) == 0:
                logger.info("No queued ingestion jobs found; worker is idle.")
            time.sleep(poll_seconds)
            continue
        empty_polls = 0
        logger.info("Processing ingestion job %s (%s)", job.job_id, job.source_file_name)
        try:
            _process_job(job.job_id)
        except Exception:
            logger.exception("Unhandled worker error while processing job %s", job.job_id)


def main() -> None:
    from app.config.settings import get_settings
    from app.database.session import init_db

    _configure_logging()
    settings = get_settings()
    init_db()
    run_worker(poll_seconds=settings.ingestion_job_poll_seconds)


if __name__ == "__main__":
    main()
