# EAC Labor Timesheets — Data Dictionary

**Requirement:** REQ-57  
**Application:** EAC Labor Timesheets  
**Date:** June 1, 2026  
**Version:** 1.0  

---

## Overview

This document defines every field in the EAC data model. It is organized into five sections that follow the data lifecycle: source record ingestion, project registry lookup, classification output, reconciliation reporting, and the connector interface contract. Each table includes the data type, allowed values or range, business definition, production source system, and transformation notes. Fields that are simulated or derived in the POC are marked **[POC: simulated]** or **[POC: derived]** in the Transformation Notes column.

---

## 1. Employee Activity Record

The Employee Activity Record is the canonical unit of work in the EAC system. One record represents a single employee's allocation of hours to one project code and one activity type for one calendar week. Records are produced by connectors from source files and passed through the agentic pipeline for classification.

### 1.1 Employee Identity Fields

| Field Name | Data Type | Allowed Values / Range | Business Definition | Source System (Production) | Transformation Notes |
| --- | --- | --- | --- | --- | --- |
| `employee_id` | string | Non-empty, unique per employee | Unique identifier for the employee. Used as the primary reference for linking records across weeks, audit events, and review packets. | HRIS (e.g. Workday, SAP SuccessFactors) | Read directly from source. Validated as non-null and non-empty. **[POC: simulated]** values in the sample Excel dataset. |
| `full_name` | string | Non-empty display name | Human-readable full name of the employee. Used for display in the UI and for fuzzy-search matching in Employee Review and Employee Directory. | HRIS | Normalized: leading/trailing whitespace stripped. Not used for record identity; `employee_id` is the authoritative key. |
| `job_title` | string | Free text | Current role designation of the employee (e.g. "Senior Software Engineer"). Informs the classification engine's context about the type of work typically performed. | HRIS | Passed through as-is. Classification engine uses this to set activity-type priors. |
| `job_family` | string | Free text | Functional role group (e.g. "Engineering", "Business Analysis"). Used to group employees in analytics and to weight classification signals. | HRIS | Normalized to trimmed string. **[POC: simulated]** from the sample dataset. |
| `team_name` | string | Free text | Name of the organizational team the employee belongs to (e.g. "Platform Engineering"). Used for team-lead routing and the Review Queue grouping. | HRIS | Passed through. Used by the Confidence & Routing Agent to assign escalations to the correct team lead. |
| `org_unit` | string | Free text (cost centre code or name) | Organizational unit or cost centre the employee is mapped to. Used for cost-centre roll-up in the Finance Reconciliation Report. | HRIS | Normalized to trimmed string. Maps to `cost_center` in reconciliation output. |
| `manager_id` | string | Non-empty employee ID | Employee ID of the direct manager. Used by the routing layer to assign low-confidence records to the correct team lead's escalation queue. | HRIS | Validated as a non-empty string. **[POC: simulated]** in the sample dataset. |

### 1.2 Temporal and Attendance Fields

| Field Name | Data Type | Allowed Values / Range | Business Definition | Source System (Production) | Transformation Notes |
| --- | --- | --- | --- | --- | --- |
| `week_start_date` | date | ISO 8601 (YYYY-MM-DD), Monday | First day of the working week to which this record applies. All records for the same employee in the same week share this value. | Source timesheet / calendar | Parsed from Excel date columns or DOCX form text. Normalized to ISO 8601 string. Validated: must be a Monday in production convention. |
| `week_end_date` | date | ISO 8601 (YYYY-MM-DD), Friday | Last day of the working week. Forms the upper bound of the weekly window. | Source timesheet / calendar | Parsed and normalized to ISO 8601. Validated: must be exactly 4 days after `week_start_date`. |
| `standard_days` | float | Typically 5.0; values 1.0–5.0 for part-time | Contractual number of working days in the week as defined by the employee's employment agreement. | HRIS (contract calendar) | Read from source or defaulted to 5.0 if absent. **[POC: simulated]** — fixed at 5.0 for all records in the sample dataset. |
| `holiday_days` | float | 0.0 – 5.0 | Number of public / bank holiday days falling within the week that reduce the employee's working obligation. | Calendar system (corporate holiday calendar) | Read from source. Validated: `holiday_days + pto_days + sick_days <= standard_days`. **[POC: simulated]** — populated from sample data. |
| `pto_days` | float | 0.0 – 5.0 | Number of approved paid time-off days taken in the week. Reduces `actual_working_days`. | HR leave management system (e.g. Workday Absence) | Read from source. Editable by employee in the Employee Review screen. |
| `sick_days` | float | 0.0 – 5.0 | Number of sick leave days recorded in the week. Reduces `actual_working_days`. | HR leave management system | Read from source. Editable by employee in the Employee Review screen. |
| `actual_working_days` | float | 0.0 – 5.0 | Net working days available in the week after deducting holiday, PTO, and sick leave. Used to validate total hours and anchor expected CapEx/OpEx splits. Computed as: `standard_days - holiday_days - pto_days - sick_days`. | **[POC: derived]** | Computed during normalization. Not stored as a separate column in the POC SQLite model; re-derived at query time. |

### 1.3 Observable Signal Fields

Observable signals are soft evidence inputs to the Classification Agent. In the POC they are simulated or sourced from the sample Excel dataset. In production each field would be populated from the listed source system via the Data Harvesting Agent.

| Field Name | Data Type | Allowed Values / Range | Business Definition | Source System (Production) | Transformation Notes |
| --- | --- | --- | --- | --- | --- |
| `meeting_count` | integer | >= 0 | Number of calendar meetings attended during the week. Higher counts correlate with coordination, project management, and architecture activity types. | Calendar / Microsoft Outlook (Graph API) | Validated as a non-negative integer. **[POC: simulated]** from the sample dataset. |
| `ticket_count` | integer | >= 0 | Number of Jira or ServiceNow tickets worked on during the week. Higher counts correlate with development, testing, and incident/support activity types. | Jira / ServiceNow | Validated as a non-negative integer. **[POC: simulated]** from the sample dataset. |
| `email_volume` | string | `Low` / `Medium` / `High` | Categorical email activity level for the week, derived from Exchange analytics. Used as a supporting signal for coordination-heavy activity types. | Microsoft Exchange (Exchange Online analytics) | Validated against the enumeration. Case-normalized on ingestion. **[POC: simulated]** from the sample dataset. |
| `code_commit_count` | integer | >= 0 | Number of code commits pushed during the week across linked repositories. Strong positive signal for Development & Engineering CapEx classification. | GitHub / Azure DevOps | Validated as a non-negative integer. **[POC: simulated]** from the sample dataset. |
| `system_activity_score` | float | 0.0 – 100.0 | Composite system-activity score derived from endpoint telemetry (keyboard activity, application usage, VPN time). Acts as a general productivity signal. Higher scores support confidence in billable-hours claims. | Endpoint telemetry / DEM platform (e.g. Nexthink, Lakeside) | Normalized to float in [0, 100]. **[POC: simulated]** from the sample dataset. |

### 1.4 Project and Activity Fields

| Field Name | Data Type | Allowed Values / Range | Business Definition | Source System (Production) | Transformation Notes |
| --- | --- | --- | --- | --- | --- |
| `project_code` | string | Alphanumeric project code | Unique code identifying the capital project or operational programme to which the employee's hours are allocated. Must exist in the Project Code Registry. | Project Registry / PPM tool (e.g. ServiceNow PPM, Planview) | Validated against the project registry lookup. Records with unknown codes are flagged with lower confidence. |
| `project_name` | string | Free text | Human-readable name of the project associated with `project_code`. Used for display and for evidence generation in the Classification Agent. | Project Registry / PPM tool | Joined from the project registry at normalization time. If not found, carried through from the source file. |
| `activity_type` | string enum | `Development & Engineering` / `Business Analysis` / `Testing & QA` / `Meetings & Coordination` / `Incident & Support` / `Documentation` / `Architecture & Design` / `Project Management` | The type of work performed during the week on the stated project. This is the primary input to the CapEx/OpEx classification ruleset. Each value maps to a deterministic classification path through the Policy & Rules Agent. | Employee self-report (timesheet / DOCX form) | Validated against the enumeration. DOCX forms use fuzzy matching if the employee's free-text entry does not exactly match an enum value. Unrecognized values trigger a `review` routing state. |
| `hours_allocated` | float | >= 0.0 | Total hours the employee worked on this project code and activity type during the week. The sum of `hours_allocated` across all records for the same employee-week should not exceed `actual_working_days * 8`. | Employee self-report (timesheet / DOCX form) | Validated as non-negative. Hours-vs-days consistency check is applied during normalization; failures lower confidence. |
| `submission_notes` | string | Free text or null | Optional free-text note provided by the employee at submission time. Used by the Classification Agent as additional evidence context and surfaced in the audit trail. | Employee self-report | May be null or empty. Not validated beyond length trimming. Stored verbatim. |

---

## 2. Project Code Registry

The Project Code Registry is a lookup table that maps project codes to project attributes used by the classification engine. In the POC the registry is embedded in the Excel source file. In production it would be maintained in a PPM or project accounting tool.

| Field Name | Data Type | Allowed Values / Range | Business Definition | Source System (Production) | Transformation Notes |
| --- | --- | --- | --- | --- | --- |
| `project_code` | string | Alphanumeric, unique per project | Primary key of the registry. Every `project_code` referenced in an Employee Activity Record must have a corresponding entry here. | Project Registry / PPM tool | Used as the join key during normalization. Missing codes are flagged and reduce classification confidence. |
| `project_name` | string | Free text, non-empty | Human-readable name of the project. Joined onto activity records at normalization time. | Project Registry / PPM tool | Carried through to the classification context bundle and displayed in the UI. |
| `is_capital_project` | boolean | `true` / `false` | Flags whether the project has been approved as a capital investment project. The Policy & Rules Agent uses this flag as the primary deterministic CapEx gate: hours on a capital project with a CapEx activity type classify as CapEx. | Project Registry / Finance / accounting rules | **[POC: simulated]** — inferred from project code patterns in the sample data. In production this is a governed field set by the Finance team. |
| `project_status` | string | Active / Closed / Pending | Lifecycle status of the project. Closed projects do not accept new hours; records against closed projects are flagged in row quality. | Project Registry / PPM tool | **[POC: simulated]** — all sample projects treated as Active. |
| `cost_center_code` | string | Alphanumeric | Cost centre to which the project belongs. Used for the cost-centre roll-up in the Reconciliation Report when an employee's `org_unit` does not directly map to a cost centre. | Project Registry / Finance system | **[POC: simulated]** — not explicitly modeled as a separate column in the POC schema. |

---

## 3. Classification Output Record

Classification output fields are prefixed with `_` to distinguish them from source payload fields. They are produced by the agentic pipeline and stored alongside the canonical activity record in the `ActivityRecord` persistence entity.

### 3.1 Primary Classification Fields

| Field Name | Data Type | Allowed Values / Range | Business Definition | Source System (Production) | Transformation Notes |
| --- | --- | --- | --- | --- | --- |
| `_classification` | string enum | `CapEx` / `OpEx` / `Review` | The system's primary classification decision for this record. `CapEx` means the hours are eligible for capitalization under the applicable fixed-asset accounting policy. `OpEx` means the hours are treated as operating expense. `Review` means the system could not make a confident determination and the record requires human resolution. | Classification Agent (LangGraph pipeline) | Set by the Classification Agent. Never null after pipeline completion. Overridable by a team lead via the Review Queue. |
| `_confidence` | integer | 0 – 100 | Confidence score for the `_classification` decision on a 0–100 scale. Scores below the routing threshold (default: 70) trigger `_routingState = review`. Scores at or above the threshold trigger `_routingState = approved`. | Classification Agent | Computed from weighted signal inputs and rule-match strength. Stored as an integer percentage. |
| `_evidence` | string | Non-empty human-readable text | Human-readable narrative explaining the classification decision. Lists which rules fired, which signals were decisive, and the reasoning chain. Surfaced verbatim in the Audit Trail and the Activity Records expansion panel. | Classification Agent | Generated by the Classification Agent. In the POC, constructed as a deterministic template string. In production, may be enriched by an LLM summary. |
| `_signals` | array of objects | Each object: `{ label: string, impact: string, kind: string }` | Structured list of evidence signals that contributed to the classification. Each signal has a human-readable label (e.g. "code_commit_count: 12"), an impact qualifier (e.g. "Strong Positive", "Weak Negative"), and a kind tag (e.g. "activity", "project", "signal"). | Classification Agent | Serialized as a JSON array. Rendered as a signal-badge list in the UI audit view. |
| `_ruleVersion` | string | Semver string (e.g. "1.0.0") | Version identifier of the classification ruleset that was applied. Enables replay comparison when rules change between runs. | Rules Engine | Set at pipeline initialization from the active rule configuration. Stored per-record. |
| `_persona` | string | Free text | Describes the classification "persona" or reasoning mode used (e.g. "policy-led deterministic", "hybrid with LLM context"). Supports governance review of which classification strategy was applied. | Classification Agent | Set by the Classification Agent based on pipeline configuration. |

### 3.2 Routing and Override Fields

| Field Name | Data Type | Allowed Values / Range | Business Definition | Source System (Production) | Transformation Notes |
| --- | --- | --- | --- | --- | --- |
| `_routingState` | string enum | `approved` / `review` | Determines which output channel the record enters. `approved` records flow to the Employee Timesheet Draft queue. `review` records flow to the Team Lead Escalation queue. | Confidence & Routing Agent | Set by the Confidence & Routing Agent based on `_confidence` vs. the routing threshold. Can be promoted to `approved` by a team-lead override. |
| `_override` | string enum or null | `CapEx` / `OpEx` / `Review` / `null` | Team-lead or admin manual override of the system classification. When non-null, this value is the effective classification used for reporting, superseding `_classification`. | Team lead via Review Queue UI (stored in `ActivityRecord`) | Set via `POST /api/records/{record_uid}/override`. An audit event is created on every override write. |
| `_overrideNote` | string or null | Free text or null | Optional justification note provided by the team lead when setting `_override`. Stored verbatim and displayed in the audit trail. | Team lead via Review Queue UI | May be null. No content validation beyond trimming. |

### 3.3 Normalization and Extraction Provenance Fields

| Field Name | Data Type | Allowed Values / Range | Business Definition | Source System (Production) | Transformation Notes |
| --- | --- | --- | --- | --- | --- |
| `_normalizedAt` | string | ISO 8601 datetime (UTC) | Timestamp when this record was normalized by the connector layer. Records the point at which the raw source payload was converted to the canonical schema. | Connector layer | Set by the connector at normalization time using UTC clock. |
| `_extractionConfidence` | float | 0.0 – 100.0 | Confidence score for the extraction step (primarily meaningful for DOCX connector). Reflects how reliably the connector parsed the source document. Low extraction confidence (<70) causes the record to be quarantined or routed to review. | DOCX Connector | Computed by the DOCX parser based on required-field presence and parse quality. Excel connector records default to 100.0. **[POC: simulated]** for Excel-sourced records. |
| `_matchedExcel` | integer | `0` / `1` | Flag indicating whether this DOCX-sourced record was successfully matched against a corresponding Excel dataset record using the stable record key. `1` = matched; `0` = not matched. Used in Form Extraction Validation. | DOCX Connector / FlowOrchestrator | Set during the post-classification Excel-match pass in the FlowOrchestrator. Only meaningful for DOCX-sourced records. |

### 3.4 Row Quality Fields

| Field Name | Data Type | Allowed Values / Range | Business Definition | Source System (Production) | Transformation Notes |
| --- | --- | --- | --- | --- | --- |
| `_rowQuality.status` | string | `ok` / `warning` / `error` | Overall quality status of the row after connector-level validation. `ok` = passed all checks. `warning` = passed but with non-fatal issues. `error` = failed validation and quarantined. | Connector validation layer | Set during normalization. Records with `error` status are not sent to the classification pipeline; they are stored as quarantined with a `review` routing state. |
| `_rowQuality.issues` | array of strings | Free-text issue descriptions | List of specific validation issues found during normalization (e.g. "hours_allocated exceeds actual_working_days * 8", "unknown project_code"). Each entry corresponds to one failing check. | Connector validation layer | Populated by the connector's validation pass. May be empty for `ok` records. Displayed in the Audit Trail and Activity Records expansion. |
| `_source` | string enum | `Excel` / `DOCX form` | Identifies the source file type from which this record was extracted. | Connector layer | Set by the connector. Stored as a top-level metadata field on the record payload. |
| `_sourceFileName` | string | File name with extension | Name of the source file from which this record was extracted (e.g. "EAC_Dataset_Week22.xlsx"). Supports provenance tracking. | Connector layer | Set by the connector from the uploaded file name. |
| `_sourceRecordId` | string | Connector-generated ID | Connector-assigned identifier for the raw source row or form (e.g. row index, DOCX file name). Used for deduplication and audit linkage. | Connector layer | Set by each connector using its own ID scheme. Combined with `employee_id`, `week_start_date`, `project_code`, and `activity_type` to form the stable `_key`. |
| `_key` | string | Non-empty stable string | Stable deduplication and audit-linkage key derived from `employee_id + week_start_date + project_code + activity_type`. Consistent across runs and connectors, enabling DOCX-to-Excel matching and replay comparison. | **[POC: derived]** | Computed by the connector at normalization time using a deterministic hash or concatenation of the four identity dimensions. |

---

## 4. Reconciliation Report Schema

The Reconciliation Report is produced by the Reconciliation & Reporting Agent after classification is complete. It aggregates approved records by cost centre and computes the CapEx/OpEx split for Finance reporting.

### 4.1 Cost-Centre Summary Row

| Field Name | Data Type | Allowed Values / Range | Business Definition | Source System (Production) | Transformation Notes |
| --- | --- | --- | --- | --- | --- |
| `cost_center` | string | Cost centre code or name | Identifier of the organizational cost centre for this summary row. Groups all employee activity records that belong to the same cost centre for the reporting period. | Derived from `org_unit` on activity records | Mapped from employee `org_unit` during aggregation. One summary row per distinct cost centre per run. |
| `employee_count` | integer | >= 1 | Total number of distinct employees with records in this cost centre for the reporting period. | **[POC: derived]** | Count of distinct `employee_id` values within the cost-centre group. |
| `completed_records` | integer | >= 0 | Number of records that have been reviewed and submitted (employee review status = submitted) within this cost centre. | **[POC: derived]** | Count of records with `_routingState = approved` and employee submission flag set. |
| `outstanding_records` | integer | >= 0 | Number of records still awaiting employee or team-lead review within this cost centre. | **[POC: derived]** | `total_records - completed_records`. |
| `total_hours` | float | >= 0.0 | Sum of `hours_allocated` across all records in this cost centre for the reporting period. | **[POC: derived]** | Aggregated at query time from classified records. |
| `capex_hours` | float | >= 0.0 | Sum of `hours_allocated` for all records with effective classification `CapEx` (considering overrides) in this cost centre. | **[POC: derived]** | Effective classification = `_override` if non-null, else `_classification`. |
| `opex_hours` | float | >= 0.0 | Sum of `hours_allocated` for all records with effective classification `OpEx` in this cost centre. | **[POC: derived]** | Same effective-classification logic as `capex_hours`. |
| `review_hours` | float | >= 0.0 | Sum of `hours_allocated` for all records with effective classification `Review` (pending human resolution) in this cost centre. | **[POC: derived]** | Represents unresolved hours that cannot yet be assigned to CapEx or OpEx. |
| `baseline_opex_hours` | float | >= 0.0 | Baseline total hours treated as OpEx before CapEx classification is applied. Always equals `total_hours`. Represents the pre-classification cost position used to compute the capitalisation delta. | **[POC: derived]** | Set equal to `total_hours` at aggregation time. |
| `capitalisation_delta_hours` | float | >= 0.0 | The number of hours reclassified from OpEx to CapEx by the system. Equals `capex_hours`. Represents the capitalisation opportunity identified by the EAC engine. | **[POC: derived]** | `capitalisation_delta_hours = capex_hours`. |
| `capitalisation_pct` | float | 0.0 – 100.0 | Percentage of total hours classified as CapEx. Computed as `(capex_hours / total_hours) * 100` where `total_hours > 0`. | **[POC: derived]** | Rounded to two decimal places. Zero when `total_hours = 0`. |
| `flagged_employee_count` | integer | >= 0 | Number of employees in this cost centre who have one or more records in `Review` routing state (low confidence or unresolved). Used to triage manual review workload. | **[POC: derived]** | Count of distinct `employee_id` values with at least one `_routingState = review` record. |

### 4.2 Employee-Level Drill-Down

The `employees` array within the reconciliation report contains one entry per employee for each cost centre. Each entry mirrors the cost-centre summary fields scoped to a single employee, enabling Finance reviewers to drill down from the cost-centre total to individual contributors.

| Field Name | Data Type | Allowed Values / Range | Business Definition | Source System (Production) | Transformation Notes |
| --- | --- | --- | --- | --- | --- |
| `employee_id` | string | Non-empty | Employee identifier for this drill-down row. | Derived from activity records | Foreign key to the Employee Activity Record. |
| `full_name` | string | Non-empty | Display name for this employee in the reconciliation report. | Derived from activity records | Carried through from the canonical record. |
| `job_title` | string | Free text or empty | Current role designation of the employee. Surfaced in the reconciliation drill-down to enable grouping by job function within a cost centre. | HRIS (via activity record payload) | Carried through from `job_title` on the canonical activity record. Empty string if not present in source. |
| `total_hours` | float | >= 0.0 | Total hours allocated by this employee in this cost centre for the period. | **[POC: derived]** | Sum of `hours_allocated` for this employee within the cost-centre group. |
| `capex_hours` | float | >= 0.0 | Hours classified as CapEx for this employee. | **[POC: derived]** | Aggregated using effective classification (`_override` if non-null, else `_classification`). |
| `opex_hours` | float | >= 0.0 | Hours classified as OpEx for this employee. | **[POC: derived]** | Aggregated using effective classification. |
| `review_hours` | float | >= 0.0 | Hours pending review for this employee — not yet resolved to CapEx or OpEx. Equals `total_hours - capex_hours - opex_hours`. | **[POC: derived]** | Aggregated using effective classification. Ensures `capex_hours + opex_hours + review_hours = total_hours` for full accounting integrity. |
| `capex_pct` | float | 0.0 – 100.0 | Percentage of this employee's total hours classified as CapEx. | **[POC: derived]** | `(capex_hours / total_hours) * 100`. Zero when `total_hours = 0`. |
| `delta_hours` | float | >= 0.0 | Capitalisation recovery in hours for this employee vs 100% OpEx baseline. Equals `capex_hours`. | **[POC: derived]** | `delta_hours = capex_hours`. Multiply by the standard cost rate to estimate USD recovery contribution. |
| `record_count` | integer | >= 1 | Total number of activity records for this employee in this cost centre for the period. | **[POC: derived]** | Count of distinct activity records grouped by `employee_id` within the cost-centre. |
| `flagged` | boolean | `true` / `false` | Indicates whether this employee has one or more records in the escalation / review routing state. `true` = at least one record with `_routingState = review`. | **[POC: derived]** | Set to `true` if any of the employee's records in this cost centre have `routing != approved`. Surfaces in the Finance report as a targeted review marker. |

---

## 5. Connector Interface Contract

The Connector Interface Contract defines the standard data structure that every source connector must produce before records enter the classification pipeline. All connectors — regardless of source type — must conform to this contract. It is enforced by the FlowOrchestrator before records are passed to the Data Harvesting Agent.

| Field Name | Data Type | Allowed Values / Range | Business Definition | Source System (Production) | Transformation Notes |
| --- | --- | --- | --- | --- | --- |
| `source_type` | string | `Excel` / `DOCX form` / future connector names | Identifies the type of source connector that produced this record. Used for provenance tracking and connector-specific post-processing (e.g. Excel-match pass for DOCX records). | Connector layer | Set by each connector implementation as a class-level constant. Stored as `_source` on the output record. |
| `source_file_name` | string | Non-empty file name | Name of the source file from which this record was extracted. Supports audit trail and run-manifest generation. | Connector layer | Set by each connector from the upload context. Stored as `_sourceFileName` on the output record. |
| `source_record_id` | string | Non-empty connector-assigned ID | Connector-specific identifier for the individual row or form parsed (e.g. Excel row index, DOCX file name within a ZIP). Used to trace each output record back to its precise source location. | Connector layer | Set by each connector. Stored as `_sourceRecordId` on the output record. Used in combination with other fields to compute `_key`. |
| `key` | string | Non-empty stable dedup key | Stable deduplication key derived from `employee_id + week_start_date + project_code + activity_type`. Must be consistent across re-runs of the same source data to support deduplication and DOCX-to-Excel matching. | **[POC: derived]** by the connector | Computed by the connector at normalization time. Must use the same derivation formula across all connectors. Stored as `_key` on the output record. |
| `raw_payload` | dict (JSON object) | All source-specific raw fields | The unmodified raw field values extracted from the source, before normalization or transformation. Stored verbatim for full audit reproducibility. Allows re-normalization if the canonical schema changes. | Connector layer | Captured before any transformation is applied. Stored inside the `ActivityRecord` payload JSON under a `_raw` envelope. |
| `normalized_record` | object (NormalizedActivityRecord) | All canonical activity record fields | The fully normalized canonical record conforming to the Employee Activity Record schema defined in Section 1. This is the object passed into the agentic pipeline. | **[POC: produced]** by the connector | All field-level normalization (type coercion, date parsing, enum validation, whitespace trimming) is applied by the connector before this object is constructed. The FlowOrchestrator validates that required fields are present before pipeline dispatch. |
| `extraction_confidence` | float | 0.0 – 100.0 | Confidence score for the extraction step. For the DOCX Connector, reflects how reliably the parser could populate required fields from the form document. For the Excel Connector, defaults to 100.0 (structured source). Records with extraction confidence below the configured floor (default: 70.0) are quarantined before classification. | DOCX Connector / Excel Connector | Stored as `_extractionConfidence` on the output record. Thresholded by the FlowOrchestrator before pipeline dispatch. |
| `row_quality.status` | string | `ok` / `warning` / `error` | Overall row-level quality status assigned by the connector's validation pass. Mirrors the `_rowQuality.status` field on the output record. | Connector validation layer | Set by each connector's `validate()` method. Records with `error` status are not dispatched to the pipeline; they are quarantined with a classification of `Review` and a `review` routing state. |
| `row_quality.issues` | array of strings | Free-text issue descriptions | List of specific validation failures or warnings found during connector-level validation. Populated alongside `row_quality.status`. | Connector validation layer | Stored as `_rowQuality.issues` on the output record. May be empty for `ok` records. Used in the Audit Trail and Data Sources / Form Extraction Validation UI. |
| `row_quality.repairs` | array of strings or null | Free-text repair descriptions or null | Optional list of automatic repairs applied by the connector (e.g. "Defaulted standard_days to 5.0", "Trimmed whitespace from project_code"). Supports transparency about connector-side data quality corrections. | Connector validation layer | **[POC: partially implemented]** — the DOCX connector logs some repairs; the Excel connector does not currently expose this field. Stored as `_rowQuality.repairs` on the output record when present. |

---

## Appendix: Field-to-Screen Mapping

The table below summarises which screens in the EAC portal surface each major field group.

| Field Group | Overview | Activity Records | Review Queue | Employee Review | Employee Directory | Analytics | Audit Trail | Data Sources |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Employee identity | summary | expanded | expanded | primary | primary | grouped | trace | — |
| Temporal / attendance | summary | expanded | expanded | editable | read | week bars | trace | — |
| Observable signals | — | expanded | expanded | — | — | — | trace / signals | — |
| Project & activity | project chart | primary | primary | editable | read | project chart | trace | — |
| Classification output | totals | primary | primary | read | read | KPIs | primary | pipeline |
| Override / routing | — | override control | override control | — | — | — | events | — |
| Row quality | — | badge | badge | — | — | — | issues | form validation |
| Reconciliation | CapEx delta | — | — | — | — | stacked bars | — | — |
