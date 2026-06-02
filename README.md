# EAC Labor Timesheets

AI-enabled CapEx / OpEx review application for the Project Coder Weekly Timesheet use case (UC-2).

The application ingests weekly labor activity data from Excel and raw DOCX timesheet forms, normalizes both sources into one canonical activity schema, classifies labor as `CapEx`, `OpEx`, or `Review`, and presents the output through dashboards, review queues, employee-level review screens, reconciliation reporting, early insights, audit traces, and connector validation views.

## Purpose

Large engineering and technology teams often reconstruct weekly project labor from memory. That creates inaccurate timesheets, missed capitalization opportunities, and weak audit support. This app demonstrates a review-and-confirm workflow where the system pre-populates timesheet classifications from structured activity data and lets employees or team leads review only what needs correction.

The POC addresses requirements REQ-01 through REQ-59, including the May 22 stakeholder addendum (REQ-53 through REQ-59):

- Weekly project-coded labor classification (CapEx / OpEx / Review).
- Employee-level timesheet review and confirmation.
- Team-lead review queue for ambiguous records.
- 7-stage agentic pipeline ending with Reconciliation & Reporting (REQ-54).
- Finance-facing cost-centre reconciliation report with 4-level hierarchical roll-up (REQ-55, REQ-56).
- Early Insights layer with 5 interactive slices and automatic anomaly detection (REQ-58, REQ-59).
- Standalone agentic workflow diagram — PNG, PDF, and embedded in Architecture Document (REQ-53).
- Data Dictionary covering all 5 required sections (REQ-57).
- Auditability and evidence traceability.
- Excel plus DOCX/ZIP ingestion.
- Stubbed connector expansion for future sources.

## Core Data Flow

1. **Upload data** in `Data Sources`.
2. **Excel connector** loads the synthetic activity workbook.
3. **Form parser connector** loads one DOCX file or a ZIP of DOCX forms.
4. Records are normalized into the shared canonical activity schema.
5. The **7-stage agentic pipeline** produces classification, confidence, evidence, signals, routing decision, and reconciliation metadata for every record.
6. High-confidence records become employee review packets.
7. Low-confidence or ambiguous records go to the Review Queue.
8. The **Reconciliation & Reporting Agent** (7th stage) aggregates all records to cost-centre level, computes CapEx/OpEx deltas vs the 100% OpEx baseline, and produces the finance-facing report.
9. Corrections and submissions are saved back to the record payload and audit trail.

## Application Screens

### Overview

Summarizes portfolio-level CapEx / OpEx outcomes:

- Total records, hours, CapEx hours, OpEx hours, and review volume.
- Project-code level CapEx / OpEx overview.
- Capitalization trend visuals.
- Overall classification and recovery indicators.

### Activity Records

Row-level canonical explorer:

- Project code, date, classification, and source filtering.
- Pagination with configurable page size.
- Expandable rows showing full canonical fields, classification evidence, signals, and source metadata.
- Manual classification override controls per record.

### Review Queue

Team-lead escalation surface for low-confidence or ambiguous records:

- Record inspection with full canonical context.
- Resolve to `CapEx`, `OpEx`, or `Review`.
- Resolved records become eligible for employee review.

### Employee Review

Employee-facing review-and-confirm workspace:

- All employees listed; fuzzy search with automatic best-match loading.
- All weeks shown in one view per employee.
- Editable attendance fields: holidays, PTO, sick days, calculated working days.
- Editable timesheet lines: classification, project code, employee notes.
- `Save Changes` persists edits; `Submit Draft` records the submission event.
- Every edit is captured in the audit trail.

### Employee Directory

Employee-level analysis view for browsing and pattern recognition:

- Total hours, CapEx/OpEx contribution, project mix, activity mix.
- Weekly timesheet history with attendance context.
- Links from employee activity to audit details.

### Analytics

Operational views beyond the Overview screen, including:

- Six KPI metric cards: total CapEx records, OpEx records, pending review count, CapEx spend estimate, override rate, and average confidence.
- CapEx Spend by Project — horizontal bar chart per project code.
- Weekly CapEx vs OpEx — stacked bar chart with hover tooltips.
- **Employee Contribution Matrix** — per-employee hours breakdown.

#### Early Insights (REQ-58, REQ-59)

A second output tier that surfaces patterns and anomalies across the classified dataset without requiring the reviewer to inspect individual records. Every slice is interactive — click any row to drill down to the underlying records.

**Insight Slices:**

| Slice | What it shows | Flag logic |
|-------|--------------|------------|
| CapEx / OpEx Split by Job Title | Average CapEx % per job title | Flagged when employees within the same role disagree by >40 percentage points (internal variance — not a global average comparison) |
| Job Function Across Business Units | Same role in different teams — side-by-side CapEx % | Flagged when spread >25 points; labelled as "quick win" per client feedback |
| CapEx Capitalisation Rate by Team | Per-team CapEx %; highest and lowest flagged | Shows review segment where records are still unresolved |
| Project Capitalisation Rates | Per-project CapEx rate | Flagged when a project has CapEx hours but <30% capitalisation rate |
| Activity Type Distribution | Hours volume by activity type | Flagged when employees spending 100% of time in one activity category are found; shows count |
| Completion & Escalation Rate by Team | % of records classified with high confidence vs escalated, by team | Teams with >40% escalation rate flagged |

**Automatic Anomaly Detection (REQ-59):**

| Anomaly | Trigger |
|---------|---------|
| Large Cross-Team Capitalisation Spread | Single finding showing the highest and lowest team pair when the spread exceeds 50 percentage points |
| Low CapEx Project | Projects with CapEx-classified hours but <25% overall capitalisation rate |
| Single-Activity Employee | Employees with 3+ records all in one activity type — may indicate misclassification |

### Reconciliation (REQ-54, REQ-55, REQ-56)

Finance-facing cost-centre reconciliation report, implemented as the 7th stage of the agentic pipeline.

**Header metrics:** Employees processed, cost centres, total hours, CapEx hours, capitalisation rate, recovery estimate (CapEx hours × $125/hr).

**4-level hierarchical roll-up** — click any row to expand the next level:

| Level | What is shown |
|-------|--------------|
| Cost Centre | Employees, completed records, outstanding records, total/CapEx/OpEx hours, capitalisation bar, delta vs baseline, flagged count |
| Job Title | Aggregated stats for all employees with that role within the cost centre |
| Employee | Individual employee stats including review hours; expandable if they have project records |
| Project | Per-project-code hour breakdown with CapEx/OpEx split |

All levels expose the same columns: Count, Completed, Outstanding, Total Hours, CapEx Hours, OpEx Hours, Capitalisation %, Delta vs Baseline, Flagged.

**Data Schema & Production Integration Note** is embedded in the screen, documenting:
- Full report field schema (all 14 fields with types and business definitions).
- SAP S/4HANA / CO-PA integration path.
- Power BI / Tableau / Looker BI connector path.
- CSV/Excel export path for tax and accounting teams.
- Delta calculation method and cost rate sourcing.

### Audit Trail

Traceability for classification and review actions:

- Paginated audit events.
- Expandable record details and classification trace.
- Signal ledger and agent pipeline trace.
- Event timeline covering ingestion, classification, overrides, edits, and submissions.

### Data Sources

Connector and ingestion workspace with three subtabs:

- **Connectors** — Excel Dataset Connector, Form Document Parser, upload staging, Run Sync flow, connector metrics, Coming Soon catalog.
- **Classification Pipeline** — EAC-style pipeline explanation with all 7 agent stages.
- **Form Extraction Validation** — parsed DOCX form values vs Excel values, match status, extraction confidence.

### Feedback Learning

Correction pattern capture for future model and rules improvement:

- Override volume and trend summary.
- Correction Log with original vs corrected classification and evidence comparison.
- Calibration Candidates for targeted rule improvement.
- Learning loop explanation.

## Agent Pipeline

The app uses a **7-stage LangGraph state graph**:

```
Harvesting → Context → Retrieval → Policy → Classification → Routing → Reconciliation → END
```

| Stage | Agent | Responsibility |
|-------|-------|---------------|
| ② | Data Harvesting Agent | Ingest, schema validation, quarantine malformed records |
| ③ | Context Building Agent | Per-employee 7-day activity digest, rolling weekly window |
| ④ | Classification Agent | CapEx / OpEx / Review decision, confidence 0–100, evidence trail, signal ledger |
| ⑤ | Policy & Rules Agent | Accounting rule overlay, project code constraints, persona configuration, rule version stamp |
| ⑥ | Confidence & Routing Agent | Approved → Employee Review Queue; low-confidence → Team Lead Escalation Queue |
| ⑦ | Reconciliation & Reporting Agent | Cost-centre stamp, CapEx/OpEx delta vs 100% OpEx baseline, finance report aggregation (REQ-54) |

Agent trace is surfaced verbatim in the Audit Trail for every record.

## Deliverables

| Deliverable | Location | REQ |
|-------------|----------|-----|
| Architecture Document (PDF) | `docs/EAC_Timesheets_Architecture_Document.pdf` | — |
| Agentic Workflow Diagram (PNG) | `docs/EAC_Agentic_Workflow_Diagram.png` | REQ-53 |
| Agentic Workflow Diagram (PDF) | `docs/EAC_Agentic_Workflow_Diagram.pdf` | REQ-53 |
| Data Dictionary | `docs/data_dictionary.md` | REQ-57 |
| API Documentation | `docs/api_documentation.md` | — |
| Stubs Inventory | `docs/stubs.md` | — |

## Classification Behavior

Each record is classified as `CapEx`, `OpEx`, or `Review`. Classification output includes:

- Confidence score (0–100).
- Evidence summary (human-readable).
- Signal list (structured, with impact qualifier per signal).
- Rule version (for replay comparison).
- Source metadata and provenance.
- Routing state (`approved` or `review`).
- Reconciliation metadata (cost centre, delta hours, flagged status).
- Agent trace.

Manual overrides are stored separately from the original classification so the system shows both the rule/model output and the human correction.

## Canonical Schema

Both Excel and DOCX connectors produce the same normalized activity record. Key fields:

- Employee identity and job context (`employee_id`, `full_name`, `job_title`, `job_family`, `team_name`, `org_unit`, `manager_id`).
- Temporal fields (`week_start_date`, `week_end_date`, `standard_days`, `holiday_days`, `pto_days`, `sick_days`, `actual_working_days`).
- Project and activity (`project_code`, `project_name`, `activity_type`, `hours_allocated`, `submission_notes`).
- Observable signals (`meeting_count`, `ticket_count`, `email_volume`, `code_commit_count`, `system_activity_score`).
- Classification output (`_classification`, `_confidence`, `_evidence`, `_signals`, `_routingState`, `_override`, `_ruleVersion`).
- Reconciliation metadata (`_reconciliation.cost_center`, `_reconciliation.capitalisation_delta_hours`, `_reconciliation.flagged`).

Full field documentation is in `docs/data_dictionary.md` (REQ-57).

## Stubbed or Simulated Areas

| Area | Status |
|------|--------|
| HR profile enrichment beyond dataset fields | Simulated from sample data |
| Project code registry | Embedded in Excel source; production would use PPM tool |
| Historical precedent retrieval (Semantic Retrieval Agent) | Stub — returns empty context |
| Accounting policy knowledge base | Deterministic rules; no external knowledge base |
| Real model retraining from feedback | Captured and displayed; no auto-retraining |
| Future connectors (BigQuery, HR systems, Jira, Git) | Listed in catalog; not implemented |
| Recovery estimate | `capex_hours × $125/hr` proxy; production rate from HRIS cost rate table |
| LLM classification | Configurable; deterministic path works without live LLM |

See `docs/stubs.md` for the full stub inventory.

## Useful API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /api/upload/excel` | Stage Excel workbook ingestion |
| `POST /api/upload/forms` | Stage DOCX / ZIP ingestion |
| `GET /api/upload/jobs/{job_id}` | Poll ingestion progress |
| `GET /api/summary` | Dashboard summary metrics |
| `GET /api/records` | Normalized classified records |
| `GET /api/drafts` | Employee weekly review packets |
| `POST /api/drafts/submit` | Submit reviewed employee lines |
| `GET /api/escalations` | Review Queue items |
| `POST /api/records/{record_uid}/override` | Team-lead classification override |
| `PATCH /api/records/{record_uid}` | Employee review edits |
| `GET /api/audit/{record_uid}` | Audit events for a record |
| `GET /api/connectors` | Connector status and metrics |
| `GET /api/reconciliation` | Cost-centre reconciliation report with 4-level roll-up (REQ-54–56) |

## Local Run

Run the backend:

```bash
cd backend
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

Run the frontend:

```bash
cd frontend
npm install
npm run dev -- --hostname 127.0.0.1 --port 3000
```

Open:

```text
http://127.0.0.1:3000
```

## Environment

The app expects the backend API at:

```text
http://127.0.0.1:8001
```

If using an LLM provider, configure it in `.env`. The deterministic classification and all UI demo paths work without live network calls.

## Validation Commands

Compile backend:

```bash
python3 -m compileall backend/app
```

Build frontend:

```bash
cd frontend
npm run build
```

Regenerate architecture PDF:

```bash
cd docs
python3 md_to_pdf_timesheets.py
```

Regenerate standalone agentic workflow diagram (REQ-53):

```bash
cd docs
python3 generate_agentic_workflow_diagram.py
```

## Demo Walkthrough

1. Start backend and frontend.
2. Open `Data Sources`. Upload the Excel dataset and click `Run Sync`. Upload DOCX forms and click `Run Sync`.
3. Open `Overview` — inspect aggregate CapEx / OpEx results and project-level breakdown.
4. Open `Activity Records` — inspect canonical rows, expand a record to see evidence and agent trace.
5. Open `Review Queue` — resolve one or more low-confidence items.
6. Open `Employee Review` — search for an employee, review weekly packet, edit a line, submit.
7. Open `Analytics` — view KPIs and weekly stacked bars. Scroll to **Early Insights** to see the 5 interactive slices. Click a row to drill down to underlying records. Review the Detected Anomalies panel.
8. Open `Reconciliation` — expand a cost centre, then a job title, then an employee to see the 4-level roll-up. Review the Data Schema & Production Integration note.
9. Open `Audit Trail` — inspect the 7-stage agent pipeline trace, evidence, and correction events.
