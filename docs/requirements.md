# Employee Activity Classification System

**AI-Enabled CapEx / OpEx Activity Classification System — Use Case 2: Project Coder Weekly Timesheet**

## 1. Executive Summary

This document defines the complete business and technical requirements for an AI-enabled Employee Activity Classification System, scoped to Use Case 2: Project Coder Weekly Timesheet Pre-Population. The system automatically classifies employee work activities as Capital Expenditure (CapEx) or Operating Expense (OpEx) by ingesting observable digital workplace signals, applying fixed asset accounting rules, and producing pre-populated weekly timesheet drafts that are auditable, defensible, and ready for employee review-and-confirm.

The financial opportunity this system addresses is measured in hundreds of millions of dollars annually. Significant portions of the engineering and software development workforce manually reconstruct a week of work from memory each Friday — assigning hours to project codes that carry CapEx or OpEx designations. Accuracy degrades with every hour of delay between the work and the entry. The system recovers this capitalisation opportunity by replacing the recall-and-categorise task with a review-and-confirm workflow.

The system is architected around three principles confirmed by the sponsoring organisation: (1) engine-first and source-agnostic — the classification engine is the primary deliverable; data connectors are pluggable inputs; (2) overnight batch processing — signals are collected during the day and classified in a nightly run, producing a pre-populated timesheet draft available each morning; and (3) 80% one-size-fits-all coverage — the engine handles the dominant project-coder persona patterns generically, with edge-case handling addressed in later iterations.

For the purposes of this assessment, two synthetic data inputs are provided. The first is a set of 10 raw weekly timesheet entry documents (.docx format) provided in sample_timesheets.zip — candidates must ingest and parse these to extract structured activity and project code data, testing the ingestion pipeline capability. The second is a full synthetic employee activity dataset (EAC_Timesheet_Dataset.xlsx) containing complete weekly activity records that candidates use for the full classification workflow. The 10 raw timesheet entries correspond to 10 rows in the dataset — candidates should validate their parser output against these rows. All other data contexts (HR profiles, project code registries, accounting rules) may be simulated.

## 2. Business Context and Problem Statement

### 2.1 The Core Business Problem

Large enterprises with significant technology and engineering workforces are required to classify employee labor activities as either capital expenditure or operating expense. Correct classification directly affects financial reporting, tax treatment, balance sheet strength, and regulatory compliance. Misclassification — specifically, treating capitalizable labor as operating expense — results in the permanent loss of capitalisation opportunity that cannot be retroactively recovered.

The classification process for project-coding employees today relies on the following mechanism, with significant deficiencies:

Weekly timesheets: Employees manually assign work hours to project codes mapped to CapEx or OpEx categories. Accuracy degrades when entry is delayed — employees reconstructing work done days prior. Compliance is inconsistent. Cognitive burden is high. Many employees fill timesheets as rough estimates, particularly on weeks with complex project switching or unplanned work.

### 2.2 The Opportunity

Observable digital workplace data — calendar events, meeting participation, project tickets, task completions, code commits, system activity logs — provides a near-complete record of what employees do each week. This data, combined with HR job profile data, project and investment case context, and fixed asset accounting rules, is sufficient to infer weekly time allocation across project codes with high confidence for the majority of project-coding employees.

An AI-enabled classification engine can pre-populate timesheet entries for weekly project coders, reducing their effort to a review-and-confirm task. The target experience: an employee opens their timesheet and finds a pre-populated draft — hours already allocated across project codes and activity types based on observable signals from the previous week. They review, adjust if needed, and submit. Effort is under five minutes.

### 2.3 Current State Inventory

| **Mechanism** | **Employee Population** | **Current Pain** | **System Impact** |
| --- | --- | --- | --- |
| Weekly timesheets | Software engineers, product developers, and IT professionals across all organisational functions | Weekly recall unreliable; accuracy degrades with delay; compliance inconsistent; cognitive burden high | Pre-populate timesheet draft from week of observable activity signals; reduce effort to review-and-confirm |
| No classification (100% OpEx default) | 21,000+ employees booking all time to operating expense regardless of actual activity | Capitalizable labor permanently lost; growing population as builder culture expands across functions | Automatically classify and surface capitalizable activities for this population |

## 3. Business Objectives

**[BO-01]** Classify employee work activities as CapEx or OpEx using AI inference over observable digital workplace signals, with no manual reconstruction required from employees.

**[BO-02]** Reduce employee cognitive burden for activity reporting to a review-and-confirm interaction rather than a recall-and-categorise task.

**[BO-03]** Pre-populate weekly timesheet entries for project-coding employee populations with AI-generated classifications derived from their observable activity signals.

**[BO-04]** Identify and classify capitalizable activities performed by the untracked employee population (currently booking 100% OpEx) and surface these for recognition.

**[BO-05]** Produce a measurable and trackable capitalisation shift metric — quantifying the movement of labor from OpEx to CapEx classification over time.

**[BO-06]** Build a classification engine that is source-agnostic and extensible — capable of serving additional employee populations, job families, and reporting cadences without architectural rebuilds.

**[BO-07]** Ensure all classifications are auditable, traceable to specific observable signals, and defensible against accounting and regulatory scrutiny.

## 4. Success Metrics

### 4.1 POC Success Criteria

The prototype is considered successful if it demonstrates the end-to-end classification pipeline functioning on the weekly timesheet use case, with human-review output that a domain expert can evaluate for accuracy and defensibility. The prototype does not need to be production-complete — it must be experience-ready and architecturally sound.

| **Metric** | **POC Target** | **Measurement Method** |
| --- | --- | --- |
| End-to-end pipeline | Functional: ingest → classify → weekly timesheet output | Demo on Project Coder weekly timesheet use case |
| Raw timesheet data extraction | 10 timesheet records extracted and schema-mapped; match validated against dataset rows | Parser output vs. dataset row comparison |
| Classification accuracy | ≥ 70% agreement with domain expert review on test set | Manual review by domain expert / evaluator team |
| Confidence scoring | Every record carries a confidence score | System output inspection |
| Human review flow | Corrections captured and visible | UI walkthrough |
| Auditability | Each classification traceable to specific signals | Output report review |
| Capitalisation shift metric | Baseline vs. classified delta visible | Output dashboard or report |
| Batch run architecture | Described in document; on-demand execution acceptable for POC | Architecture document review |

## 5. Scope Definition — Required for POC

| **Capability Area** | **Required** |
| --- | --- |
| Classification engine | Functional engine producing CapEx/OpEx output with confidence scores and evidence notes |
| Use case coverage | At minimum: Project Coder Weekly Timesheet use case |
| Raw timesheet data extraction pipeline | 10 raw timesheet documents parsed; structured records extracted and schema-mapped; validation against corresponding dataset rows demonstrated or documented |
| Synthetic activity dataset ingestion | Full synthetic dataset ingested and processed through the classification workflow |
| Agent architecture | Orchestrator, Data Harvesting, Context Builder, Classification, Policy/Rules, Confidence/Routing — functional pipeline; agents may be stubs |
| Human review interface | Per-employee weekly timesheet draft with confidence indicators and evidence trail |
| Capitalisation shift metric | Baseline vs. post-classification delta surfaced in output |
| Timesheet pre-population | Weekly hours distributed across project codes and activity types with CapEx/OpEx designation per line item |
| Connector framework | Two functional connectors (synthetic dataset + raw timesheet parser); pluggable interface documented; "Coming Soon" panel in UI |
| Persona coverage | Software engineering / project-coder persona |
| Value tracking output | Per-employee and aggregate CapEx reclassification amount visible |
| Audit trail stub | Audit trail panel in UI — input signals, rule version, confidence, output, overrides |
| Architecture diagram | Impeccable, fully labelled system diagram submitted with Architecture Document |

## 6. Functional Requirements

Requirements marked [REQ-xx] are mandatory for this assessment. Architecture must accommodate future-state capabilities without a rebuild, but only [REQ-xx] items are required deliverables.

### FR-1: Classification Engine

The classification engine is the primary deliverable of this system. All other components exist to serve it. It must be built first and treated as source-agnostic — its inputs are structured records from the data layer, not raw connector outputs.

**[REQ-01]** The engine SHALL accept as input a structured per-employee activity record containing: observable signals (meeting count, ticket count, email frequency, system activity, code commits), HR context (job title, job family, organisation), project and investment case context (project codes, funding category, CapEx/OpEx designation per project), and a time window (7-day rolling week).

**[REQ-02]** The engine SHALL apply fixed asset accounting rules to each activity record and classify it as: (a) clearly CapEx, (b) clearly OpEx, or (c) ambiguous/gray-area requiring human review.

**[REQ-03]** The engine SHALL produce a confidence score (0–100) for every classification. Low confidence SHALL trigger routing to the human review queue, not direct output to the employee.

**[REQ-04]** The engine SHALL produce an evidence trail for every classification — citing the specific observable signals that drove the classification decision. This trail must be human-readable and must accompany every output record.

**[REQ-05]** The engine SHALL operate in Weekly mode for this assessment — distributing employee activity hours across project codes and activity types (e.g., detailed design, build, requirements, admin) for a rolling 7-day context window. Each activity block is tagged CapEx or OpEx per the associated project code designation. On-demand execution triggered by dataset upload is acceptable for the POC in lieu of scheduled nightly runs.

**[REQ-06]** The engine SHALL be designed as a nightly batch process. For the POC, on-demand execution triggered by data upload is acceptable. The architecture must support transition to scheduled overnight runs without redesign.

**[REQ-07]** The engine SHALL be source-agnostic. It consumes structured records from the data layer and SHALL NOT contain any connector-specific logic.

**[REQ-08]** The engine SHALL be configurable by persona. Persona configuration controls: output mode (Weekly for this assessment), aggregation window (7-day), activity-to-project-code mapping, confidence thresholds, and applicable accounting rule set — without modifying engine code.

### FR-2: Data Ingestion and Hydration Layer

The data layer collects, normalises, and structures signals from approved sources into the unified record format consumed by the classification engine. It operates independently of the engine and must be designed as a pluggable connector framework.

Two active connectors are required for this assessment: the synthetic activity dataset connector (full workflow data) and the raw timesheet document parsing connector (ingestion capability test). All other data sources — HR job profiles, project code registries, accounting rules, historical timesheet data — may be simulated for the POC.

**Stubbed data:** HR profiles, project code registries, accounting rules, and historical timesheet data may be simulated. Clearly document what is stubbed and how the system would ingest real equivalents.

**[REQ-09]** The data layer SHALL implement a synthetic employee activity dataset connector as the primary full-dataset input. The connector must ingest the provided EAC_Timesheet_Dataset.xlsx, validate all records against the standard schema, and stage clean records for the classification pipeline. The Excel connector is the reference connector implementation that all future connectors must conform to.

**[REQ-10]** The data layer SHALL implement a raw timesheet document parsing connector capable of extracting structured data fields from the provided raw weekly timesheet documents (.docx format). Each document contains activity records across project codes, activity types, and time allocations embedded in narrative or semi-structured format. The parser must identify and extract each field, map extracted values to the standard schema, and produce validated records in the same format as the synthetic dataset connector output. The 10 extracted records must be validated against the corresponding rows in EAC_Timesheet_Dataset.xlsx.

**[REQ-11]** The data layer SHALL support historical timesheet and classification data as labeled reference input for model calibration. For the POC, this may be simulated as a representative dataset with known CapEx/OpEx splits per activity type and project code.

**[REQ-12]** The data layer SHALL support HR job profile data (job title, job family, job description, org unit). For the POC, this may be simulated. The connector interface must be defined even if the data is mocked.

**[REQ-13]** The data layer SHALL ingest project and investment case context: project codes, funding categories, and CapEx/OpEx designation per project code. This is the authoritative mapping that ties each activity to a capital or expense classification. For the POC, this may be provided as a simulated static project code registry.

**[REQ-14]** The data layer SHALL ingest fixed asset accounting rules as a static context document. These rules SHALL be versioned and replaceable without engine changes.

**[REQ-15]** Each connector SHALL produce output in a standardised, schema-validated record format. The connector-to-engine interface SHALL be formally defined and documented as the extensibility contract for all future connectors.

**[REQ-16]** The data layer SHALL support a hydration frequency of at least daily — refreshing data stores at least once per 24-hour period in advance of the nightly batch run.

### FR-3: Agent Architecture

The system is implemented as an orchestrated multi-agent pipeline. Each agent has a defined responsibility, a defined interface with the orchestrator, and behavioral parameters configurable by persona. The agent taxonomy is shared across all use cases; behavior adapts to persona without architectural changes.

**[REQ-17]** The system SHALL implement a Flow Orchestrator that coordinates the nightly batch pipeline, manages agent sequencing, handles failures with retry logic, and produces a run manifest (inputs processed, outputs produced, errors encountered).

**[REQ-18]** The system SHALL implement a Data Harvesting Agent responsible for triggering connector refresh across both active connectors, validating ingested records against schema, and staging clean records for downstream agents.

**[REQ-19]** The system SHALL implement a Context Building Agent that constructs a per-employee context record for a given 7-day window: a daily-segmented activity digest showing meeting participation, ticket activity, system events, and project code context, summed to weekly totals.

**[REQ-20]** The system SHALL implement a Classification Agent — the core engine — that applies accounting rules and persona configuration to each context record and produces a classified output with confidence score and evidence trail. In Weekly mode, output is hours distributed across project codes and activity types.

**[REQ-21]** The system SHALL implement a Policy and Rules Agent that overlays fixed asset accounting rules, project code constraints, and persona-specific classification rules on top of the base classification. This agent is the authoritative enforcer of accounting policy within the pipeline.

**[REQ-22]** The system SHALL implement a Confidence and Routing Agent that evaluates each classified record against configured confidence thresholds and routes: (a) high-confidence records to the output queue for employee review; (b) low-confidence records to the human escalation queue — routed to domain team leads, NOT directly to individual employees.

### FR-4: Output and Reporting

System outputs must be actionable, explainable, and tailored to the receiving employee population. All outputs are per-employee. Aggregate reporting is available for domain team leads and finance reviewers.

**[REQ-23]** The system SHALL produce a per-employee weekly timesheet output in Weekly mode: hours distributed across project codes and activity types (e.g., detailed design, build, requirements, admin), each tagged as CapEx or OpEx, with confidence score and evidence trail per line item.

**[REQ-24]** The system SHALL produce a capitalisation shift output: for each employee and in aggregate, the system SHALL show baseline (pre-classification, assumed 100% OpEx) vs. post-classification CapEx percentage — quantifying the financial recovery for the period.

**[REQ-25]** Every output record SHALL include an evidence trail citing the specific signals that drove the classification. The evidence trail must be human-readable without technical expertise.

**[REQ-26]** Low-confidence records SHALL appear in a separate escalation report delivered to domain team leads, not to individual employees. The escalation report SHALL include the record, the confidence score, and the specific signals that prevented high-confidence classification.

### FR-5: User Interface and Experience

The user interface is a review-and-confirm surface, not a data entry surface. The system produces the timesheet draft; the employee reviews, adjusts if needed, and confirms. The UX philosophy is: give employees a confident starting point, not a blank form.

The use of AI tools and capabilities for building the UI is not just permitted — it is expected. Candidates are encouraged to explore creative, visually compelling interface designs. Extra credit will be awarded for exceptional UX quality, dashboard creativity, and interface polish beyond the functional baseline.

**[REQ-27]** The UI SHALL present per-employee weekly timesheet draft in a clear, non-technical layout showing: (a) activity blocks by project code and activity type, (b) the CapEx/OpEx designation for each block, (c) the confidence level, and (d) the evidence behind the classification in plain language.

**[REQ-28]** The UI SHALL provide a correction mechanism: employees can override any classification, reassign an activity to a different project code or activity type, and submit the correction. Every correction is captured and logged.

**[REQ-29]** The UI SHALL support flexible cadence: employees can review their timesheet draft at any point during the week. The system retains the draft until the employee acts on it. No fixed submission schedule is enforced by the UI.

**[REQ-30]** The UI SHALL NOT surface low-confidence records to individual employees. Low-confidence records are handled through the escalation queue to domain leads only.

**[REQ-31]** The UI SHALL display aggregate capitalisation metrics: total hours classified as CapEx, total classified as OpEx, and the overall capitalisation percentage for the current period.

**[REQ-32]** Domain team lead escalation view: team leads SHALL have a separate view showing all low-confidence records for their team, with the ability to clarify, reclassify, and return resolved records to the output queue.

## 7. Use Case Specifications

### UC-2: Project Coder Weekly Timesheet Pre-Population [REQUIRED — Primary POC Target]

#### Description

Software engineers, product developers, and related project-coding employees are required to submit weekly timesheets assigning their work hours to specific project codes. Each project code carries a CapEx or OpEx designation. This population spans thousands of employees across engineering, technology, and product functions. Timesheet submission is typically weekly but often delayed, resulting in inaccurate retrospective reconstructions of how time was spent.

#### Why This Is the POC Priority

Synthetic labeled data available: the provided synthetic activity dataset and raw timesheet documents enable end-to-end pipeline testing without requiring live enterprise data.

Clear weekly cadence: the 7-day rolling window provides a natural scope boundary and a measurable output — does the pre-populated draft match what an expert would submit?

Immediate operational relevance: timesheet compliance and accuracy are recurring pain points for engineering managers across technology organisations.

Measurable capitalisation impact: project code CapEx/OpEx designations provide clear ground truth for evaluating classification accuracy.

#### User Journey

Current state: Employee opens timesheet on Friday (or later) and attempts to reconstruct the week from memory — assigning hours to project codes and activity types. Accuracy degrades with delay. Many employees provide rough estimates. Compliance to the weekly deadline is inconsistent.

Target state for POC: Employee opens their timesheet and finds a pre-populated draft — hours already allocated across project codes and activity types based on observable signals from the week. Employee reviews, adjusts if needed, and submits. Effort is under five minutes.

Future state: Timesheet is submitted automatically upon employee approval in a single click. Learning loop progressively reduces the need for manual adjustment as the model improves.

#### Data Inputs — UC-2

**REQUIRED**

EAC_Timesheet_Dataset.xlsx: complete synthetic employee activity dataset used for the full classification workflow.

sample_timesheets.zip: 10 raw weekly timesheet entry documents (.docx) — parsed and extracted to validate the timesheet ingestion pipeline; the extracted 10 records are validated against the corresponding rows in the activity dataset.

HR job profile data: job title, job family, organisation unit (simulated for POC).

Project code registry: project codes, funding categories, and CapEx/OpEx designation per project (simulated for POC).

Fixed asset accounting rules applicable to software development and engineering functions.

**Stubbed data:** All data contexts beyond the two provided files may be stubbed. Clearly document what is simulated and how the system would ingest real equivalents in production.

#### Output Format — UC-2

Per-employee: weekly hours distributed across project codes and activity types, each tagged CapEx or OpEx.

Per-employee: evidence summary citing the signal types and counts that drove each allocation.

Per-employee: confidence score per activity block.

Per-employee: overall weekly capitalisation percentage.

Aggregate: team-level weekly capitalisation shift (baseline vs. classified).

Escalation report: employees with low-confidence classifications requiring team lead review.

#### Engine Behavior — UC-2

Context window: rolling 7-day week; nightly batch produces updated draft for current week.

Aggregation mode: daily-segmented activity digest, summed to weekly totals per project code and activity type.

Output mode: hours distributed across project codes and activity types.

Training baseline: historical timesheet data (simulated) used to calibrate activity-to-project-code mappings.

## 8. Data Requirements

### 8.1 Data Architecture Principles

All data ingested by the system flows into a shared data store before it is consumed by the classification engine. The engine NEVER calls source APIs directly during a classification run. This design enables: (1) cost-effective overnight batch processing without rate-limit exposure, (2) historical replay and retraining, (3) connector-engine independence, and (4) unified schema enforcement.

### 8.2 Data Source Registry

For the POC, two data sources are active (synthetic dataset + raw timesheet documents). All others may be stubbed. The registry below represents the full intended data architecture — stubbed sources must still have a defined connector interface.

| **Source** | **Signal Type** | **Format / Access** | **POC Status** | **Classification Relevance** |
| --- | --- | --- | --- | --- |
| EAC_Timesheet_Dataset.xlsx | Full synthetic employee activity dataset — all fields per the standard schema | Excel (.xlsx) — provided with test materials | REQUIRED — Active | Primary full-volume data source for classification workflow |
| sample_timesheets.zip (10 documents) | Raw weekly timesheet entries — project codes, activity types, hours, and date ranges in narrative or semi-structured format | .docx documents — provided with test materials | REQUIRED — Active | Data extraction test; 10 extracted records validate against dataset rows |
| Historical timesheet / classification data | Labeled reference: known correct CapEx/OpEx splits per activity type and project code | Provided as simulated dataset within test materials | REQUIRED — Simulated | Ground truth for model calibration and validation |
| HR job profile data | Job title, job family, job description, org unit | Simulated / mocked data acceptable for POC | REQUIRED — Simulated | Critical context for persona-based activity weighting |
| Fixed asset accounting rules | Policy document: which activity types qualify as capital vs. expense | Static document — one-time injection, versioned | REQUIRED | Authoritative rules for classification decisions |
| Project code registry | Project codes, funding categories, CapEx/OpEx designation per project code | Simulated / mocked data acceptable for POC | REQUIRED — Simulated | Maps employee hours to specific capital investments per project |

### 8.3 Data Quality Requirements

**[REQ-33]** All ingested records — whether sourced from the synthetic dataset connector or the raw timesheet parsing connector — SHALL be validated against the standard connector schema before being staged for the classification engine. Invalid records are rejected, logged, and reported in the run manifest.

**[REQ-34]** The raw timesheet document parsing connector SHALL extract all structured data fields from each timesheet document — including project code references, activity type declarations, time allocations, and date ranges — and map them to the standard schema. All extracted fields must be present in the schema-validated output record.

**[REQ-35]** The system SHALL handle missing signals gracefully: if a data field is unavailable for a given employee record, the engine classifies using available signals with a proportionally reduced confidence score — it does not fail or skip the record.

**[REQ-36]** HR job profile data SHALL be refreshed at least weekly to reflect role changes, transfers, and promotions.

**[REQ-37]** Fixed asset accounting rules SHALL be versioned. Any rule change produces a new version; historical classifications retain the rule version that was active at the time of classification.

## 9. Architecture Principles

These principles are confirmed design constraints — not preferences. The prototype architecture must conform to all of them. Future iterations must extend, not contradict, these principles.

**AP-01: Engine-First, Source-Agnostic**

The classification engine is the primary deliverable. Its inputs are structured records from the data layer. It contains no connector-specific logic. Data source availability or unavailability does not block engine development. Connectors are pluggable inputs that can be added, swapped, or upgraded independently.

**AP-02: Overnight Batch as the Primary Processing Model**

Signals are collected throughout the day into the shared data store. The classification engine runs as a nightly batch process. Results are available by the following morning. This model is cost-effective, avoids live API rate limits, and supports historical replay. Real-time processing is a future-state capability — the architecture must support it without requiring the batch model to be abandoned.

**AP-03: 80% One-Size-Fits-All Coverage**

The engine handles the dominant employee persona patterns with a generic, configurable model. The target is ≥ 80% of the employee population classified without custom persona-specific logic. The remaining ≤ 20% is addressed in subsequent iterations through persona workshops and targeted rule additions.

**AP-04: Parameterizable Persona Configuration**

All persona-specific behavior is expressed as configuration, not code. Persona config controls: output mode (Weekly for this use case), aggregation window, activity-to-project-code mapping, confidence thresholds, and applicable rule set. Adding a new persona requires a new config file, not a code change.

**AP-05: Modular, Versioned Connector Framework**

Every data source is a versioned, independently deployable connector. The connector-to-data-layer interface is the system's primary extensibility contract. New connectors are onboarded by conforming to this interface — no engine or orchestrator changes required. The synthetic dataset connector and the raw timesheet parsing connector serve as the two reference implementations.

**AP-06: Human Accountability is Structurally Enforced**

Low-confidence classifications never reach employees directly. They are routed to domain team leads through a structured escalation queue. Accounting standards require human accountability — this is not a UX preference, it is a compliance requirement.

**AP-07: Defensibility by Design**

Every classification carries a traceable evidence trail. The system can explain, at any time, why a specific record was classified as it was — citing specific signals, their values, and the rules applied. This trail is immutable and retained for audit purposes.

**AP-08: Designed for Scale — Architecture Vision**

The architecture is built to serve an arbitrary number of stakeholder groups, each with different reporting cadences, job taxonomies, data sources, and accounting rule sets. The POC delivers for one use case. The architecture must support 30 without a rebuild.

## 10. Non-Functional Requirements

### NFR-1: Performance

**[REQ-38]** The nightly batch run SHALL complete within a 12-hour window for the POC employee population size.

**[REQ-39]** The UI SHALL load the per-employee weekly timesheet view in under a minute for a single employee record.

### NFR-2: Accuracy and Confidence

**[REQ-40]** The classification engine SHALL produce a confidence score for 100% of processed records. No record is output without a score.

**[REQ-41]** POC target: ≥ 70% of classifications confirmed correct by domain expert review on a representative test set.

**[REQ-42]** The raw timesheet parsing connector SHALL achieve ≥ 90% field extraction accuracy across the 10 provided documents, measured as extracted field values matching the corresponding ground-truth rows in EAC_Timesheet_Dataset.xlsx.

### NFR-3: Auditability and Traceability

Full production audit infrastructure is not required for the POC. The audit trail must be architecturally designed and represented in the UI as a visible stub — demonstrating that the capability exists and is planned, even if not fully operational for the assessment submission.

**[REQ-43]** Every classification SHALL have an immutable audit record: input signals, rule version, confidence score, output, and any human overrides.

**[REQ-44]** The system SHALL log every data access event: which employee record was accessed, by which component, at what time.

### NFR-4: Security and Access Control

**[REQ-45]** All data access operates under a scoped read-only permission model. No connector has write access to source systems.

**[REQ-46]** Employee classification data is accessible only to: (a) the employee themselves, (b) their authorised domain team lead, and (c) authorised finance reviewers. No cross-employee data exposure.

**[REQ-47]** All data in transit is encrypted. All data at rest in the shared data store is encrypted. (Exclude this rule for staged data outside of the client ecosystem.)

### NFR-5: Extensibility

**[REQ-48]** Adding a new data source connector SHALL require no changes to the classification engine, orchestrator, or agent logic. Additional agents can be added to pre-process data but the engine structure remains independent.

**[REQ-49]** Adding a new employee persona SHALL require only a new persona configuration file — no code changes.

**[REQ-50]** The fixed asset accounting rule set SHALL be updatable without a system deployment.

### NFR-6: Observability

**[REQ-51]** Every nightly batch run produces a run manifest: records processed (by source connector), classified, escalated, failed, and elapsed time per agent.

**[REQ-52]** The conflict rate (corrections as % of classifications) is tracked per run and surfaced in the system dashboard.

## 11. Constraints and Assumptions

### 11.1 Confirmed Constraints

First iteration covers full-time employees only. Vendors and contractors are explicitly out of scope.

The system must not contact individual employees directly for clarification. All employee-facing interaction is through the approved UI or mediated through domain team leads.

All data access requires explicit approval through the organisational data governance process.

Fixed asset accounting rules are externally defined and must be treated as immutable inputs to the system — the system applies them, it does not define them.

### 11.2 Assumptions

Two synthetic data inputs are provided for the POC: EAC_Timesheet_Dataset.xlsx (full workflow dataset) and sample_timesheets.zip (10 raw weekly timesheet documents in .docx format).

The 10 timesheet documents in sample_timesheets.zip correspond to 10 specific rows in EAC_Timesheet_Dataset.xlsx. Candidates should use this correspondence as a validation mechanism to verify their parsing pipeline accuracy.

Simulated or mocked HR profile data and project code registry data are acceptable for POC purposes. Candidates may derive persona context from the provided synthetic dataset.

General GAAP/accounting capitalisation principles may be applied if specific fixed asset accounting rules are not provided as part of the test materials.

All non-provided data contexts (project code registries, accounting rules, historical timesheet data) may be stubbed for the POC. Clearly document what is simulated and how it would be replaced in production.

The POC operates in shadow/dark mode — classification outputs are for demonstration and evaluation purposes only and do not replace the current timesheet submission workflow.

## 12. Glossary

**CapEx (Capital Expenditure)**

Spending on assets that provide long-term value — in this context, labor spent on building, designing, or creating systems and capabilities. Capitalizable labor reduces operating expense and is amortized over the asset's useful life.

**OpEx (Operating Expenditure)**

Day-to-day operational spending — labor spent on activities that do not qualify as capital investment (administration, maintenance, support, etc.).

**Project Coder**

An employee in a software engineering, product development, or related function who is required to submit weekly timesheets assigning their work hours to specific project codes, each with a defined CapEx or OpEx classification.

**Project Code**

A financial identifier assigned to a specific project or investment. Each project code carries a CapEx or OpEx designation that determines the capitalisation treatment of labor hours assigned to it.

**Activity Type**

A classification of how an employee's time was spent — for example: detailed design, build, requirements gathering, administration, maintenance, or support. Activity types map to CapEx or OpEx treatment based on fixed asset accounting rules and project code context.

**Weekly Mode**

The engine operating mode for the Project Coder use case — distributing employee activity hours across project codes and activity types for a rolling 7-day context window. Each activity block is tagged CapEx or OpEx per the associated project code designation.

**Timesheet Pre-Population**

The primary output of the UC-2 system — a pre-filled weekly timesheet draft presenting each employee with an AI-generated allocation of their hours across project codes and activity types, ready for employee review, adjustment, and submission.

**Raw Timesheet Parsing Connector**

The connector responsible for reading raw weekly timesheet documents (.docx), extracting structured activity records — project codes, activity types, time allocations, date ranges — from narrative or semi-structured content, and producing schema-validated records for the classification pipeline.

**Fixed Asset Accounting Rules**

The organisational policy document that defines which types of activities qualify as capital expenditure vs. operating expense under applicable accounting standards. Treated as an immutable input to the classification engine.

**Confidence Score**

A 0–100 score produced by the classification engine for every classified record, representing the engine's certainty in its classification. Records below the configured threshold are routed to human review.

**Evidence Trail**

A human-readable explanation of why a record was classified as it was — citing specific observable signals (e.g., "attended 6 build planning meetings; job family = software engineer; project code = CapEx project Y; 80% of ticket activity tagged as feature development") and the rules applied.

**Conflict Rate**

The percentage of classified records that are overridden by a human reviewer. The primary measure of classification quality and model improvement over time.

**Overnight Batch Run**

The nightly execution of the full classification pipeline — data harvesting from all active connectors, context building, classification, confidence routing, and output generation. Runs outside business hours; results available the following morning.

**Persona Configuration**

A configuration file defining the behavioral parameters of the classification engine for a specific employee population: output mode, aggregation window, activity-to-project-code mapping, confidence thresholds, and applicable rule set.

**Dark / Shadow Mode**

A deployment model where the classification system runs in parallel with existing processes, producing outputs for expert review and validation — but not replacing the current timesheet submission workflow. The POC operates in shadow mode.

**Stubbed / Simulated Data**

Hardcoded, mocked, or generated data used in place of a live enterprise data source. A well-designed stub clearly documents the schema and assumptions it represents, so it can be replaced by a real connector without engine changes.

**Labeled Training Data**

Historical data where the correct output is known — used to calibrate and validate the classification model. For this assessment, simulated historical timesheet data with known CapEx/OpEx splits per activity type serves as labeled training data.
