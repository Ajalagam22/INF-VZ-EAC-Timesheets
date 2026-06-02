# Employee Activity Classification System

**AI-Enabled CapEx / OpEx Activity Classification — UC-2 Supplementary Requirements**

Addendum to: EAC_Candidate_Brief_TEST May 22.docx

**Purpose of this document:** This addendum captures four supplementary requirements arising from the May 22 stakeholder demo call. It is a companion to the primary brief — not a replacement. All original requirements (REQ-01 through REQ-52) remain in force. The items below extend or clarify the scope based on direct client feedback from Mike Hanson and Paul Kerl.

---

## A. Agentic Workflow Diagram — Required Deliverable

**NEW — client feedback (May 22 demo):** Mike Hanson (immediate priority, confirmed by Paul Kerl): produce one clean slide or diagram showing the full agentic workflow end-to-end, including the reconciliation and reporting outputs at the tail of the pipeline.

The primary brief requires an architecture diagram within the submitted Architecture Document. This addendum elevates the agentic workflow diagram to a standalone deliverable in its own right — separate from, and in addition to, the system architecture diagram.

The workflow diagram must tell the full pipeline story: data enters, agents process it in sequence, and structured outputs reach the right audience. It must be legible as a standalone slide or single-page document — able to communicate the system to a non-technical executive without supporting commentary.

### A.1 Diagram Content Requirements

The diagram must depict, at minimum, the following stages in sequence:

| **Stage** | **Agent / Component** | **What to Show** |
|---|---|---|
| 1 | Data Sources | Connectors feeding the pipeline: Excel dataset, raw timesheet documents, and "Coming Soon" sources (BigQuery, HR systems, project registries) |
| 2 | Data Harvesting Agent | Ingestion, schema validation, staging. Show the two active connectors explicitly. |
| 3 | Context Building Agent | Per-employee 7-day activity digest construction. Show the rolling weekly window. |
| 4 | Classification Agent | CapEx / OpEx classification with confidence score and evidence trail generation. |
| 5 | Policy & Rules Agent | Accounting rule overlay, project code constraint enforcement, persona configuration. |
| 6 | Confidence & Routing Agent | Bifurcation: high-confidence records to employee review queue; low-confidence to team lead escalation queue. |
| 7 | Reconciliation & Reporting Agent | NEW: Post-classification aggregation — roll up to cost center; count completions and deltas; produce finance-facing reconciliation report. See Section B. |
| Output Channels | Three distinct outputs | (a) Employee pre-populated timesheet draft; (b) Team lead escalation view; (c) Finance / tax reconciliation report with cost center roll-up |

**[REQ-53]** The submitted Architecture Document SHALL include a standalone agentic workflow diagram that depicts all seven pipeline stages (Data Harvesting through Reconciliation & Reporting) and all three output channels. The diagram must be fully labelled, readable at A4 / Letter scale, and self-explanatory without supporting text. It must be submitted as part of the Architecture Document and may additionally be submitted as a separate single-page PDF or slide.

---

## B. Reconciliation & Reporting Agent — New Pipeline Stage

**NEW — client feedback (May 22 demo):** Mike Hanson: the pipeline currently stops at classification and confidence routing. It needs a downstream step that aggregates row-level results to cost center, counts completions and deltas, and delivers a reconciled output to tax and accounting.

The existing agent taxonomy in the primary brief (REQ-17 through REQ-22) defines six agents ending at Confidence & Routing. Based on client feedback, a seventh agent is now required: the Reconciliation & Reporting Agent. This agent operates after routing and serves a fundamentally different audience — finance and tax teams — rather than operational managers or individual employees.

The need arises because the classification engine produces row-level per-employee outputs. Finance and tax teams do not review individual rows — they review cost center summaries, reconcile completions, and act on deltas. Without this agent, the system's value chain is incomplete: the classification is done but the financial reporting step that enables action is missing.

### B.1 Agent Responsibility

- Aggregate classified row-level records up to cost center, team, and organisational hierarchy.
- Count survey / timesheet completions per cost center and flag outstanding submissions.
- Compute CapEx / OpEx deltas: compare pre-classification baseline (assumed 100% OpEx) against post-classification output to quantify capitalisation recovery per cost center.
- Identify and surface records with unusually large deltas or anomalous classification patterns for targeted review.
- Produce a finance-facing reconciliation report in a format reviewable by tax and accounting teams — not a dashboard, but a structured tabular output suitable for downstream systems.

**[REQ-54]** The system SHALL implement a Reconciliation & Reporting Agent as the seventh stage of the agentic pipeline. This agent SHALL execute after the Confidence & Routing Agent has completed its run for the current batch window. The agent SHALL aggregate all high-confidence classified records (those not in the escalation queue) to cost center level and produce a reconciliation report as defined in REQ-55.

**[REQ-55]** The Reconciliation & Reporting Agent SHALL produce a cost-center-level reconciliation report containing: (a) total employees processed in the batch window; (b) completion count and outstanding submission count per cost center; (c) aggregate CapEx hours and OpEx hours per cost center; (d) baseline-vs-classified delta showing capitalisation recovery in hours and percentage; and (e) a list of employees or records flagged for large deltas or review. For the POC, this report may be rendered as a UI panel or downloadable table — a stub is acceptable provided the data shape is fully defined and documented.

**[REQ-56]** The reconciliation report SHALL support hierarchical roll-up: results must be navigable at individual employee level, cost center level, job title level, and project level — consistent with the hierarchy described by the client. The POC must demonstrate at least two levels of roll-up.

> **Stubbed data:** The reconciliation report UI may be stubbed for the POC. Clearly document the data schema of the report output and describe how it would connect to real finance reporting systems in production (e.g., SAP, internal BI tools).

---

## C. Data Structure and Data Dictionary — Submitted Deliverable

**NEW — client feedback (May 22 demo):** Client alignment (May 22 demo): lock down the data schema now so the workflow can be rapidly re-pointed to real enterprise data when it starts flowing in.

The primary brief specifies the synthetic dataset and defines connectors, but does not require the candidate to formally document the schema as a standalone deliverable. Based on the client conversation, the data dictionary is now a required submission — it is the artefact that bridges the POC to real data onboarding.

The intent is that the data dictionary produced in this assessment can be shared directly with the client's data team to validate that the schema covers the real-world fields they will eventually provide. It must be written for a data engineer, not a developer — field names, types, allowed values, business definitions, and source system hints, not code.

### C.1 Data Dictionary Content Requirements

| **Section** | **Required Content** |
|---|---|
| Employee Activity Record | All fields in EAC_Timesheet_Dataset.xlsx — field name, data type, allowed values / range, business definition, and how the field would map to a real source system (e.g., HRIS, project management tool, calendar API). Include submission_notes. |
| Project Code Registry | Schema for the project code reference data consumed by the classification engine — project_code, project_name, funding_category, capex_opex_designation, and any additional classification-relevant attributes. May be based on the simulated registry used in the POC. |
| Classification Output Record | Schema of the per-employee classified output: all fields produced by the Classification Agent including confidence score, evidence trail, override flag, and audit metadata. |
| Reconciliation Report Schema | Schema of the cost-center-level reconciliation report output (see REQ-55). Must define all aggregation fields, delta calculations, and the hierarchy keys used for roll-up. |
| Connector Interface Contract | The standardised record format that all connectors must produce — the extensibility contract referenced in REQ-15. Must be formally defined here as a schema table. |

**[REQ-57]** The candidate SHALL submit a Data Dictionary document as part of the Architecture Document or as a separate appendix. The Data Dictionary must cover the five sections defined above. For fields that are simulated in the POC, the candidate must indicate which source system would provide that field in production and what transformation (if any) is required to map it to the schema.

---

## D. Early Insights Layer — Output Enhancement

**NEW — client feedback (May 22 demo):** Client feedback (May 22 demo): the system should go beyond "here are the results" to "here are the early insights" — sliced by job title, team, and project. Slicing by job function across different business units will surface quick wins.

The primary brief requires per-employee weekly outputs and aggregate capitalisation shift metrics. Based on client feedback, a second output tier is now required: an early insights layer that surfaces patterns and anomalies across the classified dataset without requiring the viewer to inspect individual records. This layer serves team leads, finance analysts, and program sponsors — not individual employees.

The distinction from existing outputs is the level of interpretation. Current outputs answer: "what was classified for this employee?" The insights layer answers: "what patterns are visible across this population, and where should we focus attention first?"

### D.1 Required Insight Slices

The following slices must be available in the output dashboard or report. Data from the synthetic dataset is sufficient for the POC — real data is not required.

| **Insight Slice** | **Description** | **POC Implementation** |
|---|---|---|
| By job title | CapEx / OpEx split distribution across each job title in the dataset. Surface outliers: job titles where the classified split differs materially from the expected split for that role. | Chart or table showing avg CapEx % per job title; flag titles where individual variance is high |
| By team / org unit | CapEx / OpEx split per team. Enable comparison across teams — e.g., does one business unit capitalise more or less than another for equivalent roles? | Side-by-side team comparison view; highlight largest cross-team deltas |
| By project | Hours distribution across project codes. Surface projects where OpEx hours are disproportionately high relative to the project's CapEx designation. | Project portfolio view showing CapEx-designated projects with low capitalisation rates — flagged for attention |
| Activity type distribution | Breakdown of time spent by activity type (meetings & coordination, build / development, incident response, etc.) across the full dataset. Flag employees spending 100% of their time in a single activity category inconsistent with their role. | Activity type heat map or bar chart; role-inconsistency flag logic |
| Completion and escalation rate | What % of records were classified with high confidence vs. escalated? How does this vary by team, job family, or week? | Summary panel showing confidence distribution; escalation rate by team |

**[REQ-58]** The UI SHALL include an Early Insights panel or view that presents the five insight slices defined above: by job title, by team / org unit, by project, by activity type distribution, and by completion and escalation rate. Each slice must be interactive — the reviewer must be able to filter or drill down to the underlying records that make up any given metric. For the POC, the synthetic dataset is the data source.

**[REQ-59]** The insights layer SHALL surface anomalies automatically — it must not require the reviewer to know what to look for. Minimum anomaly detection: (a) employees whose activity type distribution is inconsistent with their job title; (b) projects with CapEx designations but low classified CapEx rates; (c) teams with materially different capitalisation rates from peers in equivalent job families.

> **Stubbed data:** Insight logic may use heuristic thresholds on the synthetic dataset for the POC. Document the threshold values and how they would be calibrated against real data in production.

---

## E. Addendum Requirement Index

The following new requirements are added by this addendum. All original requirements REQ-01 through REQ-52 remain in force unchanged.

| **Req ID** | **Section** | **Summary** | **Stub OK?** |
|---|---|---|---|
| REQ-53 | A | Standalone agentic workflow diagram — all 7 agents + 3 output channels | No |
| REQ-54 | B | Reconciliation & Reporting Agent — 7th pipeline stage | Yes (data shape must be defined) |
| REQ-55 | B | Cost-center reconciliation report with completions, deltas, and flagging | Yes |
| REQ-56 | B | Hierarchical roll-up — employee → cost center → job title → project | Partial (2 levels min) |
| REQ-57 | C | Data Dictionary — 5 sections: activity record, project registry, output, reconciliation, connector contract | No |
| REQ-58 | D | Early Insights panel — 5 slices: job title, team, project, activity type, completion rate | No |
| REQ-59 | D | Automatic anomaly detection within insights layer | Yes (heuristic thresholds acceptable) |

---

*This addendum was produced from stakeholder feedback captured during the May 22, 2025 demo call with Mike Hanson and Paul Kerl. It supplements EAC_Candidate_Brief_TEST May 22.docx and should be read alongside it. Questions about scope interpretation should be directed to the InfoVision engagement team.*
