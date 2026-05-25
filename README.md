# EAC Labor Timesheets

AI-enabled CapEx / OpEx review application for the Project Coder Weekly Timesheet use case.

The application ingests weekly labor activity data from Excel and raw DOCX timesheet forms, normalizes both sources into one canonical activity schema, classifies labor as `CapEx`, `OpEx`, or `Review`, and presents the output through dashboards, review queues, employee-level review screens, audit traces, and connector validation views.

## Purpose

Large engineering and technology teams often reconstruct weekly project labor from memory. That creates inaccurate timesheets, missed capitalization opportunities, and weak audit support. This app demonstrates a review-and-confirm workflow where the system pre-populates timesheet classifications from structured activity data and lets employees or team leads review only what needs correction.

The POC focuses on:

- Weekly project-coded labor.
- CapEx / OpEx classification.
- Employee-level timesheet review.
- Team-lead review queue for ambiguous records.
- Auditability and evidence traceability.
- Excel plus DOCX/ZIP ingestion.
- Stubbed connector expansion for future sources.

## Core Data Flow

1. **Upload data** in `Data Sources`.
2. **Excel connector** loads the synthetic activity workbook.
3. **Form parser connector** loads one DOCX file or a ZIP of DOCX forms.
4. Records are normalized into the shared canonical activity schema.
5. The classification pipeline produces class, confidence, evidence, signals, and audit events.
6. High-confidence records become employee review packets.
7. Low-confidence or ambiguous records go to the Review Queue.
8. Corrections and submissions are saved back to the record payload and audit trail.

## Application Screens

### Overview

The Overview screen summarizes portfolio-level CapEx / OpEx outcomes:

- Total records, hours, CapEx hours, OpEx hours, and review volume.
- Project-code level CapEx / OpEx overview.
- Capitalization trend visuals.
- Overall classification and recovery indicators.

This is the first screen for a finance reviewer or demo audience to understand the current labor classification outcome.

### Activity Records

Activity Records is the detailed row-level explorer.

It supports:

- Project code filtering.
- Date filtering.
- Pagination.
- CapEx / OpEx / Review filtering.
- Expandable rows.
- Full canonical field display similar to the EAC reference system.
- Manual classification override controls.

Each expanded row shows the complete record context from the ingested dataset, including employee information, project information, work activity, attendance fields, classification evidence, and source metadata.

### Review Queue

Review Queue is the team-lead escalation surface.

It shows low-confidence or ambiguous records that should not be sent directly to individual employees. Team leads can review the record, inspect the same detailed canonical fields used in Activity Records, and resolve the item by selecting `CapEx`, `OpEx`, or `Review`.

When a record is resolved to `CapEx` or `OpEx`, it is removed from the queue and becomes eligible for employee review.

### Employee Review

Employee Review is the review-and-confirm workspace for employee-facing weekly timesheet packets.

Features:

- Employees are listed by employee ID order.
- Search supports exact and fuzzy matching across employee ID, name, title, team, and manager.
- The right-side detail panel automatically opens the best matching employee while searching.
- Each selected employee shows all weeks in one view, not one screen per week.
- Each week contains editable attendance fields:
  - Holidays
  - PTO
  - Sick days
  - Calculated working days
- Each timesheet line is editable:
  - Classification
  - Project code
  - Employee notes
- `Save Changes` persists edits.
- `Submit Draft` records the employee submission event.

Every employee edit is captured in the audit trail.

### Employee Directory

Employee Directory is the employee-level analysis view.

It is designed for browsing employee history rather than submitting edits. It shows:

- Employee list sorted by employee ID.
- Fuzzy search with automatic best-match detail loading.
- Total hours across weeks.
- CapEx / OpEx contribution.
- Project mix.
- Activity mix.
- Weekly timesheet history.
- Sick, PTO, holiday, and workday context.
- Links from employee activity back to audit details.

This screen is useful for employee-by-employee review, pattern recognition, and manager walkthroughs.

### Analytics

Analytics provides operational views beyond the Overview screen, focused on actionable classification insight.

Current analytics panels include:

- Six KPI metric cards: total CapEx records, total OpEx records, pending review count, CapEx spend estimate, override rate, and average confidence.
- CapEx Spend by Project — horizontal bar chart showing relative CapEx hour contribution per project code.
- Weekly CapEx vs OpEx — stacked bar chart showing classified hours per week broken down by CapEx, OpEx, and Review, with hover tooltips showing exact hour counts and CapEx percentage per week.

The goal is to help reviewers understand classification outcomes per project and per week without requiring a full time series.

### Audit Trail

Audit Trail provides traceability for classification and review actions.

It includes:

- Paginated audit events.
- Expandable record details.
- Classification trace.
- Timesheet context.
- Signal ledger.
- Semantic precedent placeholders.
- Agent pipeline trace.
- Event timeline.

Audit entries capture ingestion, classification, overrides, employee edits, and draft submissions. The design mirrors the EAC reference system so reviewers can inspect why a record was classified and what changed later.

### Data Sources

Data Sources is the connector and ingestion workspace.

It has three subtabs:

- **Connectors**
  - Excel Dataset Connector.
  - Form Document Parser.
  - Upload staging.
  - Run Sync flow.
  - Connector metrics.
  - Coming Soon catalog including Google Drive, Google Sheets, SharePoint, BigQuery, Jira, Slack, and MCP Servers.

- **Classification Pipeline**
  - EAC-style pipeline explanation.
  - Agent responsibilities.
  - Runtime contract.
  - Source-agnostic normalized record flow.

- **Form Extraction Validation**
  - Validates parsed DOCX forms against matching Excel records.
  - Shows extracted form values versus Excel values.
  - Displays match status and extraction confidence.

The form connector accepts either one DOCX file or a ZIP containing multiple DOCX forms.

### Feedback Learning

Feedback Learning captures correction patterns for future model and rules improvement.

It shows:

- Manual override volume and trend summary.
- Correction Log — override history with original class, corrected class, and evidence comparison.
- Calibration Candidates — top records that most need rule or model calibration, displayed alongside the Correction Log in a two-column layout.
- Classification movement analysis.
- Learning loop explanation.

For this POC, the learning loop is captured and displayed. It does not automatically retrain a model.

## Classification Behavior

The app classifies each activity record as:

- `CapEx`: capitalizable labor activity.
- `OpEx`: operating expense labor activity.
- `Review`: ambiguous or low-confidence activity requiring human review.

Each classification carries:

- Confidence score.
- Evidence summary.
- Signal list.
- Rule version.
- Source metadata.
- Audit trace.

Manual overrides are preserved separately from the original classification, so the system can show both original model/rule output and human correction.

## Canonical Schema

Both Excel and DOCX ingestion map into the same normalized activity record contract. Key fields include:

- Employee identity and job context.
- Manager and team.
- Week start and week end.
- Standard days, holiday days, PTO days, sick days, actual working days.
- Project code and project name.
- Activity type.
- Hours allocated.
- Observable work signals.
- Source system and source file.
- Classification, confidence, evidence, and review reason.

This shared schema is what lets the UI compare Excel rows to DOCX forms and lets the classification pipeline stay source-agnostic.

## Agent Pipeline

The app includes a multi-agent style pipeline trace modeled after the EAC reference system.

The represented agents are:

- Harvesting Agent.
- Context Enrichment Agent.
- Semantic Retrieval Agent.
- Policy & Rules Agent.
- Classification Agent.
- Confidence Routing Agent.

Some behaviors are deterministic or stubbed for the POC, but the UI and audit contract are structured to support a LangGraph-style multi-agent implementation.

## Stubbed or Simulated Areas

For the POC, the following areas are simulated or deterministic:

- HR profile enrichment beyond the dataset fields.
- Project code registry beyond loaded test data.
- Historical precedent retrieval.
- Accounting policy knowledge base.
- Real model retraining from feedback.
- Future connectors listed in the catalog.
- Recovery estimate, currently calculated as a demo proxy from CapEx hours.

See `docs/stubs.md` for the detailed stub inventory.

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

Frontend API base configuration is read from the frontend environment. The app currently expects the backend API at:

```text
http://127.0.0.1:8001
```

If using an LLM provider, configure it in `.env`. The deterministic classification and UI demo paths still work without live network calls.

## Useful API Endpoints

Backend routes include:

- `POST /api/upload/excel`
- `POST /api/upload/forms`
- `GET /api/upload/jobs/{job_id}`
- `GET /api/summary`
- `GET /api/records`
- `GET /api/drafts`
- `POST /api/drafts/submit`
- `GET /api/escalations`
- `POST /api/records/{record_uid}/override`
- `PATCH /api/records/{record_uid}`
- `GET /api/audit/{record_uid}`
- `GET /api/connectors`

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

## Demo Walkthrough

1. Start backend and frontend.
2. Open `Data Sources`.
3. Upload the Excel dataset and click `Run Sync`.
4. Upload one DOCX form or a ZIP of DOCX forms and click `Run Sync`.
5. Review connector metrics and form extraction validation.
6. Open `Overview` to inspect aggregate CapEx / OpEx results.
7. Open `Activity Records` to inspect row-level canonical records.
8. Open `Review Queue` and resolve low-confidence items.
9. Open `Employee Review`, search for an employee, edit the weekly packet, and submit.
10. Open `Audit Trail` to inspect the trace and correction events.

