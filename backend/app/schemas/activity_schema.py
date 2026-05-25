from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

ClassificationLabel = Literal["CapEx", "OpEx", "Review"]
SignalKind = Literal["capex", "opex", "quality", "policy"]


class Signal(BaseModel):
    label: str
    impact: int
    kind: SignalKind


class OverrideRequest(BaseModel):
    classification: Optional[ClassificationLabel] = Field(
        default=None,
        description="Optional manual override classification"
    )
    note: str = Field(default="Manual reviewer correction")


class RecordUpdateRequest(BaseModel):
    classification: Optional[ClassificationLabel] = None
    project_code: Optional[str] = None
    holiday_days: Optional[float] = None
    pto_days: Optional[float] = None
    sick_days: Optional[float] = None
    submission_notes: Optional[str] = None
    note: str = Field(default="Employee review correction")


class DraftSubmitRequest(BaseModel):
    record_uids: List[str] = Field(default_factory=list)
    note: str = Field(default="Employee submitted weekly draft")


class RunManifest(BaseModel):
    run_id: str
    source_type: str
    source_file_name: str
    records_processed: int = 0
    records_classified: int = 0
    records_quarantined: int = 0
    records_escalated: int = 0
    records_failed: int = 0
    matched_excel: int = 0
    elapsed_seconds: float = 0.0
    agent_timings: Dict[str, float] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)


class APIMessage(BaseModel):
    status: str
    message: str


class IngestionResponse(BaseModel):
    run_id: str
    source_type: str
    source_file_name: str
    processed: int
    classified: int
    quarantined: int = 0
    escalated: int
    failed: int
    matched_excel: int
    elapsed_seconds: float
    records: List[Dict[str, Any]]
    manifest: RunManifest
    agent_trace: List[Dict[str, Any]] = Field(default_factory=list)


class IngestionJobSubmissionResponse(BaseModel):
    job_id: str
    status: Literal["queued", "processing", "completed", "failed"]
    status_url: str
    source_type: str
    source_file_name: str
    created_at: datetime
    stage: str


class IngestionJobStatusResponse(BaseModel):
    job_id: str
    status: Literal["queued", "processing", "completed", "failed"]
    source_type: str
    source_file_name: str
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    stage: str
    attempts: int = 0
    processed: int = 0
    classified: int = 0
    quarantined: int = 0
    escalated: int = 0
    failed: int = 0
    matched_excel: int = 0
    elapsed_seconds: float = 0.0
    run_id: str | None = None
    manifest: RunManifest | None = None
    result: IngestionResponse | None = None
    error: str | None = None


class AuditEventPayload(BaseModel):
    event_type: str
    payload: Dict[str, Any] = Field(default_factory=dict)


class RecordListResponse(BaseModel):
    records: List[Dict[str, Any]]


IngestionJobSubmissionResponse.model_rebuild()
IngestionJobStatusResponse.model_rebuild()
