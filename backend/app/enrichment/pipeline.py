from __future__ import annotations

from datetime import datetime
import re
from typing import Any, Dict, List, Tuple

from app.schemas.normalized_activity import DataQuality, NormalizedActivityRecord

TIMESHEET_FIELDS: Tuple[str, ...] = (
    "employee_id",
    "full_name",
    "job_title",
    "job_family",
    "team_name",
    "org_unit",
    "manager_id",
    "week_start_date",
    "week_end_date",
    "standard_days",
    "holiday_days",
    "pto_days",
    "sick_days",
    "actual_working_days",
    "meeting_count",
    "ticket_count",
    "email_volume",
    "code_commit_count",
    "system_activity_score",
    "project_code",
    "project_name",
    "activity_type",
    "hours_allocated",
    "submission_notes",
)

REQUIRED_FIELDS: Tuple[str, ...] = (
    "employee_id",
    "full_name",
    "job_title",
    "job_family",
    "team_name",
    "org_unit",
    "manager_id",
    "week_start_date",
    "week_end_date",
    "actual_working_days",
    "project_code",
    "project_name",
    "activity_type",
    "hours_allocated",
)


def clean_text(value: Any) -> str:
    return str(value if value is not None else "").replace("\n", " ").replace("\r", " ").strip()


def to_number(value: Any) -> float:
    text = clean_text(value).replace("$", "").replace("%", "").replace(",", "")
    if not text:
        return 0.0
    match = re.search(r"[-+]?\d+(?:\.\d+)?", text)
    if not match:
        return 0.0
    try:
        return float(match.group(0))
    except ValueError:
        return 0.0


def to_int(value: Any) -> int:
    return int(round(to_number(value)))


def parse_date(value: Any) -> str | None:
    if hasattr(value, "date"):
        try:
            return value.date().isoformat()
        except Exception:
            pass
    text = clean_text(value)
    if not text:
        return None
    iso_text = text.replace("Z", "+00:00") if "T" in text else text
    try:
        return datetime.fromisoformat(iso_text).date().isoformat()
    except ValueError:
        pass
    for pattern in (
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%m/%d/%Y",
        "%m/%d/%y",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%y %H:%M:%S",
        "%m/%d/%Y %I:%M:%S %p",
        "%m/%d/%y %I:%M:%S %p",
        "%m/%d/%Y %I:%M %p",
        "%m/%d/%y %I:%M %p",
        "%A, %B %d, %Y",
        "%A, %B %d, %Y %H:%M:%S",
        "%B %d, %Y",
        "%B %d, %Y %H:%M:%S",
        "%b %d, %Y",
        "%b %d, %Y %H:%M:%S",
    ):
        try:
            return datetime.strptime(text, pattern).date().isoformat()
        except ValueError:
            continue
    return text


def canonical_key(record: Dict[str, Any]) -> str:
    parts = [
        clean_text(record.get("employee_id")) or "unknown-employee",
        clean_text(record.get("week_start_date")) or "unknown-week",
        clean_text(record.get("project_code")) or "unknown-project",
        clean_text(record.get("activity_type")).lower().replace(" ", "-").replace("/", "") or "unknown-activity",
    ]
    return "::".join(parts)


def normalize_numeric_fields(record: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(record)
    for field in (
        "employee_id",
        "full_name",
        "job_title",
        "job_family",
        "team_name",
        "org_unit",
        "manager_id",
        "email_volume",
        "project_code",
        "project_name",
        "activity_type",
        "submission_notes",
    ):
        normalized[field] = clean_text(normalized.get(field)) or None
    for field in ("week_start_date", "week_end_date"):
        normalized[field] = parse_date(normalized.get(field))
    for field in (
        "standard_days",
        "holiday_days",
        "pto_days",
        "sick_days",
        "actual_working_days",
        "meeting_count",
        "ticket_count",
        "code_commit_count",
        "system_activity_score",
    ):
        normalized[field] = to_int(normalized.get(field))
    normalized["hours_allocated"] = to_number(normalized.get("hours_allocated"))
    return normalized


def json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [json_safe(item) for item in value]
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            pass
    return value


def assess_row_quality(raw_record: Dict[str, Any], normalized: Dict[str, Any]) -> Dict[str, Any]:
    issues: List[str] = []
    quarantined_fields: List[str] = []
    missing = [field for field in REQUIRED_FIELDS if not clean_text(normalized.get(field))]
    for field in missing:
        issues.append(f"Missing required field: {field}")
        quarantined_fields.append(field)

    hours = to_number(normalized.get("hours_allocated"))
    if hours <= 0:
        issues.append("hours_allocated must be greater than zero")
        quarantined_fields.append("hours_allocated")

    activity_score = to_int(normalized.get("system_activity_score"))
    if activity_score < 0 or activity_score > 100:
        issues.append("system_activity_score must be between 0 and 100")
        quarantined_fields.append("system_activity_score")

    status = "quarantined" if quarantined_fields else "clean"
    return {
        "status": status,
        "issues": issues,
        "repairedFields": [],
        "quarantinedFields": quarantined_fields,
        "corrections": [],
    }


def infer_persona(record: Dict[str, Any], default_persona: str) -> str:
    family = clean_text(record.get("job_family"))
    title = clean_text(record.get("job_title"))
    if family:
        return f"{family} Weekly Timesheet"
    if title:
        return f"{title} Weekly Timesheet"
    return default_persona


def enrich_record(
    record: Dict[str, Any],
    source_type: str,
    source_file_name: str,
    rule_version: str,
    persona_name: str,
    extraction_confidence: float | None = None,
    raw_fields: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    normalized = normalize_numeric_fields(record)
    normalized_fields = json_safe(dict(normalized))
    record_key = canonical_key(normalized)
    missing_fields = [field for field in REQUIRED_FIELDS if not clean_text(normalized.get(field))]
    row_quality = assess_row_quality(raw_fields or record, normalized)
    quality = DataQuality(
        completenessScore=round((len(REQUIRED_FIELDS) - len(missing_fields)) / len(REQUIRED_FIELDS), 2),
        missingFields=missing_fields,
        warnings=list(row_quality["issues"]),
    )
    record_model = NormalizedActivityRecord(
        **normalized,
        key=record_key,
        source=source_type,
        source_file_name=source_file_name,
        source_record_id=clean_text(normalized.get("_sourceRecordId")) or clean_text((raw_fields or {}).get("_sourceRecordId")) or None,
        rule_version=rule_version,
        persona=infer_persona(normalized, persona_name),
        normalized_at=datetime.utcnow().isoformat() + "Z",
        extraction_confidence=round((extraction_confidence or 1.0) * 100, 2),
        raw_fields=json_safe(raw_fields or dict(record)),
        normalized_fields=normalized_fields,
        data_quality=quality,
        row_quality=row_quality,
        form_validation=dict(record.get("_formValidation") or {}),
        matched_excel=int(record.get("_matchedExcel", 0)),
    )
    if hasattr(record_model, "model_dump"):
        return record_model.model_dump(by_alias=True)
    return record_model.dict(by_alias=True)
