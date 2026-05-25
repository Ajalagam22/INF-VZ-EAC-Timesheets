from __future__ import annotations

from sqlalchemy import Column, DateTime, Float, Integer, JSON, String, Text, func
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class BatchRun(Base):
    __tablename__ = "batch_runs"

    id = Column(Integer, primary_key=True)
    run_id = Column(String(64), unique=True, nullable=False, index=True)
    source_type = Column(String(32), nullable=False)
    source_file_name = Column(String(255), nullable=False)
    status = Column(String(32), nullable=False, default="completed")
    records_processed = Column(Integer, nullable=False, default=0)
    records_classified = Column(Integer, nullable=False, default=0)
    records_quarantined = Column(Integer, nullable=False, default=0)
    records_escalated = Column(Integer, nullable=False, default=0)
    records_failed = Column(Integer, nullable=False, default=0)
    matched_excel = Column(Integer, nullable=False, default=0)
    elapsed_seconds = Column(Float, nullable=False, default=0.0)
    manifest_json = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ActivityRecord(Base):
    __tablename__ = "activity_records"

    id = Column(Integer, primary_key=True)
    record_uid = Column(String(128), unique=True, nullable=False, index=True)
    run_id = Column(String(64), nullable=False, index=True)
    source_type = Column(String(32), nullable=False)
    source_file_name = Column(String(255), nullable=False)
    source_record_id = Column(String(128), nullable=True, index=True)
    source_key = Column(String(128), nullable=True, index=True)
    payload_json = Column(JSON, nullable=False, default=dict)
    classification = Column(String(16), nullable=False)
    confidence = Column(Integer, nullable=False)
    evidence = Column(Text, nullable=False, default="")
    review_reason = Column(Text, nullable=False, default="")
    rule_version = Column(String(64), nullable=False)
    persona = Column(String(128), nullable=False)
    normalized_at = Column(DateTime(timezone=True), nullable=False)
    override = Column(String(16), nullable=True)
    override_note = Column(Text, nullable=True)
    extraction_confidence = Column(Float, nullable=True)
    matched_excel = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True)
    run_id = Column(String(64), nullable=False, index=True)
    record_uid = Column(String(128), nullable=True, index=True)
    event_type = Column(String(64), nullable=False)
    payload_json = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

