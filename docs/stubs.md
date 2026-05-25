# Stub Inventory

This document identifies which capabilities are intentionally simulated for the
Project Coder Weekly Timesheet POC. The POC keeps the core workflow functional:
Excel ingestion, DOCX timesheet parsing, canonical schema mapping,
classification, confidence routing, employee review surfaces, escalation
surfaces, and audit visibility.

## Must Remain Functional

These are required POC capabilities and should not be reduced to placeholders.

| Capability | Reason |
| --- | --- |
| Excel dataset connector | Primary full-volume workflow input required by REQ-09. |
| DOCX / ZIP timesheet parser | Required extraction capability for the 10 sample forms under REQ-10 and REQ-42. |
| Canonical schema validation | Required connector-to-engine contract under REQ-15 and REQ-33. |
| CapEx / OpEx classification engine | Primary deliverable under REQ-01 through REQ-08. |
| Confidence scoring and routing | Required for every record under REQ-03, REQ-22, and REQ-40. |
| Evidence trail | Required for every classification under REQ-04 and REQ-25. |
| Employee weekly draft view | Required review-and-confirm surface under REQ-23 and REQ-27. |
| Team lead escalation view | Required for low-confidence records under REQ-26, REQ-30, and REQ-32. |
| Dashboard capitalisation shift metrics | Required under BO-05, REQ-24, and REQ-31. |

## Acceptable POC Stubs

The requirements explicitly allow these to be simulated, provided their
interfaces and production replacement paths are documented.

| Stub | Current POC Representation | Production Replacement |
| --- | --- | --- |
| HR job profile connector | Employee fields are carried in the synthetic workbook and DOCX schema: job title, job family, team, org unit, manager. | HRIS/Workday-style connector refreshed at least weekly, producing the same canonical employee context fields. |
| Project code registry | Static in-code registry mapping project code to project name, funding category, phase, and CapEx/OpEx designation. | Finance/project portfolio connector or governed reference table with versioned project code mappings. |
| Fixed asset accounting rules source | Versioned deterministic rule module with activity lists and score impacts. | Versioned policy/rules store or document ingestion pipeline; rules updated without engine deployment. |
| Historical timesheet / classification data | Synthetic records and generated semantic precedents used for calibration/demo context. | Historical approved timesheets, human-reviewed classifications, and corrections loaded as labeled training/reference data. |
| Persona configuration store | Project-coder persona parameters are represented in settings/rule version and code constants. | JSON/YAML persona config files controlling cadence, thresholds, activity mappings, and applicable rule sets. |
| Nightly scheduler | On-demand upload-triggered batch execution. | Cron, Airflow, Cloud Scheduler, or enterprise workflow scheduler triggering the same orchestrator. |
| Queue infrastructure | In-process job/progress tracking for POC ingestion. | SQS/RabbitMQ/Celery/managed queue for scalable async agent execution. |
| Enterprise shared data store | SQLite local database for POC state and audit tables. | PostgreSQL or enterprise warehouse with migrations, encryption, retention, and access controls. |
| Semantic precedent retrieval | LLM/stub-generated precedent summaries shown in audit UI. | Vector store or reviewed-classification search over labeled historical activity records. |
| LLM gray-area reasoning fallback | LLM calls are optional; deterministic rules remain authoritative. Local stubs return context, policy, retrieval, and evidence text when the provider is unavailable or skipped. | Approved LLM provider with structured outputs, prompt/version registry, monitoring, and fallback controls. |
| Access control / roles | UI sections are visible in the POC without real user identity enforcement. | SSO/RBAC enforcing employee, team lead, and finance-reviewer scopes. |
| Data access audit logging | Classification and override audit events are persisted; read/access events are not fully logged. | Append-only access log for every record view/API read with actor, component, timestamp, and purpose. |
| Encryption controls | Local development assumptions. | Managed encrypted storage, TLS-only service communication, key management, and enterprise secrets management. |
| Future connectors | Coming Soon catalog cards for Calendar, Jira, GitHub, Slack, Google Drive, SharePoint, BigQuery, Google Sheets, MCP servers. | Each implemented as a connector conforming to the canonical schema contract. |
| Feedback learning loop | Overrides are captured as audit events, but no automated model/rule retraining is performed. | Human corrections persisted to a calibration dataset and reviewed before rule/model updates. |

## Stub Boundaries

- Stubs must output the same canonical record shape as real connectors.
- Stubs must not add connector-specific logic inside the classification engine.
- Stubs must be visible in architecture and UI as simulated/planned where they
  are not active sources.
- The deterministic classification rules remain the authoritative POC decision
  path; LLM/stub outputs enrich evidence and traceability rather than silently
  changing accounting outcomes.

## Recommended Demo Framing

For the showcase, describe the system as a functional POC with two active
connectors and several enterprise-context stubs. The correct message is:

"The engine, ingestion path, classification path, employee review surface,
escalation surface, metrics, and audit trace are functional. HR, project
registry, historical labels, scheduler, enterprise security, and additional
connectors are simulated behind stable interfaces and can be replaced without
rewriting the engine."
