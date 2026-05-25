from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class DataQuality(BaseModel):
    completenessScore: float = Field(default=1.0)
    missingFields: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class RowQuality(BaseModel):
    status: str = Field(default="clean")
    issues: List[str] = Field(default_factory=list)
    repairedFields: List[str] = Field(default_factory=list)
    quarantinedFields: List[str] = Field(default_factory=list)
    corrections: List[Dict[str, Any]] = Field(default_factory=list)


class NormalizedActivityRecord(BaseModel):
    employee_id: Optional[str] = None
    full_name: Optional[str] = None
    job_title: Optional[str] = None
    job_family: Optional[str] = None
    team_name: Optional[str] = None
    org_unit: Optional[str] = None
    manager_id: Optional[str] = None
    week_start_date: Optional[str] = None
    week_end_date: Optional[str] = None
    standard_days: int = 0
    holiday_days: int = 0
    pto_days: int = 0
    sick_days: int = 0
    actual_working_days: int = 0
    meeting_count: int = 0
    ticket_count: int = 0
    email_volume: Optional[str] = None
    code_commit_count: int = 0
    system_activity_score: int = 0
    project_code: Optional[str] = None
    project_name: Optional[str] = None
    activity_type: Optional[str] = None
    hours_allocated: float = 0.0
    submission_notes: Optional[str] = None
    key: str = Field(default="", alias="_key")
    source: str = Field(default="", alias="_source")
    source_file_name: str = Field(default="", alias="_sourceFileName")
    source_record_id: Optional[str] = Field(default=None, alias="_sourceRecordId")
    rule_version: str = Field(default="", alias="_ruleVersion")
    persona: str = Field(default="", alias="_persona")
    normalized_at: str = Field(default="", alias="_normalizedAt")
    extraction_confidence: float = Field(default=0.0, alias="_extractionConfidence")
    raw_fields: Dict[str, Any] = Field(default_factory=dict, alias="_rawFields")
    normalized_fields: Dict[str, Any] = Field(default_factory=dict, alias="_normalizedFields")
    data_quality: DataQuality = Field(default_factory=DataQuality, alias="_dataQuality")
    row_quality: RowQuality = Field(default_factory=RowQuality, alias="_rowQuality")
    form_validation: Dict[str, Any] = Field(default_factory=dict, alias="_formValidation")
    matched_excel: int = Field(default=0, alias="_matchedExcel")

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        validate_by_name=True,
    )
