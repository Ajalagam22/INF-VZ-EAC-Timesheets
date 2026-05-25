# EAC System — Execution Plan & Architecture Document

**Employee Activity Classification System — UC-2: Project Coder Weekly Timesheet**

---

## 1. Strategic Assessment

### 1.1 What We're Actually Building

This is not a simple rules engine. The system must solve three fundamentally different problems simultaneously:

1. **An ETL/data engineering problem** — ingesting heterogeneous data (structured Excel, semi-structured .docx narratives, stubbed HR/project registries) into a unified schema.
2. **A classification problem** — applying accounting rules + signal inference to produce CapEx/OpEx labels with calibrated confidence.
3. **A human-in-the-loop workflow problem** — routing outputs to the right audience (employees vs. team leads) based on confidence, capturing corrections, and closing the feedback loop.

The POC must demonstrate all three working end-to-end. The critical insight from the brief: the **engine is the product**. Connectors, UI, and agents exist to serve it. Build the engine first, wire everything else around it.

### 1.2 Key Constraints Driving Architecture Decisions

| Constraint | Source | Architecture Impact |
| --- | --- | --- |
| Engine must be source-agnostic | AP-01 | Connector → Unified Schema → Engine. No connector logic leaks into engine. |
| Overnight batch, not real-time | AP-02 | Queue-based pipeline. Shared data store as intermediate. No synchronous API calls during classification. |
| 80% generic coverage | AP-03 | Rule-based core with ML-assist for gray areas. Don't over-engineer persona-specific logic. |
| Persona config = config files, not code | AP-04 | YAML/JSON persona definitions. Engine reads config at runtime. |
| Connectors are versioned and independently deployable | AP-05 | Connector interface contract. Schema validation at ingestion boundary. |
| Low-confidence never reaches employees | AP-06 | Confidence-based routing is structural, not UI-level filtering. |
| Every classification has an immutable evidence trail | AP-07 | Append-only audit log. Evidence is generated during classification, not reconstructed after. |

### 1.3 Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- |
| .docx parsing fails on edge-case formatting | High | Medium | LLM-assisted extraction with structured output validation against known dataset rows |
| Confidence scores are poorly calibrated | High | High | Use historical/simulated labeled data to set thresholds; expose calibration dashboard |
| Activity type → CapEx/OpEx mapping is ambiguous for mixed activities | High | High | Policy Rules Agent applies deterministic accounting rules first; AI only handles residual ambiguity |
| Single-employee context is insufficient for classification | Medium | Medium | Context Builder enriches with project-level and team-level signals |
| Nightly batch window exceeded at scale | Low (POC) | High (Prod) | Architecture supports parallelization per-employee; POC runs sequentially |
| Human corrections not fed back into model | Medium | High | Correction capture pipeline wired from day one; feedback loop documented even if not auto-learning for POC |

---

## 2. System Architecture

### 2.1 Architecture Overview

The system follows a **pipeline architecture** with six discrete agents orchestrated by a Flow Orchestrator. Data flows in one direction through the pipeline during each batch run, with human feedback creating a secondary loop that feeds back into subsequent runs.

```
[Data Sources] → [Data Harvesting Agent] → [Shared Data Store]
                                                    ↓
                                          [Context Building Agent]
                                                    ↓
                                          [Classification Agent]
                                                    ↓
                                          [Policy & Rules Agent]
                                                    ↓
                                          [Confidence & Routing Agent]
                                                    ↓
                              ┌──────────────────────┴──────────────────────┐
                    [High-Confidence Queue]                    [Low-Confidence Queue]
                              ↓                                          ↓
                    [Employee Review UI]                    [Team Lead Escalation UI]
                              ↓                                          ↓
                    [Corrections Captured]                    [Reclassifications]
                              └──────────────────────┬──────────────────────┘
                                                     ↓
                                          [Feedback → Data Store]
```

### 2.2 Component Breakdown

#### Layer 1: Connector Framework (Data Ingestion)

**Purpose:** Transform heterogeneous source data into the Unified Activity Record schema.

**Active connectors for POC:**

**Connector A — Excel Dataset Connector (EAC_Timesheet_Dataset.xlsx)**
- Reads structured tabular data.
- Validates each row against the Unified Activity Record schema.
- Rejects invalid rows with error logging.
- Reference implementation for all future connectors.

**Connector B — Raw Timesheet Parsing Connector (sample_timesheets.zip)**
- Reads .docx files containing narrative/semi-structured timesheet entries.
- Uses LLM-assisted extraction (Claude API) with structured output prompts to pull: employee ID, project codes, activity types, hours per activity, date ranges.
- Maps extracted fields to the Unified Activity Record schema.
- Validates 10 extracted records against corresponding dataset rows.

**Stubbed connectors (interface defined, data mocked):**
- HR Job Profile Connector — returns simulated job title, family, org unit per employee.
- Project Code Registry Connector — returns static project code → CapEx/OpEx mapping.
- Accounting Rules Connector — returns versioned rule document.
- Historical Timesheet Connector — returns simulated labeled training data.

**Connector interface contract:**
```
interface Connector {
  id: string
  version: string
  source_type: string
  
  ingest(): UnifiedActivityRecord[]
  validate(record: UnifiedActivityRecord): ValidationResult
  get_schema(): SchemaDefinition
  get_metadata(): ConnectorMetadata
}
```

Every connector outputs `UnifiedActivityRecord[]`. The engine never sees connector internals.

#### Layer 2: Shared Data Store

**Purpose:** Single source of truth between connectors and the classification engine.

**Design decisions:**
- PostgreSQL for structured records + JSONB for flexible signal payloads.
- Append-only audit tables — no UPDATE/DELETE on classification records.
- Versioned schema with migration support.

**Core tables:**

| Table | Purpose | Key Fields |
| --- | --- | --- |
| `activity_records` | Unified ingested records | employee_id, week_start, project_code, activity_type, hours, signals (JSONB) |
| `employee_context` | Enriched per-employee weekly context | employee_id, week_start, context_json, hr_profile, project_codes |
| `classifications` | Engine output | record_id, classification (CapEx/OpEx/Ambiguous), confidence, evidence_json |
| `audit_log` | Immutable classification trail | classification_id, rule_version, input_signals, output, timestamp |
| `corrections` | Human overrides | classification_id, original, corrected, corrected_by, timestamp, reason |
| `run_manifests` | Batch run metadata | run_id, start_time, records_processed, classified, escalated, failed, agent_timings |
| `persona_configs` | Persona definitions | persona_id, config_json, version |
| `accounting_rules` | Versioned rule sets | rule_id, version, rules_json, effective_date |

#### Layer 3: Agent Pipeline

**Agent 1 — Flow Orchestrator [REQ-17]**

Responsibilities:
- Triggers nightly batch run (or on-demand for POC).
- Sequences agents: Harvesting → Context → Classification → Policy → Confidence/Routing.
- Manages retry logic per agent (max 3 retries with exponential backoff).
- Produces run manifest on completion.
- Halts pipeline if >10% of records fail at any stage (circuit breaker).

Implementation: Python orchestrator with a state machine. Each agent is a callable with a defined input/output contract. Orchestrator tracks state per-record and per-batch.

**Agent 2 — Data Harvesting Agent [REQ-18]**

Responsibilities:
- Triggers `ingest()` on all active connectors.
- Validates every record against the Unified Activity Record schema.
- Rejects and logs invalid records.
- Stages clean records in `activity_records` table.
- Reports: records ingested per connector, validation failures, schema mismatches.

Edge cases:
- Partial .docx extraction (some fields missing) → ingest with null fields, flag for reduced confidence downstream.
- Duplicate records (same employee + same week from multiple connectors) → deduplicate by connector priority (Excel > .docx parser).
- Schema version mismatch → reject record, log with connector version info.

**Agent 3 — Context Building Agent [REQ-19]**

Responsibilities:
- For each employee + week combination, constructs a context record:
  - Daily-segmented activity digest (Mon–Sun).
  - Meeting count, ticket count, code commits, email frequency per day.
  - Project code allocation summary.
  - HR profile enrichment (job title, family, org unit).
  - Project and investment case context (project code → funding category → CapEx/OpEx designation).
- Stores enriched context in `employee_context` table.

Edge cases:
- Employee appears in activity data but has no HR profile → use "Unknown" persona, flag for review.
- Project code in activity data not found in registry → flag as unmapped, reduce confidence.
- Zero-hour weeks (employee has no activity signals) → generate empty context with note, skip classification.

**Agent 4 — Classification Agent (Core Engine) [REQ-20]**

This is the heart of the system. The classification engine applies a multi-layer classification strategy:

**Layer A — Deterministic Rule Application (highest priority)**
- If project code has explicit CapEx designation AND activity type is in the capitalizable list (design, build, test, requirements gathering for new features) → CapEx, confidence 85-95.
- If project code has explicit OpEx designation → OpEx, confidence 90-95.
- If activity type is always OpEx regardless of project (admin, leave, general meetings, support, maintenance) → OpEx, confidence 90-95.

**Layer B — Signal-Weighted Inference (for ambiguous cases)**
- Uses observable signals to infer activity nature when rules alone are insufficient.
- Signal weights (configurable per persona):
  - Code commits to CapEx project repos → strong CapEx indicator (weight: 0.8).
  - Tickets tagged "feature" or "enhancement" → CapEx indicator (weight: 0.7).
  - Tickets tagged "bug fix" or "maintenance" → OpEx indicator (weight: 0.6).
  - Meeting attendance in project planning/design meetings → CapEx indicator (weight: 0.5).
  - Email frequency to project stakeholders → weak signal (weight: 0.2).

**Layer C — LLM-Assisted Classification (for gray areas)**
- For records that remain ambiguous after Layer A and B, pass the full context to an LLM with:
  - The employee's enriched context record.
  - The applicable accounting rules.
  - The project code registry.
  - Prompt: "Given these signals and rules, classify this activity block as CapEx or OpEx. Explain your reasoning."
- LLM output is parsed for classification + evidence.
- Confidence is capped at 75 for LLM-only classifications (forces human review for purely inferential calls).

**Classification output per activity block:**
```
{
  record_id: string,
  employee_id: string,
  week_start: date,
  project_code: string,
  activity_type: string,
  hours: number,
  classification: "CapEx" | "OpEx" | "Ambiguous",
  confidence: 0-100,
  classification_layer: "deterministic" | "signal_weighted" | "llm_assisted",
  evidence: {
    signals_used: [...],
    rules_applied: [...],
    reasoning: string
  }
}
```

**Agent 5 — Policy & Rules Agent [REQ-21]**

Responsibilities:
- Overlays fixed asset accounting rules on top of base classification.
- Enforces hard constraints:
  - Total CapEx hours per employee cannot exceed their contracted hours minus mandatory OpEx activities.
  - CapEx classification requires the associated project to be in "Application Development" or equivalent SDLC phase (not "Post-Implementation" or "Maintenance").
  - Administrative activities (team meetings not tied to specific projects, 1:1s, training on existing tools) are always OpEx regardless of project code.
- Applies persona-specific rules from config:
  - Software engineer persona: code review counts as CapEx if the PR is for a CapEx project.
  - Product manager persona: requirements gathering counts as CapEx; stakeholder management is OpEx.
- Downgrades confidence if a rule override changes the base classification.

Edge cases:
- Employee works on both CapEx and OpEx projects in the same day → split proportionally by signal density.
- Activity type is "meetings" with no project code context → default to OpEx with low confidence.
- Rule version changes mid-week → apply the rule version active at the time of the activity.

**Agent 6 — Confidence & Routing Agent [REQ-22]**

Responsibilities:
- Evaluates final confidence score per record.
- Routes based on configurable thresholds (default for POC):
  - Confidence ≥ 70: → Employee review queue (high confidence).
  - Confidence 40-69: → Team lead escalation queue (medium confidence, needs human input).
  - Confidence < 40: → Team lead escalation queue with "requires investigation" flag.
- Generates escalation report for team leads.
- Low-confidence records NEVER appear in employee-facing views.

Threshold calibration approach:
- Start with conservative thresholds (70/40).
- After first batch run, analyze distribution of confidence scores.
- Adjust thresholds to hit target: ~80% of records in high-confidence queue, ~20% escalated.

#### Layer 4: Output Generation

**Weekly Timesheet Output [REQ-23]**

Per employee per week:
```
{
  employee_id: string,
  employee_name: string,
  week_start: date,
  week_end: date,
  total_hours: number,
  capex_hours: number,
  opex_hours: number,
  capitalisation_pct: number,
  line_items: [
    {
      project_code: string,
      project_name: string,
      activity_type: string,
      hours: number,
      classification: "CapEx" | "OpEx",
      confidence: number,
      evidence_summary: string
    }
  ],
  baseline_capex_pct: 0,  // Pre-classification: assumed 100% OpEx
  shift_delta: number      // Capitalisation improvement
}
```

**Capitalisation Shift Output [REQ-24]**

Per employee and aggregate:
- Baseline: 100% OpEx (pre-classification default).
- Post-classification: actual CapEx/OpEx split.
- Delta: the capitalisation recovery amount (hours × blended rate).

**Escalation Report [REQ-26]**

Per team lead:
- All low-confidence records for their team.
- Confidence score and specific signals that prevented high-confidence classification.
- Action options: reclassify, confirm, or flag for further investigation.

#### Layer 5: User Interface

**Employee View [REQ-27, REQ-28, REQ-29, REQ-30]**
- Weekly timesheet draft: hours by project code and activity type.
- Color-coded CapEx/OpEx designation per line item.
- Confidence indicators (green/yellow for high-confidence only; low-confidence records hidden).
- Evidence panel: plain-language explanation per classification.
- Correction mechanism: override classification, reassign project code or activity type.
- Aggregate metrics: total CapEx hours, total OpEx hours, capitalisation percentage.

**Team Lead Escalation View [REQ-32]**
- All escalated records for the team.
- Confidence scores, evidence trails, recommended classifications.
- Actions: clarify, reclassify, return to output queue.
- Team-level capitalisation metrics.

**Dashboard / Aggregate View [REQ-31]**
- Capitalisation shift over time (week-over-week trend).
- Classification distribution (CapEx vs. OpEx vs. Escalated).
- Conflict rate (corrections as % of total classifications).
- Connector health (records ingested, validation failures).
- Batch run status and timing.

**Connector Management Panel**
- Active connectors: Excel Dataset, Raw Timesheet Parser.
- "Coming Soon" panel for future connectors (calendar, Jira, GitHub, etc.).

### 2.3 Unified Activity Record Schema

This is the contract between connectors and the engine. Every connector must produce records conforming to this schema.

```
UnifiedActivityRecord {
  // Identity
  record_id: UUID (auto-generated)
  source_connector: string
  source_version: string
  ingestion_timestamp: datetime
  
  // Employee
  employee_id: string
  employee_name: string
  
  // Time
  week_start: date
  week_end: date
  
  // Activity
  project_code: string
  project_name: string (nullable)
  activity_type: string  // e.g., "Detailed Design", "Build", "Requirements", "Admin"
  hours: decimal
  
  // Signals (JSONB — flexible per connector)
  signals: {
    meeting_count: int (nullable)
    ticket_count: int (nullable)
    code_commits: int (nullable)
    email_count: int (nullable)
    system_activity_events: int (nullable)
    // Additional signal types added per connector
  }
  
  // Context (enriched by Context Builder)
  hr_context: {
    job_title: string (nullable)
    job_family: string (nullable)
    org_unit: string (nullable)
  }
  
  // Validation
  schema_version: string
  validation_status: "valid" | "partial" | "invalid"
  validation_errors: string[] (nullable)
}
```

### 2.4 Classification Decision Tree

```
For each activity record:

1. Is project_code in the Project Code Registry?
   ├─ NO → Flag as "unmapped project code", classify OpEx, confidence = 30
   └─ YES → Continue

2. What is the project_code's funding designation?
   ├─ Explicit OpEx → Classify OpEx, confidence = 92
   ├─ Explicit CapEx → Go to step 3
   └─ Mixed/Unknown → Go to step 4

3. Is the activity_type capitalizable under accounting rules?
   ├─ Always CapEx (design, build, test for new features) → Classify CapEx, confidence = 88
   ├─ Always OpEx (admin, maintenance, support) → Classify OpEx, confidence = 90
   └─ Conditional (code review, meetings, planning) → Go to step 4

4. Apply signal-weighted inference:
   - Compute weighted score from observable signals
   - If score > 0.65 → Classify CapEx, confidence = 60 + (score × 20)
   - If score < 0.35 → Classify OpEx, confidence = 60 + ((1-score) × 20)
   - If 0.35 ≤ score ≤ 0.65 → Go to step 5

5. LLM-assisted classification:
   - Pass full context + rules to LLM
   - Parse classification + reasoning
   - Cap confidence at 75
   - If LLM is uncertain → Classify "Ambiguous", confidence = 40

6. Policy overlay (all records):
   - Apply hard constraints (hours cap, SDLC phase check, admin override)
   - Adjust confidence if policy overrides base classification
```

---

## 3. Data Pipeline Design

### 3.1 Pipeline Flow

```
Phase 1: INGEST (Data Harvesting Agent)
  ├─ Excel Connector reads EAC_Timesheet_Dataset.xlsx
  │   └─ Row-by-row validation → activity_records table
  ├─ .docx Connector reads sample_timesheets.zip
  │   ├─ Extract text from each .docx
  │   ├─ LLM-assisted structured extraction
  │   ├─ Map to UnifiedActivityRecord
  │   └─ Validate against dataset rows (10 records)
  └─ Stubbed connectors populate HR, project, and rules data

Phase 2: ENRICH (Context Building Agent)
  ├─ For each (employee_id, week_start) pair:
  │   ├─ Aggregate daily activity signals
  │   ├─ Join HR profile data
  │   ├─ Join project code registry
  │   └─ Produce enriched context record
  └─ Store in employee_context table

Phase 3: CLASSIFY (Classification Agent)
  ├─ For each enriched context record:
  │   ├─ Apply deterministic rules (Layer A)
  │   ├─ If ambiguous → Apply signal weighting (Layer B)
  │   ├─ If still ambiguous → LLM classification (Layer C)
  │   └─ Produce classification + confidence + evidence
  └─ Store in classifications table

Phase 4: ENFORCE (Policy & Rules Agent)
  ├─ Apply accounting rule constraints
  ├─ Validate CapEx eligibility per project phase
  ├─ Enforce per-employee hour caps
  └─ Adjust confidence scores where policy overrides

Phase 5: ROUTE (Confidence & Routing Agent)
  ├─ High confidence (≥70) → Employee review queue
  ├─ Low confidence (<70) → Team lead escalation queue
  └─ Generate escalation report

Phase 6: OUTPUT
  ├─ Generate per-employee weekly timesheet drafts
  ├─ Compute capitalisation shift metrics
  ├─ Write run manifest
  └─ Make outputs available via UI API
```

### 3.2 .docx Parsing Strategy (Critical Path)

The raw timesheet parsing connector is the highest-risk component. .docx files contain narrative text with embedded structured data — not clean tables.

**Parsing approach:**

1. **Text extraction:** Use `python-docx` or `mammoth` to extract raw text + any table structures.
2. **LLM-assisted structured extraction:** Send extracted text to Claude API with a prompt template:

```
Given this raw timesheet entry, extract the following fields as JSON:
- employee_id
- employee_name
- week_start (YYYY-MM-DD)
- week_end (YYYY-MM-DD)
- line_items: array of { project_code, activity_type, hours }

Return ONLY valid JSON. If a field cannot be determined, set it to null.

Raw timesheet text:
---
{extracted_text}
---
```

3. **Validation pipeline:**
   - Parse LLM JSON output.
   - Validate each field against expected types and ranges.
   - Cross-reference extracted employee_id and week_start against EAC_Timesheet_Dataset.xlsx to find matching rows.
   - Compare extracted fields with dataset ground truth.
   - Report extraction accuracy per field and per document.

4. **Fallback:** If LLM extraction fails, attempt regex-based extraction for common patterns (project codes, date ranges, hour values).

**Accuracy target:** ≥90% field extraction accuracy [REQ-42].

### 3.3 Data Quality & Edge Cases

| Edge Case | Detection | Handling |
| --- | --- | --- |
| Employee with zero activity signals | Context Builder checks signal counts | Skip classification, flag in run manifest, include in escalation report |
| Duplicate employee-week records from multiple connectors | Dedup key: (employee_id, week_start, project_code, activity_type) | Prefer highest-priority connector; log conflicts |
| Hours exceed contracted maximum (e.g., >45 hrs/week) | Policy Agent validates totals | Flag for review, don't reject — employee may have worked overtime |
| Unknown project code | Project Code Registry lookup fails | Classify as OpEx with confidence = 30, escalate to team lead |
| Missing activity_type | Field is null after extraction | Infer from signals if possible (high code commits → "Build"), otherwise classify "Unspecified" with low confidence |
| .docx contains images/charts, not text | Text extraction returns empty/minimal content | Flag as "unparseable", log, report in run manifest |
| Accounting rule version changes between runs | Rule version tracked per classification | Each record stamps the rule version used; historical classifications immutable |

---

## 4. Technology Stack

### 4.1 POC Stack Selection

| Layer | Technology | Rationale |
| --- | --- | --- |
| Backend | Python (FastAPI) | Rapid development; rich data processing ecosystem; LLM SDK support |
| Database | PostgreSQL + JSONB | Structured + semi-structured data; robust querying; JSONB for flexible signal payloads |
| LLM | Claude API (claude-sonnet-4-20250514) | .docx parsing, gray-area classification, evidence generation |
| Data Processing | pandas + openpyxl | Excel ingestion, data transformation, validation |
| .docx Parsing | python-docx + Claude API | Text extraction + LLM-assisted structured data extraction |
| Task Orchestration | Custom Python orchestrator | Lightweight for POC; replace with Airflow/Prefect for production |
| Frontend | React + TypeScript | Component-based UI with rich interactive views |
| State Management | React Context + hooks | Sufficient for POC complexity |
| Charts | Recharts | React-native charting for dashboard visualizations |
| API Layer | FastAPI REST endpoints | Serves UI with JSON payloads |

### 4.2 Production Stack Considerations (Post-POC)

| Concern | POC | Production |
| --- | --- | --- |
| Orchestration | Custom Python | Apache Airflow / Prefect |
| Database | Single PostgreSQL | PostgreSQL cluster with read replicas |
| Caching | None | Redis for UI session and draft caching |
| Queue | In-memory | RabbitMQ / SQS for agent communication |
| Auth | None | OAuth 2.0 / SAML SSO |
| Encryption | None | TLS in transit, AES-256 at rest |
| Monitoring | Run manifests | Datadog / Prometheus + Grafana |
| CI/CD | Manual | GitHub Actions → Docker → Kubernetes |

---

## 5. Tradeoff Analysis

### 5.1 Rule-Based vs. ML-First Classification

**Decision: Rule-based core with ML assist.**

| Approach | Pros | Cons |
| --- | --- | --- |
| Pure rules-based | Deterministic, auditable, no training data needed, predictable | Cannot handle gray areas, brittle to new activity types |
| Pure ML | Handles ambiguity, learns from corrections, scales naturally | Black box for auditors, needs training data, cold-start problem |
| Hybrid (chosen) | Best of both: deterministic for clear cases, ML for residual ambiguity, fully auditable | More complex to build, two systems to maintain |

The hybrid approach satisfies AP-07 (defensibility by design) — every deterministic classification has a clear rule citation, and every ML classification has an evidence trail + confidence cap.

### 5.2 Batch vs. Real-Time

**Decision: Batch-first (AP-02), architecture supports real-time.**

The batch model is non-negotiable for the POC (AP-02). But the architecture avoids batch-only assumptions:
- Agents communicate through the data store, not through in-process function calls.
- Each agent has a defined input/output contract that works equally well with a queue-based real-time trigger.
- The connector interface supports both pull (batch) and push (webhook) patterns.

### 5.3 LLM for .docx Parsing vs. Rules/Regex

**Decision: LLM-primary with regex fallback.**

| Approach | Pros | Cons |
| --- | --- | --- |
| Regex/rule-based parsing | Fast, no API cost, deterministic | Brittle to format variation, requires per-template rules |
| LLM-assisted parsing | Handles narrative text, format-agnostic, high extraction accuracy | API cost, latency, non-deterministic output |
| LLM-primary + regex fallback (chosen) | Robust for varied formats, falls back gracefully, still validates against ground truth | Slightly higher cost, but only 10 docs for POC |

For 10 documents, the LLM approach is clearly superior — the format variation risk outweighs the API cost. At production scale (thousands of docs), batch LLM processing with caching and template detection becomes the optimization path.

### 5.4 Monolith vs. Microservices

**Decision: Modular monolith for POC.**

The agent architecture is logically separate but physically co-located in a single deployable for the POC. Each agent is a Python module with a clean interface. Extraction to independent services is a production concern, not a POC concern.

Why not microservices for POC:
- Operational overhead (deployment, networking, service discovery) distracts from engine quality.
- Single database transaction per batch run simplifies consistency.
- Agent interfaces are already defined — refactoring to services later is straightforward.

### 5.5 Confidence Score Calibration

**Decision: Heuristic calibration for POC, statistical calibration for production.**

POC approach:
- Deterministic rules: confidence = base_confidence × data_completeness_factor.
- Signal-weighted: confidence = 60 + (signal_alignment_score × 20).
- LLM-assisted: confidence capped at 75.
- Policy override: confidence reduced by 10 if policy changes base classification.

Production approach:
- Platt scaling on a held-out labeled validation set.
- Confidence = calibrated probability that a domain expert would agree.
- Tracked via conflict rate metric [REQ-52].

---

## 6. Execution Plan & Phasing

### Phase 0: Foundation (Days 1–2)

**Deliverables:**
- Project skeleton: Python backend, React frontend, PostgreSQL schema.
- Unified Activity Record schema (JSON Schema + DB migration).
- Connector interface contract (Python ABC).
- Persona configuration schema (YAML).
- Fixed asset accounting rules document (GAAP-based, versioned).
- Project code registry (simulated static data).
- HR profile mock data.

**Exit criteria:** Schema validated, mock data loadable, connector interface compilable.

### Phase 1: Data Pipeline (Days 3–5)

**Deliverables:**
- Excel Dataset Connector: reads EAC_Timesheet_Dataset.xlsx, validates, stages records.
- Raw Timesheet Parsing Connector: extracts text from .docx, LLM-assisted structured extraction, validates against dataset rows.
- Data Harvesting Agent: triggers connectors, validates, deduplicates, stages.
- Stubbed connectors: HR, project registry, accounting rules, historical data.
- Schema validation pipeline with error reporting.

**Exit criteria:** All dataset records ingested and validated. 10 .docx records extracted with ≥90% field accuracy against ground truth. Run manifest produced.

### Phase 2: Classification Engine (Days 6–9)

**Deliverables:**
- Context Building Agent: constructs per-employee weekly context records.
- Classification Agent: three-layer classification (deterministic → signal-weighted → LLM-assisted).
- Policy & Rules Agent: accounting rule enforcement, persona-specific overlays.
- Confidence & Routing Agent: threshold-based routing, escalation report generation.
- Evidence trail generation for every classification.
- Confidence scoring with calibration on labeled data.

**Exit criteria:** Full dataset classified. ≥70% agreement with expected outcomes. Every record has confidence score and evidence trail. Low-confidence records correctly routed to escalation queue.

### Phase 3: Output & Reporting (Days 10–11)

**Deliverables:**
- Per-employee weekly timesheet output generation.
- Capitalisation shift computation (baseline vs. classified).
- Escalation report for team leads.
- Run manifest with full batch metrics.
- Value tracking: per-employee and aggregate CapEx reclassification amounts.

**Exit criteria:** Complete output for all employees in dataset. Capitalisation shift visible. Escalation report populated.

### Phase 4: User Interface (Days 12–15)

**Deliverables:**
- Employee weekly timesheet review view (with confidence indicators and evidence).
- Correction mechanism (override classification, reassign project code/activity type).
- Team lead escalation view (low-confidence records, reclassification actions).
- Dashboard: capitalisation metrics, classification distribution, conflict rate, connector health.
- Connector management panel with "Coming Soon" indicators.
- Audit trail panel stub.

**Exit criteria:** End-to-end flow demo-able: upload data → classify → review draft → correct → see metrics.

### Phase 5: Polish & Documentation (Days 16–18)

**Deliverables:**
- Architecture diagram (fully labelled system diagram).
- Architecture decision records (ADRs) for key tradeoffs.
- Stubbed data documentation (what is simulated, how to replace).
- API documentation.
- POC evaluation guide (how to assess classification accuracy).
- Edge case documentation.
- Performance benchmarks on POC dataset.

**Exit criteria:** Submission-ready. All REQ items addressed. Architecture document complete.

---

## 7. Requirement Coverage Matrix

| REQ | Description | Phase | Status |
| --- | --- | --- | --- |
| REQ-01 | Engine accepts structured per-employee activity record | Phase 2 | Engine input schema |
| REQ-02 | Engine applies accounting rules, classifies CapEx/OpEx/Ambiguous | Phase 2 | Classification Agent |
| REQ-03 | Confidence score 0-100 for every classification | Phase 2 | Confidence scoring |
| REQ-04 | Evidence trail for every classification | Phase 2 | Evidence generation |
| REQ-05 | Weekly mode: hours distributed across project codes | Phase 2 | Output format |
| REQ-06 | Designed as nightly batch; on-demand for POC | Phase 2 | Orchestrator |
| REQ-07 | Engine is source-agnostic | Phase 1-2 | Connector interface |
| REQ-08 | Configurable by persona | Phase 0 | Persona config YAML |
| REQ-09 | Excel dataset connector | Phase 1 | Connector A |
| REQ-10 | Raw timesheet parsing connector | Phase 1 | Connector B |
| REQ-11 | Historical timesheet data support | Phase 0 | Stubbed connector |
| REQ-12 | HR job profile data support | Phase 0 | Stubbed connector |
| REQ-13 | Project code registry ingestion | Phase 0 | Stubbed connector |
| REQ-14 | Accounting rules as static versioned input | Phase 0 | Rules document |
| REQ-15 | Standardised connector output format | Phase 0 | Schema contract |
| REQ-16 | Daily hydration frequency | Phase 1 | Harvesting Agent |
| REQ-17 | Flow Orchestrator | Phase 2 | Orchestrator |
| REQ-18 | Data Harvesting Agent | Phase 1 | Agent 2 |
| REQ-19 | Context Building Agent | Phase 2 | Agent 3 |
| REQ-20 | Classification Agent | Phase 2 | Agent 4 |
| REQ-21 | Policy and Rules Agent | Phase 2 | Agent 5 |
| REQ-22 | Confidence and Routing Agent | Phase 2 | Agent 6 |
| REQ-23 | Per-employee weekly timesheet output | Phase 3 | Output generation |
| REQ-24 | Capitalisation shift output | Phase 3 | Shift computation |
| REQ-25 | Evidence trail on every output record | Phase 2-3 | Evidence pipeline |
| REQ-26 | Low-confidence escalation report | Phase 3 | Escalation report |
| REQ-27 | Employee timesheet UI | Phase 4 | Employee view |
| REQ-28 | Correction mechanism in UI | Phase 4 | Override flow |
| REQ-29 | Flexible review cadence | Phase 4 | Draft persistence |
| REQ-30 | Low-confidence hidden from employees | Phase 2-4 | Routing + UI filter |
| REQ-31 | Aggregate capitalisation metrics in UI | Phase 4 | Dashboard |
| REQ-32 | Team lead escalation view | Phase 4 | Escalation UI |
| REQ-33 | Schema validation for all records | Phase 1 | Validation pipeline |
| REQ-34 | .docx parser extracts all structured fields | Phase 1 | Connector B |
| REQ-35 | Graceful handling of missing signals | Phase 2 | Reduced confidence |
| REQ-36 | Weekly HR data refresh | Phase 0 | Stubbed connector |
| REQ-37 | Versioned accounting rules | Phase 0 | Rules versioning |
| REQ-38 | Batch run within 12-hour window | Phase 2 | Performance target |
| REQ-39 | UI load under 1 minute | Phase 4 | Performance target |
| REQ-40 | Confidence score for 100% of records | Phase 2 | Mandatory scoring |
| REQ-41 | ≥70% classification accuracy | Phase 2 | Accuracy target |
| REQ-42 | ≥90% .docx extraction accuracy | Phase 1 | Parsing target |
| REQ-43 | Immutable audit record per classification | Phase 2 | Audit log |
| REQ-44 | Data access event logging | Phase 2 | Access log |
| REQ-45 | Scoped read-only data access | Phase 0 | Connector design |
| REQ-46 | Employee data access control | Phase 4 | Auth/scoping |
| REQ-47 | Encryption in transit and at rest | Phase 5 | Documented for prod |
| REQ-48 | New connector requires no engine changes | Phase 0-1 | Interface contract |
| REQ-49 | New persona requires only config file | Phase 0 | Persona schema |
| REQ-50 | Rules updatable without deployment | Phase 0 | Versioned rules |
| REQ-51 | Run manifest per batch run | Phase 2 | Orchestrator output |
| REQ-52 | Conflict rate tracked per run | Phase 3-4 | Correction tracking |

---

## 8. What "Good" Looks Like

The evaluator opens the system and sees:

1. **Data pipeline works.** Upload Excel → records appear validated and staged. Upload .docx files → structured records extracted, validated against ground truth with ≥90% accuracy.

2. **Classification is defensible.** Open any classified record → see the evidence trail: "Project ALPHA-2024 is designated CapEx. Activity type 'Detailed Design' is capitalizable under Rule Set v1.2. Employee's job family (Software Engineer) has capitalizable activity weight of 0.85. 14 code commits to CapEx repo. 6 design meetings attended. Confidence: 87."

3. **The right people see the right things.** Employee view shows only high-confidence classifications with a clean timesheet draft. Team lead view shows escalated records with action buttons. No low-confidence record leaks to an employee.

4. **The capitalisation story is clear.** Dashboard shows: "Before: 100% OpEx. After classification: 62% OpEx, 38% CapEx. Capitalisation recovery: 380 hours reclassified across 12 employees this week."

5. **Architecture is extensible.** Connector panel shows two active connectors with green status, and a "Coming Soon" section listing Calendar, Jira, GitHub, Slack connectors with defined interfaces.

6. **Everything is auditable.** Audit trail panel shows: input signals → rule version → confidence → output → any human overrides — for any classification, at any time.
