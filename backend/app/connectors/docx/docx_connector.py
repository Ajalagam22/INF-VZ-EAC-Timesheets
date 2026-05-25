from __future__ import annotations

import logging
import re
import zipfile
from io import BytesIO
from typing import Any, Dict, Iterable, List

from docx import Document

from app.connectors.base.base_connector import BaseConnector
from app.config.settings import get_settings
from app.enrichment.pipeline import clean_text, enrich_record, normalize_numeric_fields, parse_date

logger = logging.getLogger(__name__)


class DocxConnector(BaseConnector):
    source_type = "DOCX form"

    def __init__(self) -> None:
        self.settings = get_settings()

    def _document(self, payload: bytes) -> Document:
        return Document(BytesIO(payload))

    def _extract_text(self, document: Document) -> str:
        parts: List[str] = []
        for paragraph in document.paragraphs:
            line = paragraph.text.strip()
            if line:
                parts.append(line)
        for table in document.tables:
            for row in table.rows:
                values = [" ".join(cell.text.split()) for cell in row.cells]
                if any(values):
                    parts.append(" | ".join(values))
        return "\n".join(parts)

    def extract(self, payload: bytes, filename: str) -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []
        buffer = BytesIO(payload)
        if filename.split("/")[-1].startswith("~$"):
            return records

        if filename.lower().endswith(".zip") and zipfile.is_zipfile(buffer):
            buffer.seek(0)
            with zipfile.ZipFile(buffer) as archive:
                members = [
                    member
                    for member in archive.infolist()
                    if not member.is_dir()
                    and member.filename.lower().endswith(".docx")
                    and not member.filename.split("/")[-1].startswith("._")
                    and not member.filename.split("/")[-1].startswith("~$")
                ]
                for member in members:
                    try:
                        doc = self._document(archive.read(member))
                        records.extend(self._parse_document(doc, member.filename.split("/")[-1]))
                    except Exception as exc:
                        logger.warning("Skipping invalid DOCX member %s: %s", member.filename, exc)
                return records

        doc = self._document(payload)
        return self._parse_document(doc, filename)

    def _value_after(self, text: str, label: str) -> str | None:
        match = re.search(rf"{re.escape(label)}:\s*(.+)", text, flags=re.IGNORECASE)
        if not match:
            return None
        return clean_text(match.group(1).split("|")[0])

    def _parse_document(self, document: Document, source_record_id: str) -> List[Dict[str, Any]]:
        text = self._extract_text(document)
        common: Dict[str, Any] = {
            "full_name": self._value_after(text, "Employee Name"),
            "employee_id": self._value_after(text, "Employee ID"),
            "job_title": self._value_after(text, "Title"),
            "job_family": self._value_after(text, "Job Family"),
            "team_name": self._value_after(text, "Team"),
            "org_unit": self._value_after(text, "Org Unit"),
            "manager_id": self._value_after(text, "Direct Manager"),
            "week_start_date": parse_date(self._value_after(text, "Week Start")),
            "week_end_date": parse_date(self._value_after(text, "Week End")),
            "standard_days": self._value_after(text, "Standard Working Days"),
            "holiday_days": self._value_after(text, "Company Holiday Days"),
            "pto_days": self._value_after(text, "PTO Days Taken"),
            "sick_days": self._value_after(text, "Sick Days Taken"),
            "actual_working_days": self._value_after(text, "Actual Working Days"),
            "meeting_count": 0,
            "ticket_count": 0,
            "email_volume": "medium",
            "code_commit_count": 0,
            "system_activity_score": 50,
            "submission_notes": self._work_summary(text),
            "_sourceRecordId": source_record_id,
        }

        line_items: List[Dict[str, Any]] = []
        for table in document.tables:
            rows = table.rows
            if not rows:
                continue
            headers = [clean_text(cell.text).lower() for cell in rows[0].cells]
            if not {"project code", "project name", "activity type", "hours"}.issubset(set(headers)):
                continue
            indexes = {header: headers.index(header) for header in headers}
            for row in rows[1:]:
                cells = [clean_text(cell.text) for cell in row.cells]
                if len(cells) < 4 or not cells[indexes["project code"]].startswith("PRJ-"):
                    continue
                line_items.append(
                    {
                        **common,
                        "project_code": cells[indexes["project code"]],
                        "project_name": cells[indexes["project name"]],
                        "activity_type": cells[indexes["activity type"]],
                        "hours_allocated": cells[indexes["hours"]],
                    }
                )

        if not line_items:
            line_items.append(common)

        total_fields = 14
        for item in line_items:
            extracted = sum(1 for field in (
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
            ) if clean_text(item.get(field)))
            item["_extractedFields"] = extracted
            item["_totalFields"] = total_fields
            item["_extractionConfidence"] = extracted / total_fields
        return line_items

    def _work_summary(self, text: str) -> str | None:
        match = re.search(
            r"WORK SUMMARY\s*(.+?)\s*Submitted by:",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if not match:
            return None
        return clean_text(match.group(1))

    def normalize(self, raw_records: Iterable[Dict[str, Any]], filename: str) -> List[Dict[str, Any]]:
        normalized: List[Dict[str, Any]] = []
        seen_keys: set[str] = set()
        for index, record in enumerate(raw_records):
            payload = normalize_numeric_fields(dict(record))
            enriched = enrich_record(
                payload,
                source_type=self.source_type,
                source_file_name=filename,
                rule_version=self.settings.rule_version,
                persona_name=self.settings.persona_name,
                extraction_confidence=record.get("_extractionConfidence", 0.0),
                raw_fields=dict(record),
            ) | {
                "_sourceRecordId": str(record.get("_sourceRecordId") or index),
                "_formValidation": {
                    "extractedFields": int(record.get("_extractedFields", 0)),
                    "totalFields": int(record.get("_totalFields", 14)),
                },
            }
            record_key = str(enriched.get("_key") or "")
            if record_key and record_key in seen_keys:
                continue
            if record_key:
                seen_keys.add(record_key)
            normalized.append(enriched)
        return normalized

    def validate(self, normalized_records: Iterable[Dict[str, Any]]) -> List[str]:
        errors: List[str] = []
        for index, record in enumerate(normalized_records):
            validation = record.get("_formValidation", {})
            extracted = int(validation.get("extractedFields", 0))
            total = int(validation.get("totalFields", 1))
            if extracted / max(total, 1) < self.settings.extraction_confidence_floor:
                errors.append(f"DOCX record {index} extraction confidence below threshold")
            for field in ("employee_id", "week_start_date", "project_code", "activity_type", "hours_allocated"):
                if not clean_text(record.get(field)):
                    errors.append(f"DOCX record {index} missing {field}")
        return errors
