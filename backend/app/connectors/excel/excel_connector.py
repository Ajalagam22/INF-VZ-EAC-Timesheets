from __future__ import annotations

from io import BytesIO
from typing import Any, Dict, Iterable, List

import pandas as pd

from app.connectors.base.base_connector import BaseConnector
from app.config.settings import get_settings
from app.enrichment.pipeline import REQUIRED_FIELDS, clean_text, enrich_record


class ExcelConnector(BaseConnector):
    source_type = "Excel"

    def __init__(self) -> None:
        self.settings = get_settings()
        self.workbook_sections: Dict[str, Any] = {
            "sheet_names": [],
            "dataset_sheet_name": None,
            "definition_sheet_name": None,
            "mapping_sheet_name": None,
            "dataset_rows": [],
            "definition_rows": [],
            "mapping_rows": [],
        }

    def extract(self, payload: bytes, filename: str) -> List[Dict[str, Any]]:
        workbook = pd.ExcelFile(BytesIO(payload))
        sheet_names = workbook.sheet_names
        dataset_sheet_name = "Data document for VZ" if "Data document for VZ" in sheet_names else sheet_names[0]
        definition_sheet_name = sheet_names[1] if len(sheet_names) > 1 else None
        mapping_sheet_name = sheet_names[2] if len(sheet_names) > 2 else None
        dataset_frame = pd.read_excel(workbook, sheet_name=dataset_sheet_name, dtype=object).fillna("")
        definition_rows = (
            pd.read_excel(workbook, sheet_name=definition_sheet_name, dtype=object).fillna("").to_dict(orient="records")
            if definition_sheet_name
            else []
        )
        mapping_rows = (
            pd.read_excel(workbook, sheet_name=mapping_sheet_name, dtype=object).fillna("").to_dict(orient="records")
            if mapping_sheet_name
            else []
        )
        dataset_rows = dataset_frame.to_dict(orient="records")
        self.workbook_sections = {
            "sheet_names": sheet_names,
            "dataset_sheet_name": dataset_sheet_name,
            "definition_sheet_name": definition_sheet_name,
            "mapping_sheet_name": mapping_sheet_name,
            "dataset_rows": dataset_rows,
            "definition_rows": definition_rows,
            "mapping_rows": mapping_rows,
        }
        return dataset_rows

    def workbook_summary(self) -> Dict[str, Any]:
        return dict(self.workbook_sections)

    def normalize(self, raw_records: Iterable[Dict[str, Any]], filename: str) -> List[Dict[str, Any]]:
        normalized: List[Dict[str, Any]] = []
        for index, record in enumerate(raw_records):
            if not clean_text(record.get("employee_id")) and not clean_text(record.get("project_code")):
                continue
            normalized.append(
                enrich_record(
                    dict(record),
                    source_type=self.source_type,
                    source_file_name=filename,
                    rule_version=self.settings.rule_version,
                    persona_name=self.settings.persona_name,
                    extraction_confidence=1.0,
                    raw_fields=dict(record)
                ) | {"_sourceRecordId": str(index)}
            )
        return normalized

    def validate(self, normalized_records: Iterable[Dict[str, Any]]) -> List[str]:
        errors: List[str] = []
        records = list(normalized_records)
        for index, record in enumerate(records):
            for field in REQUIRED_FIELDS:
                if not clean_text(record.get(field)):
                    errors.append(f"Excel record {index} missing {field}")
            if float(record.get("hours_allocated") or 0) <= 0:
                errors.append(f"Excel record {index} has non-positive hours_allocated")

        grouped: Dict[tuple, Dict[str, Any]] = {}
        for record in records:
            key = (record.get("employee_id"), record.get("week_start_date"))
            bucket = grouped.setdefault(key, {"hours": 0.0, "expected": None})
            bucket["hours"] += float(record.get("hours_allocated") or 0)
            bucket["expected"] = float(record.get("actual_working_days") or 0) * 8
        for key, values in grouped.items():
            if values["expected"] and round(values["hours"], 2) != round(values["expected"], 2):
                errors.append(
                    f"Employee-week {key[0]} {key[1]} hours sum {values['hours']} but expected {values['expected']}"
                )
        return errors
