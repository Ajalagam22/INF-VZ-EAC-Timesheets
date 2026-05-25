# EAC Labor Timesheets Design Decisions and Architecture Rationale

## Purpose

This document records the major product, architecture, UI, data, and implementation decisions for the EAC Labor Timesheets application. It follows the same intent as the EAC System Copy design rationale: make the POC defensible to senior architects, accounting SMEs, finance reviewers, and engineers who need to understand whether the implementation can evolve into a production capability.

The project is treated as a production-shaped POC. The current build is intentionally lightweight enough to run locally, but the boundaries, contracts, audit model, and review workflows are designed so enterprise services can replace local pieces without rewriting the classification engine.

## Guiding Principles

1. **Engine-first design**
   The classification engine is the primary product. Connectors, screens, and agent traces exist to feed, explain, and govern the engine.

2. **Source-agnostic classification**
   Excel rows and DOCX form entries are both normalized into one canonical activity schema before classification. The engine does not contain Excel-specific or DOCX-specific logic.

3. **Deterministic-first accounting decisions**
   CapEx / OpEx classification must be repeatable, explainable, and tied to versioned rules. LLM and semantic components can enrich evidence, but deterministic policy and confidence routing remain authoritative.

4. **Human review is part of the control system**
   Ambiguous or low-confidence records route to Review Queue for team-lead resolution. High-confidence records move to Employee Review for review-and-confirm.

5. **Employee experience is review-and-confirm**
   Employees should see a useful pre-populated packet, not a blank timesheet. The employee edits only the exception fields: classification, project code, notes, and weekly attendance adjustments.

6. **Auditability is not optional**
   Every classification and correction needs source provenance, input signals, confidence, rule version, output, override state, and event history.

7. **Governed feedback, not silent self-learning**
   Employee submissions and team-lead overrides are valuable training signals. They should be captured and reviewed before changing rules or model behavior.

## Delivery Posture

### Decision

Deliver a no-login local/public POC while documenting the production security and operating model.

### Why

The assessment and showcase need fast access and low deployment friction. A login wall or heavy enterprise dependency would slow evaluation. The domain still contains employee and finance-sensitive data, so the architecture must show how RBAC, audit retention, storage controls, and workflow separation would work in production.

### Tradeoff

| Choice | Benefit | Cost | Mitigation |
| --- | --- | --- | --- |
| Public/no-login POC | Easy evaluation and demo access | Does not prove role enforcement | Document employee, lead, finance, admin, and platform roles |
| SQLite local persistence | Simple local testing | Not a production audit store | Production path uses PostgreSQL plus immutable audit storage |
| Upload-triggered batch | Easy user-driven demo | Not true nightly automation | Same orchestrator can be triggered by scheduler/queue later |

## Product Navigation Decision

### Decision

Use a left-rail enterprise workflow organized around review, employee analysis, auditability, and data operations.

### Current Navigation

| Tab | Purpose |
| --- | --- |
| Overview | Aggregate CapEx / OpEx outcomes and project-level metrics |
| Activity Records | Full row-level canonical record explorer with filters and expansion |
| Review Queue | Team-lead queue for low-confidence or ambiguous records |
| Employee Review | Employee review-and-confirm packet with editable weekly data |
| Employee Directory | Employee-level history, project mix, activity mix, and contribution view |
| Analytics | KPI cards, CapEx spend by project (horizontal bars), weekly CapEx vs OpEx stacked bars with hover tooltips |
| Audit Trail | Classification trace, event timeline, and agent pipeline evidence |
| Data Sources | Connector ingestion, classification pipeline view, and form validation |
| Feedback Learning | Correction patterns and governed learning loop |

### Why

The required product is not a file upload demo. It must demonstrate a complete operating model: ingest data, classify, route exceptions, allow employee confirmation, inspect evidence, and learn from corrections.

### Tradeoff

- **Pros:** Communicates a production-grade operating system and covers all review audiences.
- **Cons:** More surface area than a minimal POC.
- **Mitigation:** Each screen maps to a specific requirement or demo proof point.

## Branding Decision

### Decision

Use the EAC label with a Verizon-style V mark and the subtitle `Labor Timesheets`.

### Why

The Timesheets app is still part of the EAC family, but the user-facing workflow is weekly labor review rather than the annual survey workflow. The brand should signal continuity with the EAC System Copy while making the use case specific.

### Current Header

- Brand mark: `V`
- Title: `EAC`
- Caption: `Labor Timesheets`
- Top application title: `Project Coder Weekly Timesheet`

## Data Connector Decision

### Decision

Implement two active connectors and represent future sources as Coming Soon cards.

### Active Connectors

1. **Excel Dataset Connector**
   - Reads the primary synthetic workbook.
   - Selects `Data document for VZ` when present.
   - Reads data definition and mapping sheets when available.
   - Normalizes each row into the canonical timesheet activity schema.
   - Validates required fields and employee-week hour totals.

2. **Form Document Parser**
   - Accepts one DOCX file or a ZIP of DOCX files.
   - Extracts employee header fields, week dates, attendance fields, project lines, activity types, and hours.
   - Produces the same canonical schema as Excel.
   - Deduplicates form records by stable key.
   - Validates extraction confidence and required fields.

### Coming Soon Connectors

- Google Drive
- Google Sheets
- SharePoint
- BigQuery
- Jira
- Slack
- MCP Servers
- HRIS / Workday
- ERP / finance rules

### Why

The requirements explicitly require a functional Excel dataset connector and a raw DOCX timesheet parser. Future connectors need to be shown through a stable connector contract but do not need to be production-functional in the POC.

## Canonical Schema Decision

### Decision

Normalize all sources into one `NormalizedActivityRecord` / activity payload before classification.

### Why

The engine must work on activity facts, not source-specific file structures. A shared schema also enables form validation, source comparison, audit traceability, and future connector expansion.

### Key Canonical Fields

| Group | Fields |
| --- | --- |
| Employee | employee_id, full_name, job_title, job_family, team_name, org_unit, manager_id |
| Week | week_start_date, week_end_date, standard_days, holiday_days, pto_days, sick_days, actual_working_days |
| Work | project_code, project_name, activity_type, hours_allocated, submission_notes |
| Signals | meeting_count, ticket_count, email_volume, code_commit_count, system_activity_score |
| Provenance | source type, source file, source record id, extraction confidence, raw fields |
| Classification | class, confidence, evidence, review reason, rule version, override |

### Tradeoff

- **Pros:** Engine is testable and connector-agnostic.
- **Cons:** Some DOCX fields require fallback/default values when the form lacks structured signals.
- **Mitigation:** Defaults are visible through extraction confidence, source provenance, and audit context.

## Classification Decision

### Decision

Use a hybrid pipeline with deterministic policy rules as the final decision authority.

### Role of Each Technique

| Technique | Role |
| --- | --- |
| Deterministic accounting rules | Final CapEx / OpEx / Review decision authority |
| Signal weighting | Confidence and evidence support |
| LLM enrichment | Optional context, evidence language, and gray-area rationale |
| Semantic retrieval | Similar precedent and policy context for audit trace |
| Human review | Final safety layer for low-confidence records |

### Why

Financial classification must be repeatable and defensible. An LLM-only classifier would create audit risk because the same record might receive different explanations or decisions. Deterministic rules provide governance, while LLM/semantic layers improve usability and explanation quality.

### Current Runtime Behavior

- Records are classified through the `AgenticPipeline`.
- The LangGraph graph contains harvesting, context, retrieval, policy, classification, and routing nodes.
- LLM calls are pre-fetched with concurrency control.
- If LLM execution fails, the pipeline falls back to review routing rather than silently accepting an unreliable output.
- Manual overrides do not delete the original classification; they are stored separately.

## Confidence and Routing Decision

### Decision

Route based on effective class and confidence threshold.

### Routing Rules

| Condition | Destination |
| --- | --- |
| CapEx / OpEx with sufficient confidence | Employee Review |
| CapEx / OpEx resolved by team-lead override | Employee Review |
| Review class | Review Queue |
| Confidence below threshold without override | Review Queue |
| Quarantined rows | Review / diagnostic state |

### Why

Low-confidence items should not be pushed to individual employees. Employees receive reviewed or high-confidence drafts. Team leads handle ambiguous records first.

## Employee Review Decision

### Decision

Show each employee once, with all weeks in a single editable review packet.

### Why

Reviewing one employee-week at a time becomes fragmented. The requested showcase needs employee-by-employee review with project history, weekly context, and CapEx / OpEx contribution visible together.

### Current Review Capabilities

- Employee list sorted by employee ID.
- Fuzzy search and best-match auto-selection.
- All weeks for the selected employee in one view.
- Week-level editable attendance values: holidays, PTO, sick days.
- Timesheet-line editable values: classification, project code, notes.
- Save and submit buttons with fixed dimensions.
- Audit event creation on correction and submit.

### Tradeoff

- **Pros:** Better employee-level context and demo clarity.
- **Cons:** Large employees with many weeks can create a long page.
- **Mitigation:** Week sections create visual grouping and can later support collapse/expand.

## Employee Directory Decision

### Decision

Separate Employee Directory from Employee Review.

### Why

The review screen is an action surface. The directory is an analytical browsing surface. Combining them would make the employee UX clumsy and duplicate the all-records table.

### Current Directory Capabilities

- Employee ID ordered list.
- Same fuzzy search behavior as Employee Review.
- Automatic best-match detail loading.
- CapEx / OpEx contribution.
- Project and activity mix.
- Weekly history and attendance context.
- Audit links from employee activities.

## Activity Records Decision

### Decision

Keep Activity Records as a canonical source-of-truth table, similar to the EAC System Copy All Records tab.

### Why

Auditors, engineers, and reviewers need one place to inspect every field on every row. Employee views summarize and organize data, but Activity Records must expose the full normalized contract.

### Current Capabilities

- Project code filter.
- Date filter.
- Class filter.
- Pagination.
- Expandable row detail.
- Manual override.
- Evidence and confidence display.

## Audit Trail Decision

### Decision

Implement a production-shaped audit trail with persisted events and EAC-style agent trace.

### Why

Auditability is a central requirement. The POC should not just show a status badge; it should let the reviewer inspect how the system arrived at a decision and how humans changed it.

### Audit Contents

- Record identity and source provenance.
- Classification trace.
- Timesheet context.
- Signal ledger.
- Semantic precedent placeholders.
- Agent pipeline trace.
- Event timeline.
- Override and employee review update events.

### Tradeoff

- **Pros:** Strong compliance and demo story.
- **Cons:** Local SQLite audit is not immutable production storage.
- **Mitigation:** Production architecture replaces it with append-only audit storage and access logs.

## Data Sources UX Decision

### Decision

Use the same three-subtab pattern as EAC System Copy: Connectors, Classification Pipeline, and Form Extraction Validation.

### Why

The Data Sources screen must prove three things: connectors are active, the pipeline is source-agnostic, and form extraction can be validated against the dataset.

### UX Details

- Upload does not ingest until Run Sync is clicked.
- Job progress is polled through ingestion job status.
- Excel and forms have independent connector cards.
- Form validation compares DOCX extraction to Excel mapping.
- Coming Soon connector catalog communicates extensibility.

## Feedback Learning Decision

### Decision

Capture feedback as governed learning data, not automatic retraining.

### Why

Manual corrections are useful labels, but accounting rules cannot silently change because one user corrected one record. Feedback should inform future calibration after review.

### Learning Loop

1. System classifies a record.
2. Team lead or employee corrects it.
3. Correction event captures original output, final output, note, rule version, and source context.
4. Feedback Learning summarizes patterns.
5. Offline review determines whether rules, thresholds, or prompts should change.
6. Approved changes are versioned and promoted.

## Persistence Decision

### POC Decision

Use SQLite through SQLAlchemy for local state.

### Why

SQLite keeps local testing simple and supports the current app well: records, runs, jobs, progress, overrides, and audit events persist across local sessions.

### Production Decision

Use PostgreSQL for canonical records and operational state, with append-only audit storage and object storage for raw uploaded artifacts.

### Tradeoff

- **Pros of SQLite POC:** Easy to run, no external dependency, fast iteration.
- **Cons:** Not suitable for concurrent enterprise traffic, retention policy, or immutable audit.
- **Mitigation:** SQLAlchemy isolates much of the persistence layer, making PostgreSQL migration straightforward.

## LLM Usage Decision

### Decision

Use LLMs only for bounded assistive work and trace enrichment.

### Appropriate LLM Uses

- Evidence summarization.
- Context enrichment.
- Gray-area rationale.
- Form extraction assistance in future.
- Semantic precedent summaries.

### Inappropriate LLM Uses

- Sole final accounting classification.
- Silent rule changes.
- Undocumented policy interpretation.
- Employee-specific conclusions without source evidence.

### Reliability Controls

- Provider configuration through environment variables.
- Local stub/fallback path.
- Concurrency limits.
- Structured agent trace.
- Review routing when pipeline exceptions occur.

## Recovery Estimate Decision

### Decision

Show recovery estimate as a POC proxy, not an official finance number.

### Current Formula

`CapEx hours * 125`

### Why

The synthetic dataset does not provide an authoritative loaded labor cost by employee, job family, or project. A simple proxy helps reviewers understand relative impact without claiming official recovery.

### Production Replacement

Use approved labor rates from HR/finance:

- employee loaded rate,
- job-family blended rate,
- project-specific rate,
- or finance-approved standard cost table.

## Known Production Gaps

| Area | Current POC | Production Need |
| --- | --- | --- |
| Identity | No login | SSO and role-based access |
| Database | SQLite | PostgreSQL with migrations and HA |
| Audit | Local event table | Immutable append-only audit/event archive |
| File storage | Local upload processing | Object storage with retention and encryption |
| Queue | Local job state/background worker | Managed queue with retry/dead-letter |
| Scheduler | Upload-triggered | Nightly batch scheduler |
| Semantic retrieval | Stub/precomputed trace | Vector store over approved precedents |
| LLM governance | Configured provider/fallback | Prompt registry, monitoring, approvals |
| Future connectors | Coming Soon | Real connector implementations |
| Feedback learning | Captured events | Offline calibration and promotion workflow |

## Summary

The recommended design is a deterministic, policy-led labor classification platform with AI-assisted extraction, evidence enrichment, and semantic context. The Timesheets app emphasizes employee-level review, team-lead exception handling, and auditability. The current POC is intentionally pragmatic, but its architecture preserves the boundaries needed for production: connector contracts, canonical schema, agent pipeline, confidence routing, audit trail, and governed feedback learning.
