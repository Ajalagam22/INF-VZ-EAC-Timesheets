"""
DOCX Field Mapping Validator
============================
Run this against any .docx or .zip of forms to see exactly what each regex
extracts, whether it looks clean, and how it compares to the Excel mapping sheet.

Usage:
    python -m tools.validate_docx_mapping <file.docx|file.zip> [EAC_Dataset.xlsx]

Examples:
    python -m tools.validate_docx_mapping "Sample Forms.zip" "EAC_Dataset.xlsx"
    python -m tools.validate_docx_mapping form_01.docx
"""
from __future__ import annotations

import sys
import re
from pathlib import Path
from io import BytesIO
from typing import Any

# Allow running from repo root: python -m tools.validate_docx_mapping ...
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.connectors.docx.docx_connector import DocxConnector
from app.connectors.excel.excel_connector import ExcelConnector
from app.enrichment.pipeline import (
    FORM_FIELD_MAP, clean_text, normalize_numeric_fields, canonical_key
)
from app.config.settings import get_settings

# ── colour helpers ──────────────────────────────────────────────────────────
GREEN = "\033[32m"
RED   = "\033[31m"
AMBER = "\033[33m"
RESET = "\033[0m"
BOLD  = "\033[1m"

def ok(s: str)   -> str: return f"{GREEN}✓ {s}{RESET}"
def fail(s: str) -> str: return f"{RED}✗ {s}{RESET}"
def warn(s: str) -> str: return f"{AMBER}~ {s}{RESET}"
def bold(s: str) -> str: return f"{BOLD}{s}{RESET}"


# ── numeric / text field lists ───────────────────────────────────────────────
NUMERIC_FIELDS = {
    "CapEx_Eligible_Pct", "BudgetAmount_USD", "ActualSpend_USD",
    "ForecastSpend_USD", "CumulativeSpend_USD", "PassingUnits",
    "Asset_Life_Years", "Depreciation_Annual_USD", "Hours_Logged",
    "Miles_Driven", "DriveTests_Completed", "Milestones_Completed",
}
DATE_FIELDS = {"ProjectStartDate", "ProjectEndDate"}

FIELD_NAMES = [f for f, _ in FORM_FIELD_MAP]


def _compare_values(field: str, form_val: Any, excel_val: Any) -> tuple[bool, str]:
    """Return (match, reason) for a single field comparison."""
    fv = clean_text(form_val)
    ev = clean_text(excel_val)
    if not fv and not ev:
        return True, "both blank"
    if not fv:
        return False, f"form missing, excel='{ev}'"
    if not ev:
        return None, f"excel blank, form='{fv}'"   # type: ignore[return-value]

    if field in NUMERIC_FIELDS:
        try:
            fnum = float(str(fv).replace("$","").replace("%","").replace(",",""))
            enum = float(str(ev).replace("$","").replace("%","").replace(",",""))
            if abs(fnum - enum) < 0.01:
                return True, f"{fnum}"
            return False, f"form={fnum}, excel={enum}"
        except ValueError:
            pass

    if field in DATE_FIELDS:
        # normalise both to YYYY-MM-DD before comparing
        from app.enrichment.pipeline import parse_date
        fd = parse_date(fv) or fv
        ed = parse_date(ev) or ev
        match = fd == ed
        return match, f"form={fd}, excel={ed}"

    match = fv.strip().lower() == ev.strip().lower()
    return match, f"form='{fv}', excel='{ev}'"


def _score_against_excel(form_rec: dict, excel_row: dict) -> int:
    """Count matching fields between a form record and an excel row."""
    score = 0
    for f in FIELD_NAMES:
        fv = clean_text(form_rec.get(f))
        ev = clean_text(excel_row.get(f))
        if fv and ev and fv.lower() == ev.lower():
            score += 1
    return score


def _best_excel_match(form_rec: dict, excel_rows: list[dict]) -> tuple[dict | None, int]:
    best_row, best_score = None, -1
    for row in excel_rows:
        s = _score_against_excel(form_rec, row)
        if s > best_score:
            best_score, best_row = s, row
    return best_row, best_score


def validate_form(raw_record: dict, excel_mapping_rows: list[dict], source_name: str) -> None:
    """Print a full extraction + comparison report for one form record."""
    norm = normalize_numeric_fields(dict(raw_record))
    key  = canonical_key(norm)
    extracted = int(raw_record.get("_extractedFields", 0))
    total     = int(raw_record.get("_totalFields", len(FORM_FIELD_MAP)))
    pct       = round(extracted / max(1, total) * 100)

    print(bold(f"\n{'='*70}"))
    print(bold(f"  Form: {source_name}"))
    print(f"  Canonical key : {key}")
    print(f"  Fields found  : {extracted}/{total} ({pct}%)")

    best_excel, best_score = _best_excel_match(norm, excel_mapping_rows) if excel_mapping_rows else (None, 0)
    if best_excel:
        excel_key = canonical_key(best_excel)
        print(f"  Best Excel row: {excel_key} ({best_score}/{total} fields agree)")

    # Field-by-field breakdown
    print()
    print(f"  {'Field':<30} {'Extracted value':<28} {'Excel value':<28} Match")
    print(f"  {'-'*30} {'-'*28} {'-'*28} -----")

    matched = 0
    missing = []
    mismatched = []

    for field in FIELD_NAMES:
        form_val  = norm.get(field)
        excel_val = best_excel.get(field) if best_excel else None

        fv_str = str(form_val)[:26] if form_val is not None else "—"
        ev_str = str(excel_val)[:26] if excel_val is not None and excel_val != "" else "—"

        match, reason = _compare_values(field, form_val, excel_val)

        if match is True:
            matched += 1
            status = GREEN + "✓" + RESET
        elif match is None:
            status = AMBER + "?" + RESET   # form has value, excel blank
        else:
            status = RED + "✗" + RESET
            if not form_val or form_val == "" or form_val == 0.0:
                missing.append(field)
            else:
                mismatched.append((field, reason))

        print(f"  {field:<30} {fv_str:<28} {ev_str:<28} {status}")

    print()
    total_compared = len([f for f in FIELD_NAMES
                          if best_excel and (norm.get(f) or best_excel.get(f))])
    print(f"  Summary: {matched} matched, {len(mismatched)} mismatched, "
          f"{len(missing)} missing from form")
    if mismatched:
        print(f"  {AMBER}Mismatches:{RESET}")
        for f, r in mismatched[:5]:
            print(f"    {f}: {r}")
    if missing:
        print(f"  {RED}Missing from form:{RESET} {', '.join(missing[:8])}")


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    form_path  = Path(sys.argv[1])
    excel_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    if not form_path.exists():
        print(fail(f"File not found: {form_path}"))
        sys.exit(1)

    settings = get_settings()

    # ── load Excel mapping rows ──────────────────────────────────────────────
    excel_mapping_rows: list[dict] = []
    if excel_path and excel_path.exists():
        connector = ExcelConnector()
        connector.extract(excel_path.read_bytes(), excel_path.name)
        excel_mapping_rows = connector.workbook_sections.get("mapping_rows") or []
        dataset_rows = connector.workbook_sections.get("dataset_rows") or []
        # Fall back to full dataset if mapping sheet is empty
        if not excel_mapping_rows:
            excel_mapping_rows = dataset_rows
        print(f"Excel loaded: {excel_path.name}")
        print(f"  Mapping rows: {len(excel_mapping_rows)}")
    else:
        print(warn("No Excel file provided — extraction-only mode (no comparison)"))

    # ── parse DOCX / ZIP ─────────────────────────────────────────────────────
    docx = DocxConnector()
    payload = form_path.read_bytes()
    raw_records = docx.extract(payload, form_path.name)
    print(f"\nParsed {len(raw_records)} form(s) from {form_path.name}")

    # ── validate each form ───────────────────────────────────────────────────
    for rec in raw_records:
        source_id = rec.get("_sourceRecordId") or form_path.name
        validate_form(rec, excel_mapping_rows, source_id)

    # ── overall extraction summary ───────────────────────────────────────────
    print(bold(f"\n{'='*70}"))
    print(bold("OVERALL EXTRACTION SUMMARY"))
    all_pcts = [
        int(r.get("_extractedFields", 0)) / max(1, int(r.get("_totalFields", len(FORM_FIELD_MAP)))) * 100
        for r in raw_records
    ]
    if all_pcts:
        avg = sum(all_pcts) / len(all_pcts)
        print(f"  Forms parsed         : {len(raw_records)}")
        print(f"  Avg extraction rate  : {avg:.1f}%")
        below = [r.get('_sourceRecordId') for r, p in zip(raw_records, all_pcts) if p < 90]
        if below:
            print(warn(f"  Forms < 90% extraction: {below}"))
        else:
            print(ok("  All forms above 90% extraction threshold"))


if __name__ == "__main__":
    main()
