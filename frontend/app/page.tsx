"use client";

import {
  AlertTriangle,
  BarChart3,
  Bot,
  CalendarDays,
  CheckCircle2,
  ClipboardCheck,
  Database,
  FileSpreadsheet,
  FileText,
  Gauge,
  History,
  Layers3,
  RefreshCw,
  ShieldCheck,
  TableProperties,
  TrendingUp,
  Target,
  UploadCloud,
  type LucideIcon
} from "lucide-react";
import { ChangeEvent, Fragment, useEffect, useMemo, useRef, useState } from "react";
import { appConfig } from "../config/appConfig";

type Classification = "CapEx" | "OpEx" | "Review";
type RecordFilter = "All" | Classification;
type SourceFilter = "All" | "Excel" | "DOCX form";
type TabId = "dashboard" | "records" | "analytics" | "sources" | "drafts" | "review" | "escalations" | "learning" | "audit";
type SourceSubTab = "connectors" | "pipeline" | "validation";

type Summary = {
  total: number;
  capex: number;
  opex: number;
  review: number;
  overrides: number;
  total_hours: number;
  capex_hours: number;
  opex_hours: number;
  review_hours: number;
  capitalisation_pct: number;
  estimated_recovery_usd: number;
  docx_records: number;
  docx_matched_excel: number;
  docx_match_pct: number;
};

type Signal = {
  label: string;
  impact: number;
  kind: "capex" | "opex" | "quality" | "policy";
};

type RecordItem = {
  _key?: string;
  _recordUid: string;
  employee_id: string;
  full_name: string;
  job_title: string;
  job_family: string;
  team_name: string;
  org_unit: string;
  manager_id: string;
  week_start_date: string;
  week_end_date: string;
  standard_days: number;
  holiday_days: number;
  pto_days: number;
  sick_days: number;
  actual_working_days: number;
  meeting_count: number;
  ticket_count: number;
  email_volume: string;
  code_commit_count: number;
  system_activity_score: number;
  project_code: string;
  project_name: string;
  activity_type: string;
  hours_allocated: number;
  submission_notes?: string;
  _source?: string;
  _sourceFileName?: string;
  _classification: Classification;
  _confidence: number;
  _evidence: string;
  _reviewReason: string;
  _ruleVersion?: string;
  _rowQuality?: {
    status: string;
    issues?: string[];
  };
  _signals?: Signal[];
  _override?: Classification | null;
  _overrideNote?: string | null;
  _matchedExcel?: number;
  _extractionConfidence?: number;
  _formValidation?: {
    extractedFields?: number;
    totalFields?: number;
  };
  _normalizedFields?: Record<string, unknown>;
  _rawFields?: Record<string, unknown>;
  _agentTrace?: {
    provider: string;
    model: string;
    steps: Array<{
      agent: string;
      status: string;
      summary: string;
      provider: string;
      output: Record<string, unknown>;
    }>;
  };
};

type DraftLine = {
  record_uid: string;
  project_code: string;
  project_name: string;
  activity_type: string;
  hours: number;
  classification: Classification;
  confidence: number;
  evidence_summary: string;
  signals: Signal[];
  source: string;
};

type Draft = {
  employee_id: string;
  employee_name: string;
  job_title: string;
  job_family: string;
  team_name: string;
  manager_id: string;
  week_start: string;
  week_end: string;
  holiday_days: number;
  pto_days: number;
  sick_days: number;
  actual_working_days: number;
  total_hours: number;
  capex_hours: number;
  opex_hours: number;
  capitalisation_pct: number;
  estimated_recovery_usd: number;
  line_items: DraftLine[];
};

type EscalationGroup = {
  manager_id: string;
  hours: number;
  records: RecordItem[];
};

type Connector = {
  source_type: string;
  source_file_name: string;
  records_processed: number;
  records_classified: number;
  records_failed: number;
  records_escalated: number;
  matched_excel: number;
  elapsed_seconds: number;
  created_at: string;
};

type AuditEvent = {
  id?: number;
  run_id?: string;
  record_uid?: string | null;
  event_type: string;
  payload: Record<string, unknown>;
  created_at: string;
};

type NamedValue = {
  name: string;
  hours: number;
  capexHours: number;
  opexHours: number;
  confidenceTotal: number;
  count: number;
};

type EmployeeProfile = {
  employeeId: string;
  employeeName: string;
  jobTitle: string;
  jobFamily: string;
  teamName: string;
  managerId: string;
  weeks: Draft[];
  totalHours: number;
  capexHours: number;
  opexHours: number;
  capitalisationPct: number;
  avgConfidence: number;
  projectMix: NamedValue[];
  activityMix: NamedValue[];
  keywordCloud: Array<{ word: string; weight: number }>;
};

type ProjectRecordGroup = {
  projectCode: string;
  projectName: string;
  totalHours: number;
  capexHours: number;
  opexHours: number;
  reviewHours: number;
  employees: Array<{
    employeeId: string;
    employeeName: string;
    jobTitle: string;
    teamName: string;
    hours: number;
    avgConfidence: number;
    classifications: Set<Classification>;
    records: RecordItem[];
  }>;
};

const tabs: Array<{ id: TabId; label: string; icon: LucideIcon }> = [
  { id: "dashboard", label: "Overview", icon: BarChart3 },
  { id: "records", label: "Activity Records", icon: TableProperties },
  { id: "escalations", label: "Review Queue", icon: AlertTriangle },
  { id: "review", label: "Employee Review", icon: ClipboardCheck },
  { id: "drafts", label: "Employee Directory", icon: ClipboardCheck },
  { id: "analytics", label: "Analytics", icon: TrendingUp },
  { id: "audit", label: "Audit Trail", icon: History },
  { id: "sources", label: "Data Sources", icon: Database },
  { id: "learning", label: "Feedback Learning", icon: RefreshCw }
];

const emptySummary: Summary = {
  total: 0,
  capex: 0,
  opex: 0,
  review: 0,
  overrides: 0,
  total_hours: 0,
  capex_hours: 0,
  opex_hours: 0,
  review_hours: 0,
  capitalisation_pct: 0,
  estimated_recovery_usd: 0,
  docx_records: 0,
  docx_matched_excel: 0,
  docx_match_pct: 0
};

function money(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0
  }).format(value || 0);
}

function number(value: number): string {
  if (!Number.isFinite(value)) return "0";
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 }).format(value);
}

function classNameFor(value: Classification): string {
  return value === "CapEx" ? "capex" : value === "OpEx" ? "opex" : "review";
}

function pct(value: number): string {
  return `${number(value)}%`;
}

function addNamedValue(map: Map<string, NamedValue>, name: string, line: DraftLine) {
  const item = map.get(name) ?? {
    name,
    hours: 0,
    capexHours: 0,
    opexHours: 0,
    confidenceTotal: 0,
    count: 0
  };
  item.hours += line.hours;
  item.capexHours += line.classification === "CapEx" ? line.hours : 0;
  item.opexHours += line.classification === "OpEx" ? line.hours : 0;
  item.confidenceTotal += line.confidence;
  item.count += 1;
  map.set(name, item);
}

function topItems(map: Map<string, NamedValue>): NamedValue[] {
  return Array.from(map.values()).sort((left, right) => right.hours - left.hours).slice(0, 6);
}

function buildKeywordCloud(lines: DraftLine[]): Array<{ word: string; weight: number }> {
  const stop = new Set([
    "the", "and", "for", "with", "this", "that", "from", "under", "when", "into", "work",
    "activity", "project", "classification", "confidence", "registered", "fixed", "asset",
    "policy", "hours", "signal", "signals", "capex", "opex", "tied", "line", "item"
  ]);
  const counts = new Map<string, number>();
  for (const line of lines) {
    const text = `${line.project_name} ${line.activity_type} ${line.evidence_summary}`.toLowerCase();
    for (const word of text.match(/[a-z][a-z-]{3,}/g) ?? []) {
      if (stop.has(word)) continue;
      counts.set(word, (counts.get(word) ?? 0) + 1);
    }
  }
  return Array.from(counts.entries())
    .sort((left, right) => right[1] - left[1])
    .slice(0, 18)
    .map(([word, weight]) => ({ word, weight }));
}

function buildEmployeeProfiles(drafts: Draft[]): EmployeeProfile[] {
  const grouped = new Map<string, Draft[]>();
  for (const draft of drafts) {
    const bucket = grouped.get(draft.employee_id) ?? [];
    bucket.push(draft);
    grouped.set(draft.employee_id, bucket);
  }

  return Array.from(grouped.entries())
    .map(([employeeId, weeks]) => {
      const sortedWeeks = weeks.sort((left, right) => left.week_start.localeCompare(right.week_start));
      const first = sortedWeeks[0];
      const lines = sortedWeeks.flatMap((week) => week.line_items);
      const projectMap = new Map<string, NamedValue>();
      const activityMap = new Map<string, NamedValue>();
      for (const line of lines) {
        addNamedValue(projectMap, line.project_code, line);
        addNamedValue(activityMap, line.activity_type, line);
      }
      const totalHours = sortedWeeks.reduce((sum, week) => sum + week.total_hours, 0);
      const capexHours = sortedWeeks.reduce((sum, week) => sum + week.capex_hours, 0);
      const opexHours = sortedWeeks.reduce((sum, week) => sum + week.opex_hours, 0);
      const confidenceValues = lines.map((line) => line.confidence);
      return {
        employeeId,
        employeeName: first.employee_name,
        jobTitle: first.job_title,
        jobFamily: first.job_family,
        teamName: first.team_name,
        managerId: first.manager_id,
        weeks: sortedWeeks,
        totalHours,
        capexHours,
        opexHours,
        capitalisationPct: totalHours ? (capexHours / totalHours) * 100 : 0,
        avgConfidence: confidenceValues.length
          ? confidenceValues.reduce((sum, value) => sum + value, 0) / confidenceValues.length
          : 0,
        projectMix: topItems(projectMap),
        activityMix: topItems(activityMap),
        keywordCloud: buildKeywordCloud(lines)
      };
    })
    .sort((left, right) => right.totalHours - left.totalHours);
}

function effectiveClassification(record: RecordItem): Classification {
  return record._override ?? record._classification;
}

function draftKey(draft: Draft): string {
  return `${draft.employee_id}::${draft.week_start}`;
}

function fuzzyScore(value: string, query: string): number | null {
  const target = value.toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
  const tokens = query
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim()
    .split(/\s+/)
    .filter(Boolean);
  if (!tokens.length) return 0;

  let score = 0;
  for (const token of tokens) {
    const exactIndex = target.indexOf(token);
    if (exactIndex >= 0) {
      score += exactIndex;
      continue;
    }
    if (/^\d+$/.test(token)) return null;

    let tokenIndex = 0;
    let firstMatch = -1;
    let lastMatch = -1;
    for (let targetIndex = 0; targetIndex < target.length; targetIndex += 1) {
      if (target[targetIndex] === token[tokenIndex]) {
        if (firstMatch < 0) firstMatch = targetIndex;
        lastMatch = targetIndex;
        tokenIndex += 1;
        if (tokenIndex === token.length) break;
      }
    }
    if (tokenIndex !== token.length) return null;
    score += 100 + firstMatch + Math.max(0, lastMatch - firstMatch - token.length);
  }
  return score;
}

function recordQuality(record: RecordItem): "Clean" | "Review" {
  const status = record._rowQuality?.status?.toLowerCase();
  return status && status !== "clean" ? "Review" : "Clean";
}

function buildProjectRecordGroups(records: RecordItem[]): ProjectRecordGroup[] {
  const rows = records.filter(
    (record) => (record._source ?? "") === "Excel" || ((record._source ?? "") === "DOCX form" && !Number(record._matchedExcel || 0))
  );
  const projectMap = new Map<string, ProjectRecordGroup>();

  for (const record of rows) {
    const projectCode = record.project_code || "Unmapped Project";
    const classification = effectiveClassification(record);
    const hours = Number(record.hours_allocated || 0);
    const project = projectMap.get(projectCode) ?? {
      projectCode,
      projectName: record.project_name || "Unknown project",
      totalHours: 0,
      capexHours: 0,
      opexHours: 0,
      reviewHours: 0,
      employees: []
    };
    project.totalHours += hours;
    if (classification === "CapEx") project.capexHours += hours;
    if (classification === "OpEx") project.opexHours += hours;
    if (classification === "Review") project.reviewHours += hours;

    let employee = project.employees.find((item) => item.employeeId === record.employee_id);
    if (!employee) {
      employee = {
        employeeId: record.employee_id,
        employeeName: record.full_name,
        jobTitle: record.job_title,
        teamName: record.team_name,
        hours: 0,
        avgConfidence: 0,
        classifications: new Set<Classification>(),
        records: []
      };
      project.employees.push(employee);
    }
    employee.hours += hours;
    employee.records.push(record);
    employee.classifications.add(classification);
    employee.avgConfidence =
      employee.records.reduce((sum, row) => sum + Number(row._confidence || 0), 0) / employee.records.length;

    projectMap.set(projectCode, project);
  }

  return Array.from(projectMap.values())
    .map((project) => ({
      ...project,
      employees: project.employees.sort((left, right) => right.hours - left.hours)
    }))
    .sort((left, right) => right.totalHours - left.totalHours);
}

export default function Page() {
  const [activeTab, setActiveTab] = useState<TabId>("dashboard");
  const [summary, setSummary] = useState<Summary>(emptySummary);
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [escalations, setEscalations] = useState<EscalationGroup[]>([]);
  const [connectors, setConnectors] = useState<Connector[]>([]);
  const [records, setRecords] = useState<RecordItem[]>([]);
  const [selectedRecord, setSelectedRecord] = useState<RecordItem | null>(null);
  const [selectedEmployeeId, setSelectedEmployeeId] = useState("");
  const [selectedReviewEmployeeId, setSelectedReviewEmployeeId] = useState("");
  const [employeeSearch, setEmployeeSearch] = useState("");
  const [reviewEmployeeSearch, setReviewEmployeeSearch] = useState("");
  const [recordFilter, setRecordFilter] = useState<RecordFilter>("All");
  const [sourceFilter, setSourceFilter] = useState<SourceFilter>("All");
  const [expandedRecordUid, setExpandedRecordUid] = useState("");
  const [sourceSubTab, setSourceSubTab] = useState<SourceSubTab>("connectors");
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState("Ready");

  const apiBase = appConfig.apiBaseUrl.replace(/\/$/, "");

  async function loadAll() {
    const [summaryRes, draftsRes, escalationRes, connectorsRes, recordsRes] = await Promise.all([
      fetch(`${apiBase}/api/summary`),
      fetch(`${apiBase}/api/drafts`),
      fetch(`${apiBase}/api/escalations`),
      fetch(`${apiBase}/api/connectors`),
      fetch(`${apiBase}/api/records?limit=1000`)
    ]);
    if (summaryRes.ok) setSummary(await summaryRes.json());
    if (draftsRes.ok) setDrafts((await draftsRes.json()).drafts ?? []);
    if (escalationRes.ok) setEscalations((await escalationRes.json()).escalations ?? []);
    if (connectorsRes.ok) setConnectors((await connectorsRes.json()).connectors ?? []);
    if (recordsRes.ok) setRecords((await recordsRes.json()).records ?? []);
  }

  useEffect(() => {
    loadAll().catch(() => setStatus("Backend unavailable"));
  }, []);

  async function uploadFile(kind: "excel" | "forms", file?: File) {
    if (!file) return;
    setBusy(true);
    setStatus(`Uploading ${file.name}`);
    const body = new FormData();
    body.append("file", file);
    try {
      const submitRes = await fetch(`${apiBase}/api/upload/${kind}`, { method: "POST", body });
      if (!submitRes.ok) throw new Error(await submitRes.text());
      const job = await submitRes.json();
      setStatus(`Queued ${job.source_file_name}`);
      await pollJob(job.job_id);
      await loadAll();
      setStatus(`Completed ${job.source_file_name}`);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  async function pollJob(jobId: string) {
    for (let attempt = 0; attempt < 180; attempt += 1) {
      const res = await fetch(`${apiBase}/api/upload/jobs/${jobId}`);
      if (!res.ok) throw new Error("Job status request failed");
      const job = await res.json();
      setStatus(`${job.stage}: ${job.classified}/${job.processed || "?"} classified`);
      if (job.status === "completed") return;
      if (job.status === "failed") throw new Error(job.error ?? "Ingestion job failed");
      await new Promise((resolve) => setTimeout(resolve, 750));
    }
    throw new Error("Timed out waiting for ingestion job");
  }

  async function overrideRecord(recordUid: string, classification: Classification | null) {
    const note = classification === null
      ? "Manual override cleared"
      : classification === "Review"
        ? "Returned to team lead review"
        : "Team lead correction";
    const res = await fetch(`${apiBase}/api/records/${recordUid}/override`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ classification, note })
    });
    if (res.ok) {
      await loadAll();
      setStatus(classification ? `Override saved: ${classification}` : "Override cleared");
    }
  }

  async function updateRecord(recordUid: string, request: {
    classification?: Classification;
    project_code?: string;
    holiday_days?: number;
    pto_days?: number;
    sick_days?: number;
    submission_notes?: string;
    note?: string;
  }) {
    const res = await fetch(`${apiBase}/api/records/${recordUid}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request)
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  }

  async function submitEmployeeDraft(recordUids: string[]) {
    const res = await fetch(`${apiBase}/api/drafts/submit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ record_uids: recordUids, note: "Employee submitted weekly draft" })
    });
    if (!res.ok) throw new Error(await res.text());
    const result = await res.json();
    await loadAll();
    setStatus(`Submitted ${result.submitted ?? recordUids.length} reviewed line items`);
  }

  async function loadAudit(record: RecordItem) {
    setSelectedRecord(record);
    setActiveTab("audit");
    const res = await fetch(`${apiBase}/api/audit/${record._recordUid}`);
    if (res.ok) setAuditEvents((await res.json()).events ?? []);
  }

  const employeeProfiles = useMemo(() => buildEmployeeProfiles(drafts), [drafts]);
  const projectRecordGroups = useMemo(() => buildProjectRecordGroups(records), [records]);
  const activityRecords = useMemo(
    () => records.filter((record) => recordFilter === "All" || effectiveClassification(record) === recordFilter),
    [records, recordFilter]
  );
  const feedbackEvents = useMemo(
    () => records.filter((record) => Boolean(record._override)),
    [records]
  );
  const selectedEmployee = useMemo(
    () => employeeProfiles.find((profile) => profile.employeeId === selectedEmployeeId) ?? (employeeProfiles.length > 0 ? employeeProfiles[0] : undefined),
    [employeeProfiles, selectedEmployeeId]
  );
  const selectedReviewEmployee = useMemo(
    () => employeeProfiles.find((profile) => profile.employeeId === selectedReviewEmployeeId) ?? (employeeProfiles.length > 0 ? employeeProfiles[0] : undefined),
    [employeeProfiles, selectedReviewEmployeeId]
  );

  useEffect(() => {
    if (!selectedEmployeeId && employeeProfiles[0]) {
      setSelectedEmployeeId(employeeProfiles[0].employeeId);
    }
  }, [employeeProfiles, selectedEmployeeId]);

  useEffect(() => {
    if (!selectedReviewEmployeeId && employeeProfiles[0]) {
      setSelectedReviewEmployeeId(employeeProfiles[0].employeeId);
    }
  }, [employeeProfiles, selectedReviewEmployeeId]);

  return (
    <main className="app-shell">
      <aside className="left-rail">
        <div className="brand-block">
          <div className="brand-mark" aria-label="Verizon icon">V</div>
          <div>
            <h1>EAC</h1>
            <span>Labor Timesheets</span>
          </div>
        </div>
        <nav className="nav-list">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                className={`nav-item ${activeTab === tab.id ? "active" : ""}`}
                onClick={() => setActiveTab(tab.id)}
              >
                <Icon size={17} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
        <div className="rail-footer">
          <ShieldCheck size={16} />
          <span>{appConfig.ruleVersion}</span>
        </div>
      </aside>

      <section className="workspace">
        <header className="top-nav">
          <div>
            <strong>Project Coder Weekly Timesheet</strong>
          </div>
          <button className="icon-button" onClick={loadAll} disabled={busy} title="Refresh">
            <RefreshCw size={18} />
          </button>
        </header>

        <div className="content">
          {activeTab === "dashboard" && (
            <section className="page-stack">
              <div className="page-header">
                <div>
                  <h2>Capitalisation Shift</h2>
                  <p>Baseline is 100% OpEx. Classified hours show recovered CapEx opportunity.</p>
                </div>
              </div>
              <div className="metric-grid">
                <Metric label="Total hours" value={number(summary.total_hours)} icon={ClipboardCheck} />
                <Metric label="CapEx hours" value={number(summary.capex_hours)} icon={CheckCircle2} tone="capex" />
                <Metric label="OpEx hours" value={number(summary.opex_hours)} icon={ShieldCheck} tone="opex" />
                <Metric label="Capitalisation" value={`${number(summary.capitalisation_pct)}%`} icon={BarChart3} />
                <Metric label="Escalated rows" value={number(summary.review)} icon={AlertTriangle} tone="review" />
                <Metric label="Recovery estimate" value={money(summary.estimated_recovery_usd)} icon={Database} />
              </div>
              <div className="band">
                <div className="bar">
                  <span style={{ width: `${summary.capitalisation_pct}%` }} />
                </div>
                <div className="split-labels">
                  <span>CapEx {number(summary.capex_hours)}h</span>
                  <span>OpEx {number(summary.opex_hours)}h</span>
                  <span>Review {number(summary.review_hours)}h</span>
                </div>
              </div>
              <DashboardOverview summary={summary} groups={projectRecordGroups} />
            </section>
          )}

          {activeTab === "records" && (
            <ActivityRecordsView
              records={activityRecords}
              filter={recordFilter}
              onFilter={setRecordFilter}
              sourceFilter={sourceFilter}
              onSourceFilter={setSourceFilter}
              expandedRecordUid={expandedRecordUid}
              onToggleRecord={(recordUid) =>
                setExpandedRecordUid((current) => (current === recordUid ? "" : recordUid))
              }
              onAudit={(record) => loadAudit(record)}
              onOverride={overrideRecord}
            />
          )}

          {activeTab === "analytics" && (
            <AnalyticsView
              records={records}
              summary={summary}
              projectGroups={projectRecordGroups}
              feedbackEvents={feedbackEvents}
            />
          )}

          {activeTab === "sources" && (
            <DataSourcesView
              activeSubTab={sourceSubTab}
              onSubTab={setSourceSubTab}
              busy={busy}
              status={status}
              records={records}
              summary={summary}
              connectors={connectors}
              onUpload={uploadFile}
            />
          )}

          {activeTab === "learning" && (
            <LearningView
              records={records}
              feedbackEvents={feedbackEvents}
              onAudit={(record) => loadAudit(record)}
            />
          )}

          {activeTab === "review" && (
            <section className="page-stack">
              <div className="page-header">
                <div>
                  <h2>Employee Review</h2>
                  <p>Review the pre-populated weekly draft, edit classification/project code/notes, and submit the corrected packet.</p>
                </div>
              </div>
              <EmployeeReviewWorkspace
                profiles={employeeProfiles}
                selectedEmployee={selectedReviewEmployee}
                selectedEmployeeId={selectedReviewEmployeeId}
                search={reviewEmployeeSearch}
                records={records}
                onSearch={setReviewEmployeeSearch}
                onSelectEmployee={setSelectedReviewEmployeeId}
                onAudit={(line) => {
                  const record = records.find((item) => item._recordUid === line.record_uid);
                  if (record) loadAudit(record);
                }}
                onSaveLine={updateRecord}
                onSubmitDraft={submitEmployeeDraft}
              />
            </section>
          )}

          {activeTab === "drafts" && (
            <section className="page-stack">
              <div className="page-header">
                <div>
                  <h2>Employee Directory</h2>
                  <p>Search employees A-Z and review timesheet history, weekly project allocation, and CapEx / OpEx contribution.</p>
                </div>
              </div>
              <EmployeeDirectoryWorkspace
                profiles={employeeProfiles}
                selectedEmployee={selectedEmployee}
                selectedEmployeeId={selectedEmployeeId}
                search={employeeSearch}
                records={records}
                onSearch={setEmployeeSearch}
                onSelectEmployee={setSelectedEmployeeId}
                onAudit={(line) => {
                    const record = records.find((item) => item._recordUid === line.record_uid);
                    if (record) loadAudit(record);
                }}
              />
            </section>
          )}

          {activeTab === "escalations" && (
            <section className="page-stack">
              <div className="page-header">
                <div>
                  <h2>Team Lead Escalation</h2>
                  <p>Low-confidence or ambiguous records are routed here before employee review.</p>
                </div>
              </div>
              {escalations.map((group) => (
                <article className="panel" key={group.manager_id}>
                  <div className="draft-head">
                    <div>
                      <h3>{group.manager_id}</h3>
                      <p>{group.records.length} records · {number(group.hours)} hours</p>
                    </div>
                  </div>
                  <div className="table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th aria-label="Expand" />
                          <th>Employee</th>
                          <th>Week</th>
                          <th>Project</th>
                          <th>Activity</th>
                          <th>Hours</th>
                          <th>Confidence</th>
                          <th>Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {group.records.map((record) => {
                          const expanded = expandedRecordUid === record._recordUid;
                          return (
                            <Fragment key={record._recordUid}>
                              <tr
                                className={expanded ? "expanded-parent" : ""}
                                onClick={() =>
                                  setExpandedRecordUid((current) => current === record._recordUid ? "" : record._recordUid)
                                }
                              >
                                <td className="expand-cell">
                                  <button
                                    aria-label={expanded ? "Collapse record" : "Expand record"}
                                    onClick={(event) => {
                                      event.stopPropagation();
                                      setExpandedRecordUid((current) => current === record._recordUid ? "" : record._recordUid);
                                    }}
                                  >
                                    {expanded ? "v" : ">"}
                                  </button>
                                </td>
                                <td>{record.full_name}</td>
                                <td>{record.week_start_date}</td>
                                <td>{record.project_code}</td>
                                <td>{record.activity_type}</td>
                                <td>{record.hours_allocated}</td>
                                <td>{record._confidence}</td>
                                <td className="actions" onClick={(event) => event.stopPropagation()}>
                                  <button onClick={() => overrideRecord(record._recordUid, "CapEx")}>CapEx</button>
                                  <button onClick={() => overrideRecord(record._recordUid, "OpEx")}>OpEx</button>
                                  <button onClick={() => loadAudit(record)}>Audit</button>
                                </td>
                              </tr>
                              {expanded && (
                                <tr className="expanded-row escalation-expanded-row">
                                  <td colSpan={8}>
                                    <ExpandedTimesheetRecord record={record} onAudit={(item) => loadAudit(item)} />
                                  </td>
                                </tr>
                              )}
                            </Fragment>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </article>
              ))}
            </section>
          )}

          {activeTab === "audit" && (
            <AuditView
              records={records}
              selectedRecord={selectedRecord}
              auditEvents={auditEvents}
              onSelectRecord={loadAudit}
            />
          )}
        </div>
      </section>
    </main>
  );
}

function sourceCounts(records: RecordItem[]) {
  return {
    total: records.length,
    capex: records.filter((record) => effectiveClassification(record) === "CapEx").length,
    opex: records.filter((record) => effectiveClassification(record) === "OpEx").length,
    review: records.filter((record) => effectiveClassification(record) === "Review").length,
    matched: records.filter((record) => Number(record._matchedExcel || 0) > 0).length
  };
}

function DataSourcesView({
  activeSubTab,
  onSubTab,
  busy,
  status,
  records,
  summary,
  connectors,
  onUpload
}: {
  activeSubTab: SourceSubTab;
  onSubTab: (tab: SourceSubTab) => void;
  busy: boolean;
  status: string;
  records: RecordItem[];
  summary: Summary;
  connectors: Connector[];
  onUpload: (kind: "excel" | "forms", file?: File) => Promise<void>;
}) {
  const [selectedFiles, setSelectedFiles] = useState<{ excel?: File; forms?: File }>({});
  const [syncingKind, setSyncingKind] = useState<"excel" | "forms" | null>(null);
  const tabs: Array<{ id: SourceSubTab; label: string }> = [
    { id: "connectors", label: "Connectors" },
    { id: "pipeline", label: "Classification Pipeline" },
    { id: "validation", label: "Form Extraction Validation" }
  ];
  const excelRecords = records.filter((record) => (record._source ?? "") === "Excel");
  const formRecords = records.filter((record) => (record._source ?? "") === "DOCX form");
  const excelCounts = sourceCounts(excelRecords);
  const formCounts = sourceCounts(formRecords);
  const excelConnector = connectors.find((connector) => connector.source_type === "Excel");
  const formConnector = connectors.find((connector) => connector.source_type === "DOCX form");
  async function runSync(kind: "excel" | "forms") {
    const file = selectedFiles[kind];
    if (!file || busy) return;
    setSyncingKind(kind);
    try {
      await onUpload(kind, file);
      setSelectedFiles((current) => ({ ...current, [kind]: undefined }));
    } finally {
      setSyncingKind(null);
    }
  }

  return (
    <section className="page-stack data-source-page">
      <div className="page-header">
        <div>
          <h2>Data Sources</h2>
          <p>Connectors, enrichment pipeline, and form extraction validation.</p>
        </div>
        <div className="source-header-icon">
          <UploadCloud size={22} />
        </div>
      </div>

      <div className="source-subtabs">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            className={activeSubTab === tab.id ? "active" : ""}
            onClick={() => onSubTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeSubTab === "connectors" && (
        <>
          <section className="active-connectors-panel">
            <div className="active-connectors-head">
              <div>
                <h3>Active Connectors</h3>
                <p>Both produce the same NormalizedActivityRecord contract.</p>
              </div>
              <Layers3 size={22} />
            </div>
            <div className="active-connector-grid">
              <ActiveConnectorCard
                id="excel-source-upload"
                title="Excel Dataset Connector"
                subtitle="Primary workflow source · .xlsx / .xls"
                icon={FileSpreadsheet}
                accept=".xlsx,.xls"
                disabled={busy}
                kind="excel"
                selectedFile={selectedFiles.excel}
                isSyncing={syncingKind === "excel"}
                status={status}
                metrics={[
                  ["Records Loaded", excelCounts.total || excelConnector?.records_processed || 0],
                  ["CapEx", excelCounts.capex],
                  ["OpEx", excelCounts.opex],
                  ["Review", excelCounts.review]
                ]}
                lastSync={`${excelConnector?.records_processed ?? excelCounts.total} records`}
                onFile={(file) => setSelectedFiles((current) => ({ ...current, excel: file }))}
                onRun={() => runSync("excel")}
              />
              <ActiveConnectorCard
                id="form-source-upload"
                title="Form Document Parser"
                subtitle="Timesheet forms · .docx / .zip of DOCX"
                icon={FileText}
                accept=".docx,.zip"
                disabled={busy}
                kind="forms"
                dropLabel="Drop one .docx or a .zip batch here"
                selectedFile={selectedFiles.forms}
                isSyncing={syncingKind === "forms"}
                status={status}
                metrics={[
                  ["Records Loaded", formCounts.total || formConnector?.records_processed || 0],
                  ["CapEx", formCounts.capex],
                  ["OpEx", formCounts.opex],
                  ["Matched", formCounts.matched || summary.docx_matched_excel]
                ]}
                lastSync={`${formConnector?.records_processed ?? formCounts.total} records`}
                onFile={(file) => setSelectedFiles((current) => ({ ...current, forms: file }))}
                onRun={() => runSync("forms")}
              />
            </div>
          </section>
          <ConnectorCatalog />
        </>
      )}

      {activeSubTab === "pipeline" && (
        <div className="pipeline-tab-stack">
          <section className="active-connectors-panel">
            <div className="active-connectors-head">
              <div>
                <h3>Shared Enrichment Path</h3>
                <p>Both Excel and DOCX data follow the same normalization path before the engine sees records.</p>
              </div>
              <TrendingUp size={22} />
            </div>
            <div className="pipeline-strip">
              {[
                "Source intake",
                "Schema validation",
                "Field normalization",
                "Context injection",
                "Semantic retrieval",
                "Rules overlay",
                "Classification",
                "Confidence routing",
                "Audit write",
                "Feedback capture"
              ].map((step) => (
                <div className="pipe-node" key={step}>
                  <CheckCircle2 size={16} />
                  <span>{step}</span>
                </div>
              ))}
            </div>
          </section>

          <section className="active-connectors-panel">
            <div className="active-connectors-head">
              <div>
                <h3>Agent Responsibilities</h3>
                <p>LangGraph stages stay source-agnostic and operate on the canonical weekly timesheet record.</p>
              </div>
              <Layers3 size={22} />
            </div>
            <div className="pipeline-card-grid">
              {[
                ["1", "Harvesting Agent", "Accepts connector records, validates schema, stamps source metadata, and stages clean line items."],
                ["2", "Context Enrichment Agent", "Builds weekly employee/project context from meetings, tickets, commits, system activity, and notes."],
                ["3", "Semantic Retrieval Agent", "Looks up similar reviewed patterns. In POC this can be stubbed from historical/synthetic context."],
                ["4", "Policy & Rules Agent", "Applies fixed-asset rules, project-code constraints, and activity-type capitalization logic."],
                ["5", "Classification Agent", "Produces CapEx / OpEx / Review output with confidence, evidence, rule version, and signal ledger."],
                ["6", "Confidence Routing Agent", "Sends high-confidence rows to employee drafts and low-confidence rows to team lead escalation."]
              ].map(([step, title, description]) => (
                <article className="pipeline-card" key={step}>
                  <span>{step}</span>
                  <strong>{title}</strong>
                  <p>{description}</p>
                </article>
              ))}
            </div>
          </section>

          <section className="active-connectors-panel pipeline-runtime-panel">
            <div className="active-connectors-head">
              <div>
                <h3>Runtime Contract</h3>
                <p>Current pipeline settings and active POC boundaries.</p>
              </div>
              <ShieldCheck size={22} />
            </div>
            <div className="pipeline-runtime-grid">
              <div><span>Canonical records</span><strong>{records.length}</strong></div>
              <div><span>Excel records</span><strong>{excelRecords.length}</strong></div>
              <div><span>DOCX form records</span><strong>{formRecords.length}</strong></div>
              <div><span>Review gate</span><strong>{appConfig.reviewThreshold}%</strong></div>
              <div><span>Rule version</span><strong>{appConfig.ruleVersion}</strong></div>
              <div><span>Decision authority</span><strong>{appConfig.decisionAuthorityLabel}</strong></div>
              <div><span>Output mode</span><strong>Weekly</strong></div>
              <div><span>Escalated rows</span><strong>{summary.review}</strong></div>
            </div>
          </section>
        </div>
      )}

      {activeSubTab === "validation" && (
        <FormExtractionValidation records={records} summary={summary} />
      )}
    </section>
  );
}

const canonicalComparisonFields: Array<{ key: keyof RecordItem; label: string }> = [
  { key: "employee_id", label: "Employee ID" },
  { key: "full_name", label: "Full Name" },
  { key: "job_title", label: "Job Title" },
  { key: "job_family", label: "Job Family" },
  { key: "team_name", label: "Team" },
  { key: "org_unit", label: "Org Unit" },
  { key: "manager_id", label: "Manager ID" },
  { key: "week_start_date", label: "Week Start Date" },
  { key: "week_end_date", label: "Week End Date" },
  { key: "standard_days", label: "Standard Days" },
  { key: "holiday_days", label: "Holiday Days" },
  { key: "pto_days", label: "PTO Days" },
  { key: "sick_days", label: "Sick Days" },
  { key: "actual_working_days", label: "Actual Working Days" },
  { key: "meeting_count", label: "Meeting Count" },
  { key: "ticket_count", label: "Ticket Count" },
  { key: "email_volume", label: "Email Volume" },
  { key: "code_commit_count", label: "Code Commit Count" },
  { key: "system_activity_score", label: "System Activity Score" },
  { key: "project_code", label: "Project Code" },
  { key: "project_name", label: "Project Name" },
  { key: "activity_type", label: "Activity Type" },
  { key: "hours_allocated", label: "Hours Allocated" },
  { key: "submission_notes", label: "Submission Notes" }
];

function comparableValue(value: unknown): string {
  if (value === null || value === undefined) return "";
  const text = String(value).trim();
  const numeric = Number(text.replace(/,/g, ""));
  if (text !== "" && Number.isFinite(numeric)) return String(Number(numeric.toFixed(6)));
  return text.toLowerCase();
}

function displayValue(value: unknown): string {
  if (value === null || value === undefined || value === "") return "-";
  return String(value);
}

function sameCanonicalRecord(left: RecordItem, right: RecordItem): boolean {
  if (left._key && right._key) return left._key === right._key;
  return (
    left.employee_id === right.employee_id &&
    left.week_start_date === right.week_start_date &&
    left.project_code === right.project_code &&
    left.activity_type === right.activity_type
  );
}

function FormExtractionValidation({ records, summary }: { records: RecordItem[]; summary: Summary }) {
  const formRecords = useMemo(
    () => records.filter((record) => (record._source ?? "") === "DOCX form"),
    [records]
  );
  const excelRecords = useMemo(
    () => records.filter((record) => (record._source ?? "") === "Excel"),
    [records]
  );
  const [selectedRecordUid, setSelectedRecordUid] = useState("");
  const selectedRecord = formRecords.find((record) => record._recordUid === selectedRecordUid) ?? formRecords[0];
  const matchedExcelRecord = selectedRecord
    ? excelRecords.find((record) => sameCanonicalRecord(selectedRecord, record))
    : undefined;

  useEffect(() => {
    if (!selectedRecordUid && formRecords[0]) {
      setSelectedRecordUid(formRecords[0]._recordUid);
    }
  }, [formRecords, selectedRecordUid]);

  const comparisonRows = selectedRecord
    ? canonicalComparisonFields.map(({ key, label }) => {
      const formValue = selectedRecord[key];
      const excelValue = matchedExcelRecord?.[key];
      const formComparable = comparableValue(formValue);
      const excelComparable = comparableValue(excelValue);
      const bothEmpty = !formComparable && !excelComparable;
      const match = Boolean(matchedExcelRecord) && !bothEmpty && formComparable === excelComparable;
      return { key: String(key), label, formValue, excelValue, match, bothEmpty };
    })
    : [];
  const comparableRows = comparisonRows.filter((row) => !row.bothEmpty);
  const matchedFields = comparableRows.filter((row) => row.match).length;
  const agreementPct = comparableRows.length ? (matchedFields / comparableRows.length) * 100 : 0;
  const extractionValues = formRecords.map((record) => Number(record._extractionConfidence || 0)).filter((value) => value > 0);
  const avgExtraction = extractionValues.length
    ? extractionValues.reduce((sum, value) => sum + value, 0) / extractionValues.length
    : 0;
  const extractedFields = selectedRecord?._formValidation?.extractedFields ?? comparableRows.filter((row) => comparableValue(row.formValue)).length;
  const totalFields = selectedRecord?._formValidation?.totalFields ?? canonicalComparisonFields.length;
  const matchedCount = formRecords.filter((record) =>
    Number(record._matchedExcel || 0) > 0 || excelRecords.some((excelRecord) => sameCanonicalRecord(record, excelRecord))
  ).length || summary.docx_matched_excel;

  return (
    <section className="active-connectors-panel form-validation-panel">
      <div className="active-connectors-head">
        <div>
          <h3>Form Extraction Validation</h3>
          <p>Parser output keyed against the Excel workbook using the canonical timesheet schema.</p>
        </div>
        <ShieldCheck size={22} />
      </div>

      <div className="validation-summary-grid">
        <ValidationStat label="Forms parsed" value={number(formRecords.length)} />
        <ValidationStat label="Matched dataset" value={`${number(matchedCount)}/${number(formRecords.length)}`} />
        <ValidationStat label="Avg extraction" value={pct(avgExtraction)} />
        <ValidationStat label="Excel mapping rows" value={number(excelRecords.length)} />
      </div>

      <div className="form-compare-selector">
        <div>
          <strong>Compare one form line to its Excel row</strong>
          <span>Each field should line up to the same canonical schema.</span>
        </div>
        <select
          value={selectedRecord?._recordUid ?? ""}
          onChange={(event) => setSelectedRecordUid(event.target.value)}
        >
          {formRecords.map((record) => (
            <option key={record._recordUid} value={record._recordUid}>
              {record._sourceFileName ?? "DOCX form"} · {record.employee_id} · {record.project_code} · {record.activity_type}
            </option>
          ))}
        </select>
      </div>

      {!selectedRecord && (
        <div className="validation-empty">
          <strong>No DOCX form records loaded</strong>
          <p>Upload the sample timesheets, then return here to compare parsed forms against Excel rows.</p>
        </div>
      )}

      {selectedRecord && (
        <>
          <div className="selected-form-head">
            <div>
              <h3>{selectedRecord._sourceFileName ?? "DOCX form"}</h3>
              <p>{selectedRecord._key ?? `${selectedRecord.employee_id}::${selectedRecord.week_start_date}::${selectedRecord.project_code}`}</p>
            </div>
            <span className={`badge ${matchedExcelRecord ? "capex" : "review"}`}>
              {matchedExcelRecord ? "Matched" : "Unmatched"}
            </span>
            <strong>{pct(agreementPct)}</strong>
          </div>

          <div className="validation-detail-grid">
            <ValidationStat label="Fields extracted" value={`${number(extractedFields)}/${number(totalFields)}`} />
            <ValidationStat label="Excel value agreement" value={`${number(matchedFields)}/${number(comparableRows.length)}`} />
            <ValidationStat label="Form confidence" value={number(selectedRecord._extractionConfidence ?? 0)} />
            <ValidationStat label="Excel row found" value={matchedExcelRecord ? "Yes" : "No"} />
          </div>

          <div className="records-table-wrap validation-table-wrap">
            <table className="validation-table">
              <thead>
                <tr>
                  <th>Field</th>
                  <th>Form Value</th>
                  <th>Excel Value</th>
                  <th>Match</th>
                </tr>
              </thead>
              <tbody>
                {comparisonRows.map((row) => (
                  <tr key={row.key}>
                    <td>{row.label}</td>
                    <td>{displayValue(row.formValue)}</td>
                    <td>{displayValue(row.excelValue)}</td>
                    <td>
                      <span className={`badge ${row.match ? "capex" : row.bothEmpty ? "opex" : "review"}`}>
                        {row.match ? "Match" : row.bothEmpty ? "Blank" : "Diff"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </section>
  );
}

function ValidationStat({ label, value }: { label: string; value: string }) {
  return (
    <article className="validation-stat">
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

function ActiveConnectorCard({
  id,
  title,
  subtitle,
  icon: Icon,
  accept,
  disabled,
  kind,
  dropLabel,
  selectedFile,
  isSyncing,
  status,
  metrics,
  lastSync,
  onFile,
  onRun
}: {
  id: string;
  title: string;
  subtitle: string;
  icon: LucideIcon;
  accept: string;
  disabled: boolean;
  kind: "excel" | "forms";
  dropLabel?: string;
  selectedFile?: File;
  isSyncing: boolean;
  status: string;
  metrics: Array<[string, number]>;
  lastSync: string;
  onFile: (file?: File) => void;
  onRun: () => void;
}) {
  return (
    <article className="active-connector-card">
      <input
        id={id}
        type="file"
        accept={accept}
        disabled={disabled}
        onChange={(event: ChangeEvent<HTMLInputElement>) => {
          onFile(event.target.files?.[0]);
          event.currentTarget.value = "";
        }}
      />
      <div className="connector-main-head">
        <div className="connector-icon active">
          <Icon size={22} />
        </div>
        <div>
          <strong>{title}</strong>
          <span>{subtitle}</span>
        </div>
        <i aria-label="Connector online" />
      </div>
      <div className="connector-metrics">
        {metrics.map(([label, value]) => (
          <div key={label}>
            <strong>{number(value)}</strong>
            <span>{label}</span>
          </div>
        ))}
      </div>
      <label
        className="connector-dropzone"
        htmlFor={id}
        onDragOver={(event) => event.preventDefault()}
        onDrop={(event) => {
          event.preventDefault();
          if (!disabled) onFile(event.dataTransfer.files?.[0]);
        }}
      >
        <UploadCloud size={22} />
        <span>
          {selectedFile
            ? `Selected ${selectedFile.name}`
            : <>{dropLabel ?? `Drop ${accept.includes("xlsx") ? ".xlsx" : ".docx / .zip"} here`} or <b>browse</b></>}
        </span>
      </label>
      <div className="connector-card-footer">
        <span>{isSyncing ? status : selectedFile ? "File staged. Click Run Sync to ingest." : `Last sync: ${lastSync}`}</span>
        <button type="button" disabled={disabled || !selectedFile} onClick={onRun}>
          {isSyncing ? "Syncing..." : "Run Sync"}
        </button>
      </div>
      {isSyncing && (
        <div className="connector-progress" aria-label="Sync progress">
          <span />
        </div>
      )}
    </article>
  );
}

function ConnectorCatalog() {
  const sources: Array<{
    name: string;
    description: string;
    icon: LucideIcon;
  }> = [
    {
      name: "Google Drive",
      description: "Ingestion from shared drives and team folders",
      icon: UploadCloud
    },
    {
      name: "Google Sheets",
      description: "Planning tabs, allocation trackers, and review sheets",
      icon: FileSpreadsheet
    },
    {
      name: "SharePoint",
      description: "Document libraries and team sites",
      icon: FileText
    },
    {
      name: "BigQuery",
      description: "Warehouse-backed activity and finance records",
      icon: Database
    },
    {
      name: "Jira",
      description: "Work tracking, issue, and sprint data",
      icon: ClipboardCheck
    },
    {
      name: "Slack",
      description: "Message and workflow activity signals",
      icon: TrendingUp
    },
    {
      name: "Calendar",
      description: "Meetings, field visits, and delivery checkpoints",
      icon: CalendarDays
    },
    {
      name: "MCP Servers",
      description: "Model Context Protocol server integrations",
      icon: Layers3
    }
  ];

  return (
    <section className="connector-catalog-panel">
      <div className="catalog-title">
        <h3>Connector Catalog</h3>
        <span>Coming Soon</span>
      </div>
      <p>Planned integrations for future connectors.</p>
      <div className="catalog-grid">
        {sources.map((source) => {
          const Icon = source.icon;
          return (
            <article className="catalog-card" key={source.name}>
              <Icon size={22} />
              <strong>{source.name}</strong>
              <p>{source.description}</p>
            </article>
          );
        })}
      </div>
    </section>
  );
}

function DashboardOverview({ summary, groups }: { summary: Summary; groups: ProjectRecordGroup[] }) {
  const totalHours = summary.total_hours || groups.reduce((sum, group) => sum + group.totalHours, 0);
  const capexPct = totalHours ? (summary.capex_hours / totalHours) * 100 : 0;
  const opexPct = totalHours ? (summary.opex_hours / totalHours) * 100 : 0;
  const reviewPct = totalHours ? (summary.review_hours / totalHours) * 100 : 0;
  const capexEnd = capexPct;
  const opexEnd = capexPct + opexPct;
  const topProjects = groups.slice(0, 8);
  const reviewProjects = groups
    .filter((group) => group.reviewHours > 0)
    .sort((left, right) => right.reviewHours - left.reviewHours)
    .slice(0, 5);
  const weeklyTrend = Array.from(
    groups
      .flatMap((group) => group.employees.flatMap((employee) => employee.records))
      .reduce((map, record) => {
        const week = record.week_start_date || "Unmapped Week";
        const item = map.get(week) ?? { week, capex: 0, opex: 0, review: 0, total: 0 };
        const hours = Number(record.hours_allocated || 0);
        const classification = effectiveClassification(record);
        item.total += hours;
        if (classification === "CapEx") item.capex += hours;
        if (classification === "OpEx") item.opex += hours;
        if (classification === "Review") item.review += hours;
        map.set(week, item);
        return map;
      }, new Map<string, { week: string; capex: number; opex: number; review: number; total: number }>())
      .values()
  )
    .sort((left, right) => left.week.localeCompare(right.week))
    .slice(-10);
  const maxWeekHours = Math.max(...weeklyTrend.map((week) => week.total), 1);

  return (
    <section className="dashboard-overview">
      <div className="overview-grid">
        <article className="overview-panel portfolio-panel">
          <div className="section-title">
            <h4>Portfolio Classification Mix</h4>
            <span>Overall hours by accounting outcome</span>
          </div>
          <div className="portfolio-mix">
            <div
              className="portfolio-donut"
              style={{
                background: `conic-gradient(var(--capex) 0 ${capexEnd}%, var(--opex) ${capexEnd}% ${opexEnd}%, var(--review) ${opexEnd}% 100%)`
              }}
            >
              <strong>{pct(capexPct)}</strong>
              <span>CapEx</span>
            </div>
            <div className="mix-legend">
              <MixLegendItem label="CapEx" value={summary.capex_hours} percent={capexPct} tone="capex" />
              <MixLegendItem label="OpEx" value={summary.opex_hours} percent={opexPct} tone="opex" />
              <MixLegendItem label="Review" value={summary.review_hours} percent={reviewPct} tone="review" />
            </div>
          </div>
        </article>

        <article className="overview-panel">
          <div className="section-title">
            <h4>Project Portfolio Allocation</h4>
            <span>Highest-hour project codes with CapEx / OpEx / Review composition</span>
          </div>
          <div className="project-allocation-bars">
            {topProjects.map((project) => (
              <ProjectAllocationRow key={project.projectCode} project={project} totalHours={totalHours} />
            ))}
          </div>
        </article>
      </div>

      <div className="overview-grid lower">
        <article className="overview-panel">
          <div className="section-title">
            <h4>Weekly Capitalization Trend</h4>
            <span>Chronological CapEx / OpEx / Review movement</span>
          </div>
          <div className="weekly-trend">
            {weeklyTrend.map((week) => (
              <div className="weekly-trend-row" key={week.week}>
                <strong>{week.week}</strong>
                <div className="weekly-stack" style={{ width: `${Math.max((week.total / maxWeekHours) * 100, 4)}%` }}>
                  <span
                    className="capex"
                    data-tooltip={`CapEx: ${number(week.capex)}h - ${pct(week.total ? (week.capex / week.total) * 100 : 0)}`}
                    tabIndex={0}
                    aria-label={`CapEx ${number(week.capex)} hours, ${pct(week.total ? (week.capex / week.total) * 100 : 0)}`}
                    style={{ width: `${week.total ? (week.capex / week.total) * 100 : 0}%` }}
                  />
                  <span
                    className="opex"
                    data-tooltip={`OpEx: ${number(week.opex)}h - ${pct(week.total ? (week.opex / week.total) * 100 : 0)}`}
                    tabIndex={0}
                    aria-label={`OpEx ${number(week.opex)} hours, ${pct(week.total ? (week.opex / week.total) * 100 : 0)}`}
                    style={{ width: `${week.total ? (week.opex / week.total) * 100 : 0}%` }}
                  />
                  <span
                    className="review"
                    data-tooltip={`Review: ${number(week.review)}h - ${pct(week.total ? (week.review / week.total) * 100 : 0)}`}
                    tabIndex={0}
                    aria-label={`Review ${number(week.review)} hours, ${pct(week.total ? (week.review / week.total) * 100 : 0)}`}
                    style={{ width: `${week.total ? (week.review / week.total) * 100 : 0}%` }}
                  />
                </div>
                <em>{number(week.total)}h</em>
              </div>
            ))}
          </div>
          <div className="trend-legend">
            <span><i className="dot capex" /> CapEx</span>
            <span><i className="dot opex" /> OpEx</span>
            <span><i className="dot review" /> Review</span>
          </div>
        </article>

        <article className="overview-panel">
          <div className="section-title">
            <h4>Review Focus</h4>
            <span>Project codes with unresolved review hours</span>
          </div>
          <div className="review-focus-list">
            {(reviewProjects.length ? reviewProjects : topProjects.slice(0, 5)).map((project) => {
              const records = project.employees.flatMap((employee) => employee.records);
              const avgConfidence = records.length
                ? records.reduce((sum, record) => sum + Number(record._confidence || 0), 0) / records.length
                : 0;
              return (
                <div className="review-focus-row" key={project.projectCode}>
                  <span className={`dot ${project.reviewHours > 0 ? "review" : "capex"}`} />
                  <div>
                    <strong>{project.projectCode}</strong>
                    <span>{project.projectName}</span>
                  </div>
                  <b>{number(project.reviewHours)}h review</b>
                  <em>{number(avgConfidence)} confidence</em>
                </div>
              );
            })}
          </div>
        </article>
      </div>
    </section>
  );
}

function MixLegendItem({
  label,
  value,
  percent,
  tone
}: {
  label: string;
  value: number;
  percent: number;
  tone: "capex" | "opex" | "review";
}) {
  return (
    <div className="mix-legend-item">
      <span className={`dot ${tone}`} />
      <strong>{label}</strong>
      <em>{number(value)}h</em>
      <b>{pct(percent)}</b>
    </div>
  );
}

function ProjectAllocationRow({ project, totalHours }: { project: ProjectRecordGroup; totalHours: number }) {
  const capexPct = project.totalHours ? (project.capexHours / project.totalHours) * 100 : 0;
  const opexPct = project.totalHours ? (project.opexHours / project.totalHours) * 100 : 0;
  const reviewPct = project.totalHours ? (project.reviewHours / project.totalHours) * 100 : 0;
  const portfolioPct = totalHours ? (project.totalHours / totalHours) * 100 : 0;
  return (
    <article className="project-allocation-row">
      <div className="project-allocation-head">
        <div>
          <strong>{project.projectCode}</strong>
          <span>{project.projectName}</span>
        </div>
        <em>{number(project.totalHours)}h</em>
      </div>
      <div className="project-allocation-track" aria-label={`${project.projectCode} allocation`}>
        <span className="capex" style={{ width: `${capexPct}%` }} />
        <span className="opex" style={{ width: `${opexPct}%` }} />
        <span className="review" style={{ width: `${reviewPct}%` }} />
      </div>
      <div className="project-allocation-meta">
        <span>{pct(capexPct)} CapEx</span>
        <span>{number(project.opexHours)}h OpEx</span>
        <span>{project.employees.length} employees</span>
        <span>{pct(portfolioPct)} of portfolio</span>
      </div>
    </article>
  );
}

function AnalyticsView({
  records,
  summary,
  projectGroups,
  feedbackEvents
}: {
  records: RecordItem[];
  summary: Summary;
  projectGroups: ProjectRecordGroup[];
  feedbackEvents: RecordItem[];
}) {
  const reportingRecords = records.filter(
    (record) => (record._source ?? "") === "Excel" || ((record._source ?? "") === "DOCX form" && !Number(record._matchedExcel || 0))
  );
  const totalHours = summary.total_hours || reportingRecords.reduce((sum, record) => sum + Number(record.hours_allocated || 0), 0);

  const activityRows = Array.from(
    reportingRecords.reduce((map, record) => {
      const activity = record.activity_type || "Unknown activity";
      const item = map.get(activity) ?? { activity, capex: 0, opex: 0, review: 0, total: 0, confidence: 0, count: 0 };
      const hours = Number(record.hours_allocated || 0);
      const classification = effectiveClassification(record);
      item.total += hours;
      item.confidence += Number(record._confidence || 0);
      item.count += 1;
      if (classification === "CapEx") item.capex += hours;
      if (classification === "OpEx") item.opex += hours;
      if (classification === "Review") item.review += hours;
      map.set(activity, item);
      return map;
    }, new Map<string, { activity: string; capex: number; opex: number; review: number; total: number; confidence: number; count: number }>())
      .values()
  ).sort((left, right) => right.total - left.total).slice(0, 8);
  const maxActivityHours = Math.max(...activityRows.map((activity) => activity.total), 1);

  const employeeRows = Array.from(
    reportingRecords.reduce((map, record) => {
      const employeeId = record.employee_id || "Unknown";
      const item = map.get(employeeId) ?? { employeeId, employeeName: record.full_name || employeeId, hours: 0, records: [] as RecordItem[] };
      item.hours += Number(record.hours_allocated || 0);
      item.records.push(record);
      map.set(employeeId, item);
      return map;
    }, new Map<string, { employeeId: string; employeeName: string; hours: number; records: RecordItem[] }>())
      .values()
  ).sort((left, right) => right.hours - left.hours).slice(0, 8);
  const matrixProjects = projectGroups.slice(0, 6);
  const priorityProjects = projectGroups.map((project) => {
    const projectRecords = project.employees.flatMap((employee) => employee.records);
    const avgConfidence = projectRecords.length
      ? projectRecords.reduce((sum, record) => sum + Number(record._confidence || 0), 0) / projectRecords.length
      : 0;
    const capexShare = project.totalHours ? (project.capexHours / project.totalHours) * 100 : 0;
    const reviewShare = project.totalHours ? (project.reviewHours / project.totalHours) * 100 : 0;
    const priorityScore = project.reviewHours * 2 + Math.max(0, appConfig.reviewThreshold - avgConfidence) + project.totalHours * (reviewShare / 100);
    return { ...project, avgConfidence, capexShare, reviewShare, priorityScore };
  }).sort((left, right) => right.priorityScore - left.priorityScore).slice(0, 8);
  const maxCellHours = Math.max(
    ...employeeRows.flatMap((employee) =>
      matrixProjects.map((project) =>
        employee.records
          .filter((record) => (record.project_code || "Unmapped Project") === project.projectCode)
          .reduce((sum, record) => sum + Number(record.hours_allocated || 0), 0)
      )
    ),
    1
  );


  // Analytics metrics
  const totalCapexRecords = reportingRecords.filter((r) => effectiveClassification(r) === "CapEx").length;
  const totalOpexRecords = reportingRecords.filter((r) => effectiveClassification(r) === "OpEx").length;
  const pendingReview = reportingRecords.filter((r) => effectiveClassification(r) === "Review").length;
  const capexSpend = Math.round(
    reportingRecords.filter((r) => effectiveClassification(r) === "CapEx")
      .reduce((s, r) => s + Number(r.hours_allocated || 0), 0) * 125
  );
  const overrideRate = reportingRecords.length ? Math.round((feedbackEvents.length / reportingRecords.length) * 100) : 0;
  const avgConf = reportingRecords.length
    ? Math.round(reportingRecords.reduce((s, r) => s + Number(r._confidence || 0), 0) / reportingRecords.length)
    : 0;

  // CapEx spend by project (horizontal bar chart)
  const projectSpendRows = projectGroups
    .map((p) => ({
      projectCode: p.projectCode,
      projectName: p.projectName,
      capexHours: p.capexHours,
      capexSpendEst: Math.round(p.capexHours * 125),
      capexPct: p.totalHours ? (p.capexHours / p.totalHours) * 100 : 0,
    }))
    .filter((p) => p.capexHours > 0)
    .sort((a, b) => b.capexSpendEst - a.capexSpendEst)
    .slice(0, 8);
  const maxProjectSpend = Math.max(...projectSpendRows.map((p) => p.capexSpendEst), 1);

  // Weekly CapEx vs OpEx hours (stacked bar chart)
  const weeklyHoursBars = (() => {
    const byWeek = new Map<string, { capex: number; opex: number; review: number }>();
    for (const record of reportingRecords) {
      const week = record.week_start_date || "";
      if (!week) continue;
      const e = byWeek.get(week) ?? { capex: 0, opex: 0, review: 0 };
      const h = Number(record.hours_allocated || 0);
      const cls = effectiveClassification(record);
      if (cls === "CapEx") e.capex += h;
      else if (cls === "OpEx") e.opex += h;
      else e.review += h;
      byWeek.set(week, e);
    }
    return Array.from(byWeek.entries())
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([week, d]) => ({
        week,
        label: new Date(week + "T12:00:00").toLocaleDateString("en-US", { month: "short", day: "numeric" }),
        capex: Math.round(d.capex),
        opex: Math.round(d.opex),
        review: Math.round(d.review),
        total: Math.round(d.capex + d.opex + d.review),
      }));
  })();
  const maxWeeklyHours = Math.max(...weeklyHoursBars.map((w) => w.total), 1);

  return (
    <section className="page-stack analytics-page">
      <div className="page-header">
        <div>
          <h2>Analytics</h2>
          <p>Project, employee, activity, chronology, review-risk, and feedback intelligence for weekly capital labor outcomes.</p>
        </div>
        <div className="source-header-icon">
          <TrendingUp size={22} />
        </div>
      </div>

      <section className="metric-grid analytics-metrics">
        <Metric label="CapEx records" value={number(totalCapexRecords)} icon={CheckCircle2} tone="capex" />
        <Metric label="OpEx records" value={number(totalOpexRecords)} icon={ShieldCheck} tone="opex" />
        <Metric label="Pending review" value={number(pendingReview)} icon={AlertTriangle} tone={pendingReview ? "review" : undefined} />
        <Metric label="Avg confidence" value={avgConf ? `${avgConf}%` : "N/A"} icon={Gauge} />
        <Metric label="CapEx spend (est.)" value={capexSpend ? `$${capexSpend.toLocaleString()}` : "$0"} icon={TrendingUp} tone="capex" />
        <Metric label="Override rate" value={`${overrideRate}%`} icon={RefreshCw} tone={overrideRate > 10 ? "review" : undefined} />
      </section>

      <section className="analytics-hero">
        <article className="panel">
          <div className="section-title">
            <h4>CapEx Spend by Project</h4>
            <span>estimated capital spend per project at $125 / hr</span>
          </div>
          {projectSpendRows.length ? (
            <div className="project-spend-list">
              {projectSpendRows.map((p) => (
                <div className="project-spend-row" key={p.projectCode}>
                  <div className="project-spend-label">
                    <strong>{p.projectCode}</strong>
                    <span>{p.projectName}</span>
                  </div>
                  <div className="project-spend-track">
                    <div className="project-spend-bar" style={{ width: `${(p.capexSpendEst / maxProjectSpend) * 100}%` }} />
                  </div>
                  <div className="project-spend-value">
                    <strong>${p.capexSpendEst.toLocaleString()}</strong>
                    <span>{pct(p.capexPct)}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <section className="approval-empty compact-empty">
              <BarChart3 size={22} />
              <strong>No CapEx project data</strong>
              <p>Records classified as CapEx will populate this breakdown.</p>
            </section>
          )}
        </article>

        <article className="panel">
          <div className="section-title">
            <h4>Weekly CapEx vs OpEx</h4>
            <span>hours by classification per week</span>
          </div>
          {weeklyHoursBars.length ? (
            <>
              <div className="weekly-hours-chart">
                {weeklyHoursBars.map((w) => (
                  <div
                    className="weekly-hours-col"
                    key={w.week}
                    data-tooltip={`${w.label} · CapEx: ${w.capex}h · OpEx: ${w.opex}h${w.review > 0 ? ` · Review: ${w.review}h` : ""} · ${w.total ? pct((w.capex / w.total) * 100) : "0%"} CapEx`}
                  >
                    <div className="weekly-hours-bars" style={{ height: `${Math.max((w.total / maxWeeklyHours) * 100, 4)}%` }}>
                      {w.review > 0 && <span className="review" style={{ flex: w.review }} />}
                      {w.opex > 0 && <span className="opex" style={{ flex: w.opex }} />}
                      {w.capex > 0 && <span className="capex" style={{ flex: w.capex }} />}
                    </div>
                    <span className="weekly-hours-label">{w.label}</span>
                  </div>
                ))}
              </div>
              <div className="weekly-hours-legend">
                <span className="capex">■ CapEx</span>
                <span className="opex">■ OpEx</span>
                {weeklyHoursBars.some((w) => w.review > 0) && <span className="review">■ Review</span>}
              </div>
            </>
          ) : (
            <section className="approval-empty compact-empty">
              <BarChart3 size={22} />
              <strong>No weekly data</strong>
              <p>Records with week dates will populate this chart.</p>
            </section>
          )}
        </article>
      </section>

      <section className="panel project-priority-panel">
          <div className="section-title">
            <h4>Project Review Priority</h4>
            <span>ranked by review hours, confidence gap, and project size</span>
          </div>
          <div className="project-priority-list">
            {priorityProjects.map((project, index) => {
              const priority = project.reviewHours > 0 || project.avgConfidence < appConfig.reviewThreshold
                ? "Review"
                : project.capexShare >= 50
                  ? "CapEx Watch"
                  : "Monitor";
              return (
                <div className="project-priority-row" key={project.projectCode}>
                  <span className="priority-rank">{index + 1}</span>
                  <div className="priority-main">
                    <strong>{project.projectCode}</strong>
                    <em>{project.projectName}</em>
                    <div className="priority-track">
                      <span className="capex" style={{ width: `${project.capexShare}%` }} />
                      <span className="review" style={{ width: `${project.reviewShare}%` }} />
                    </div>
                  </div>
                  <div className="priority-stats">
                    <span>{number(project.totalHours)}h</span>
                    <span>{pct(project.capexShare)} CapEx</span>
                    <span>{number(project.avgConfidence)} conf.</span>
                    <span>{number(project.reviewHours)}h review</span>
                  </div>
                  <b className={priority === "Review" ? "review" : priority === "CapEx Watch" ? "capex" : "monitor"}>
                    {priority}
                  </b>
                </div>
              );
            })}
            {!priorityProjects.length && (
              <p className="audit-muted">No project records available for prioritization.</p>
            )}
          </div>
      </section>

      <section className="panel flow-panel">
        <div className="section-title">
          <h4>Activity-To-Class Flow</h4>
          <span>how work categories resolve into CapEx, OpEx, or Review</span>
        </div>
        <div className="activity-flow-list">
          {activityRows.map((activity) => (
            <div className="activity-flow-row" key={activity.activity}>
              <div className="activity-flow-source">
                <strong>{activity.activity}</strong>
                <span>{number(activity.total)}h</span>
              </div>
              <div className="activity-flow-track">
                <span className="capex" style={{ width: `${Math.max(2, (activity.capex / maxActivityHours) * 100)}%` }}>{activity.capex ? number(activity.capex) : ""}</span>
                <span className="opex" style={{ width: `${Math.max(2, (activity.opex / maxActivityHours) * 100)}%` }}>{activity.opex ? number(activity.opex) : ""}</span>
                <span className="review" style={{ width: `${Math.max(2, (activity.review / maxActivityHours) * 100)}%` }}>{activity.review ? number(activity.review) : ""}</span>
              </div>
              <div className="activity-flow-targets">
                <span className="capex">CapEx</span>
                <span className="opex">OpEx</span>
                <span className="review">Review</span>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="panel">
        <div className="section-title">
          <h4>Employee Contribution Matrix</h4>
          <span>top employees across top project codes; darker cells mean more hours</span>
        </div>
        <div className="employee-matrix">
          <div className="matrix-header" />
          {matrixProjects.map((project) => <div className="matrix-col-head" key={project.projectCode}>{project.projectCode}</div>)}
          {employeeRows.map((employee) => (
            <Fragment key={employee.employeeId}>
              <div className="matrix-employee">
                <strong>{employee.employeeName}</strong>
                <span>{employee.employeeId}</span>
              </div>
              {matrixProjects.map((project) => {
                const projectRecords = employee.records.filter((record) => (record.project_code || "Unmapped Project") === project.projectCode);
                const hours = projectRecords.reduce((sum, record) => sum + Number(record.hours_allocated || 0), 0);
                const capexHours = projectRecords
                  .filter((record) => effectiveClassification(record) === "CapEx")
                  .reduce((sum, record) => sum + Number(record.hours_allocated || 0), 0);
                const capexShare = hours ? (capexHours / hours) * 100 : 0;
                return (
                  <div
                    className={`matrix-cell ${hours ? "active" : ""}`}
                    key={`${employee.employeeId}-${project.projectCode}`}
                    style={{ opacity: hours ? Math.max(0.35, hours / maxCellHours) : 0.22 }}
                  >
                    <strong>{hours ? `${number(hours)}h` : "-"}</strong>
                    {hours > 0 && <span>{pct(capexShare)}</span>}
                  </div>
                );
              })}
            </Fragment>
          ))}
        </div>
      </section>
    </section>
  );
}

function ActivityRecordsView({
  records,
  filter,
  onFilter,
  sourceFilter,
  onSourceFilter,
  expandedRecordUid,
  onToggleRecord,
  onAudit,
  onOverride
}: {
  records: RecordItem[];
  filter: RecordFilter;
  onFilter: (filter: RecordFilter) => void;
  sourceFilter: SourceFilter;
  onSourceFilter: (filter: SourceFilter) => void;
  expandedRecordUid: string;
  onToggleRecord: (recordUid: string) => void;
  onAudit: (record: RecordItem) => void;
  onOverride: (recordUid: string, classification: Classification | null) => void;
}) {
  const filters: RecordFilter[] = ["All", "CapEx", "OpEx", "Review"];
  const sourceFilters: SourceFilter[] = ["All", "Excel", "DOCX form"];
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [projectFilter, setProjectFilter] = useState("All");
  const [startDateFilter, setStartDateFilter] = useState("");
  const [endDateFilter, setEndDateFilter] = useState("");
  const projectOptions = useMemo(
    () => Array.from(new Set(records.map((record) => record.project_code).filter(Boolean))).sort(),
    [records]
  );
  const filteredRecords = useMemo(
    () =>
      records.filter((record) => {
        const matchesSource = sourceFilter === "All" || (record._source ?? "") === sourceFilter;
        const matchesProject = projectFilter === "All" || record.project_code === projectFilter;
        const recordDate = record.week_start_date || "";
        const matchesStart = !startDateFilter || recordDate >= startDateFilter;
        const matchesEnd = !endDateFilter || recordDate <= endDateFilter;
        return matchesSource && matchesProject && matchesStart && matchesEnd;
      }),
    [records, sourceFilter, projectFilter, startDateFilter, endDateFilter]
  );
  const pageCount = Math.max(Math.ceil(filteredRecords.length / pageSize), 1);
  const currentPage = Math.min(page, pageCount);
  const pageStart = filteredRecords.length ? (currentPage - 1) * pageSize : 0;
  const pageEnd = Math.min(pageStart + pageSize, filteredRecords.length);
  const visibleRecords = filteredRecords.slice(pageStart, pageEnd);

  useEffect(() => {
    setPage(1);
  }, [filter, sourceFilter, projectFilter, startDateFilter, endDateFilter, pageSize]);

  useEffect(() => {
    setPage((current) => Math.min(current, pageCount));
  }, [pageCount]);

  return (
    <section className="page-stack">
      <div className="page-header">
        <div>
          <h2>Activity Records</h2>
          <p>Click any row to expand all Timesheets fields. Normalized classification queue with evidence, confidence, and correction controls.</p>
        </div>
      </div>

      <div className="records-shell">
        <div className="records-toolbar">
          <div className="record-filters" role="tablist" aria-label="Activity record filters">
            {filters.map((item) => (
              <button
                key={item}
                className={filter === item ? "active" : ""}
                onClick={() => onFilter(item)}
              >
                {item}
              </button>
            ))}
          </div>
          <div className="record-field-filters">
            <label>
              Source
              <select value={sourceFilter} onChange={(event) => onSourceFilter(event.target.value as SourceFilter)}>
                {sourceFilters.map((source) => (
                  <option key={source} value={source}>
                    {source === "All" ? "All sources" : source}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Project code
              <select value={projectFilter} onChange={(event) => setProjectFilter(event.target.value)}>
                <option value="All">All projects</option>
                {projectOptions.map((projectCode) => (
                  <option key={projectCode} value={projectCode}>{projectCode}</option>
                ))}
              </select>
            </label>
            <label>
              From
              <input
                type="date"
                value={startDateFilter}
                onChange={(event) => setStartDateFilter(event.target.value)}
              />
            </label>
            <label>
              To
              <input
                type="date"
                value={endDateFilter}
                onChange={(event) => setEndDateFilter(event.target.value)}
              />
            </label>
            {(sourceFilter !== "All" || projectFilter !== "All" || startDateFilter || endDateFilter) && (
              <button
                className="clear-filters"
                onClick={() => {
                  onSourceFilter("All");
                  setProjectFilter("All");
                  setStartDateFilter("");
                  setEndDateFilter("");
                }}
              >
                Clear
              </button>
            )}
          </div>
        </div>

        <div className="records-table-wrap">
          <table className="records-table">
            <thead>
              <tr>
                <th aria-label="Expand" />
                <th>Record</th>
                <th>Employee</th>
                <th>Week</th>
                <th>Project</th>
                <th>Activity</th>
                <th>Hours</th>
                <th>Class</th>
                <th>Quality</th>
                <th>Confidence</th>
                <th>Override</th>
                <th>Evidence</th>
              </tr>
            </thead>
            <tbody>
              {visibleRecords.map((record) => {
                const classification = effectiveClassification(record);
                const expanded = expandedRecordUid === record._recordUid;
                const quality = recordQuality(record);
                return (
                  <Fragment key={record._recordUid}>
                    <tr
                      className={expanded ? "expanded-parent" : ""}
                      onClick={() => onToggleRecord(record._recordUid)}
                    >
                      <td className="expand-cell">
                        <button
                          aria-label={expanded ? "Collapse record" : "Expand record"}
                          onClick={(event) => {
                            event.stopPropagation();
                            onToggleRecord(record._recordUid);
                          }}
                        >
                          {expanded ? "v" : ">"}
                        </button>
                      </td>
                      <td>
                        <strong className="record-id">{record.project_code || "Unmapped"}</strong>
                        <span>{record._source ?? "Excel"} · {record.project_name || "No project name"}</span>
                      </td>
                      <td>
                        <strong>{record.employee_id}</strong>
                        <span>{record.full_name}</span>
                      </td>
                      <td>
                        <strong>{record.week_start_date}</strong>
                        <span>to {record.week_end_date}</span>
                      </td>
                      <td>{record.project_code}</td>
                      <td>{record.activity_type}</td>
                      <td>{number(Number(record.hours_allocated || 0))}</td>
                      <td>
                        <span className={`badge ${classNameFor(classification)}`}>{classification}</span>
                      </td>
                      <td>
                        <span className={`badge quality-${quality.toLowerCase()}`}>{quality}</span>
                      </td>
                      <td>
                        <span className={`confidence-pill ${record._confidence < 70 ? "low" : ""}`}>
                          {number(record._confidence)}
                        </span>
                      </td>
                      <td onClick={(event) => event.stopPropagation()}>
                        <select
                          className="override-select"
                          value={record._override ?? "None"}
                          onChange={(event) => {
                            const value = event.target.value as "None" | Classification;
                            onOverride(record._recordUid, value === "None" ? null : value);
                          }}
                        >
                          <option value="None">None</option>
                          <option value="CapEx">CapEx</option>
                          <option value="OpEx">OpEx</option>
                          <option value="Review">Review</option>
                        </select>
                      </td>
                      <td className="evidence-cell">{record._evidence}</td>
                    </tr>
                    {expanded && (
                      <tr className="expanded-row" key={`${record._recordUid}-detail`}>
                        <td colSpan={12}>
                          <ExpandedTimesheetRecord record={record} onAudit={onAudit} />
                        </td>
                      </tr>
                    )}
                  </Fragment>
                );
              })}
            </tbody>
          </table>
        </div>

        <div className="pagination-bar">
          <span>
            Showing {filteredRecords.length ? pageStart + 1 : 0}-{pageEnd} of {filteredRecords.length}
          </span>
          <div className="pagination-controls">
            <label>
              Rows
              <select
                value={pageSize}
                onChange={(event) => setPageSize(Number(event.target.value))}
              >
                <option value={10}>10</option>
                <option value={25}>25</option>
                <option value={50}>50</option>
                <option value={100}>100</option>
              </select>
            </label>
            <button disabled={currentPage <= 1} onClick={() => setPage(1)}>First</button>
            <button disabled={currentPage <= 1} onClick={() => setPage((value) => Math.max(value - 1, 1))}>
              Previous
            </button>
            <strong>Page {currentPage} of {pageCount}</strong>
            <button disabled={currentPage >= pageCount} onClick={() => setPage((value) => Math.min(value + 1, pageCount))}>
              Next
            </button>
            <button disabled={currentPage >= pageCount} onClick={() => setPage(pageCount)}>Last</button>
          </div>
        </div>
      </div>
    </section>
  );
}

function ExpandedTimesheetRecord({
  record,
  onAudit
}: {
  record: RecordItem;
  onAudit: (record: RecordItem) => void;
}) {
  const identity: Array<[string, unknown]> = [
    ["Employee ID", record.employee_id],
    ["Full Name", record.full_name],
    ["Job Title", record.job_title],
    ["Job Family", record.job_family],
    ["Team", record.team_name],
    ["Org Unit", record.org_unit],
    ["Manager ID", record.manager_id]
  ];
  const week: Array<[string, unknown]> = [
    ["Week Start Date", record.week_start_date],
    ["Week End Date", record.week_end_date],
    ["Standard Days", record.standard_days],
    ["Holiday Days", record.holiday_days],
    ["PTO Days", record.pto_days],
    ["Sick Days", record.sick_days],
    ["Actual Working Days", record.actual_working_days]
  ];
  const activitySignals: Array<[string, unknown]> = [
    ["Meeting Count", record.meeting_count],
    ["Ticket Count", record.ticket_count],
    ["Email Volume", record.email_volume],
    ["Code Commit Count", record.code_commit_count],
    ["System Activity Score", record.system_activity_score]
  ];
  const allocation: Array<[string, unknown]> = [
    ["Project Code", record.project_code],
    ["Project Name", record.project_name],
    ["Activity Type", record.activity_type],
    ["Hours Allocated", record.hours_allocated],
    ["Source System", record._source ?? "Excel"],
    ["Source File", record._sourceFileName ?? "Workbook"]
  ];
  const outcome: Array<[string, unknown]> = [
    ["Classification", effectiveClassification(record)],
    ["Model Classification", record._classification],
    ["Manual Override", record._override ?? "None"],
    ["Confidence", record._confidence],
    ["Quality", recordQuality(record)],
    ["Rule Version", record._ruleVersion ?? "Current"]
  ];

  return (
    <div className="expanded-record">
      <div className="expanded-accent" />
      <div className="expanded-section-grid">
        <FieldSection title="Employee Identity" rows={identity} />
        <FieldSection title="Week & Availability" rows={week} />
        <FieldSection title="Activity Signals" rows={activitySignals} />
        <FieldSection title="Project Allocation" rows={allocation} />
        <FieldSection title="Classification Outcome" rows={outcome} />
      </div>

      <div className="expanded-notes-grid">
        <div className="detail-notes">
          <strong>Evidence</strong>
          <p>{record._evidence || "No evidence generated."}</p>
        </div>
        <div className="detail-notes">
          <strong>Submission Notes</strong>
          <p>{record.submission_notes || "No submission notes supplied."}</p>
        </div>
        <div className="detail-notes">
          <strong>Review Reason</strong>
          <p>{record._reviewReason || "No review reason."}</p>
        </div>
      </div>

      {(record._signals ?? []).length > 0 && (
        <div className="signal-list expanded-signals">
          {(record._signals ?? []).map((signal) => (
            <span className={`signal ${signal.kind}`} key={signal.label}>{signal.label}</span>
          ))}
        </div>
      )}

      <div className="expanded-actions">
        <button onClick={() => onAudit(record)}>Open Audit Trail</button>
      </div>
    </div>
  );
}

function formatAuditTime(value?: string | null): string {
  if (!value) return "Unknown time";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit"
  });
}

function downloadBlob(content: string, filename: string, mime: string) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

function exportAuditCsv(records: RecordItem[]) {
  const cols = [
    "RecordKey",
    "Source",
    "SourceFile",
    "EmployeeID",
    "EmployeeName",
    "WeekStart",
    "WeekEnd",
    "ProjectCode",
    "ProjectName",
    "ActivityType",
    "HoursAllocated",
    "Classification",
    "Override",
    "FinalClassification",
    "Confidence",
    "RuleVersion",
    "Evidence",
    "ReviewReason",
    "Signals",
    "MatchedExcel",
    "RecordUID"
  ];
  const escape = (value: unknown) => `"${String(value ?? "").replace(/"/g, '""')}"`;
  const rows = records.map((record) => [
    record._key ?? record._recordUid,
    record._source ?? "Excel",
    record._sourceFileName ?? "",
    record.employee_id,
    record.full_name,
    record.week_start_date,
    record.week_end_date,
    record.project_code,
    record.project_name,
    record.activity_type,
    record.hours_allocated,
    record._classification,
    record._override ?? "",
    effectiveClassification(record),
    record._confidence,
    record._ruleVersion ?? "",
    record._evidence,
    record._reviewReason,
    (record._signals ?? []).map((signal) => `${signal.kind}:${signal.label}:${signal.impact}`).join(" | "),
    Number(record._matchedExcel || 0) ? "Yes" : "No",
    record._recordUid
  ].map(escape).join(","));
  const stamp = new Date().toISOString().slice(0, 16).replace("T", "_").replace(":", "");
  downloadBlob([cols.join(","), ...rows].join("\n"), `timesheets_audit_${stamp}.csv`, "text/csv");
}

function exportAuditJson(records: RecordItem[]) {
  const payload = records.map((record) => ({
    recordKey: record._key ?? record._recordUid,
    source: record._source ?? "Excel",
    sourceFile: record._sourceFileName ?? null,
    employeeId: record.employee_id,
    employeeName: record.full_name,
    weekStart: record.week_start_date,
    weekEnd: record.week_end_date,
    projectCode: record.project_code,
    projectName: record.project_name,
    activityType: record.activity_type,
    hoursAllocated: record.hours_allocated,
    classification: record._classification,
    override: record._override ?? null,
    finalClassification: effectiveClassification(record),
    confidence: record._confidence,
    ruleVersion: record._ruleVersion ?? null,
    evidence: record._evidence,
    reviewReason: record._reviewReason,
    signals: record._signals ?? [],
    matchedExcel: !!Number(record._matchedExcel || 0),
    recordUid: record._recordUid,
    agentTrace: record._agentTrace ?? null
  }));
  const stamp = new Date().toISOString().slice(0, 16).replace("T", "_").replace(":", "");
  downloadBlob(JSON.stringify(payload, null, 2), `timesheets_audit_${stamp}.json`, "application/json");
}

function timesheetPrecedents(record: RecordItem): Array<{
  id: string;
  title: string;
  label: Classification;
  similarity: number;
  note: string;
}> {
  const classification = effectiveClassification(record);
  const similarity = Math.min(97, Math.max(72, Math.round(Number(record._confidence || 0) + 4)));
  return [
    {
      id: "activity-precedent",
      title: `Reviewed activity: ${record.activity_type || "Unspecified activity"}`,
      label: classification,
      similarity,
      note: `${record.job_family || "Employee"} work on ${record.project_code || "the project"} used similar activity, hours, and evidence signals.`
    },
    {
      id: "project-precedent",
      title: `Project allocation pattern: ${record.project_code || "Unmapped project"}`,
      label: classification,
      similarity: Math.max(68, similarity - 8),
      note: `Comparable weekly entries were evaluated against project, employee role, work-day availability, and notes.`
    }
  ];
}

function auditEventSummary(event: AuditEvent): string {
  if (event.event_type === "classified") {
    const classification = event.payload.classification ? String(event.payload.classification) : "classification";
    const confidence = event.payload.confidence ? ` at ${event.payload.confidence}% confidence` : "";
    return `Pipeline produced ${classification}${confidence}.`;
  }
  if (event.event_type === "override") {
    const classification = event.payload.classification ? String(event.payload.classification) : "cleared";
    return `Human override ${classification === "cleared" ? "was cleared" : `set final output to ${classification}`}.`;
  }
  if (event.event_type === "quarantined") return "Row quality checks routed this record to review before classification.";
  return "Audit event captured for this record.";
}

function auditEventTone(eventType: string): string {
  if (eventType === "classified") return "classified";
  if (eventType === "override") return "override";
  if (eventType === "quarantined") return "quarantined";
  return "generic";
}

function auditPayloadChips(event: AuditEvent): Array<[string, string]> {
  return Object.entries(event.payload ?? {}).map(([key, value]) => {
    if (key === "agent_trace" && value && typeof value === "object") {
      const trace = value as { provider?: string; model?: string; steps?: unknown[] };
      const provider = trace.provider ? `${trace.provider}` : "trace";
      const model = trace.model ? ` · ${trace.model}` : "";
      const steps = Array.isArray(trace.steps) ? ` · ${trace.steps.length} steps` : "";
      return [key, `${provider}${model}${steps}`];
    }
    if (key === "signals" && Array.isArray(value)) return [key, `${value.length} signals`];
    if (key === "row_quality" && value && typeof value === "object") {
      const quality = value as { status?: string; issues?: unknown[] };
      const issueCount = Array.isArray(quality.issues) ? ` · ${quality.issues.length} issues` : "";
      return [key, `${quality.status ?? "quality"}${issueCount}`];
    }
    if (Array.isArray(value)) return [key, JSON.stringify(value)];
    if (value && typeof value === "object") return [key, JSON.stringify(value)];
    return [key, String(value ?? "—")];
  });
}

function AuditTrailDetail({ record, events }: { record: RecordItem; events: AuditEvent[] }) {
  const classification = effectiveClassification(record);
  const trace = record._agentTrace;
  const precedents = timesheetPrecedents(record);

  return (
    <div className="audit-detail-shell">
      <div className="audit-detail-grid">
        <article className="audit-card">
          <div className="section-title">
            <h4>Classification Trace</h4>
            <span>immutable record manifest</span>
          </div>
          <div className="audit-manifest-grid">
            <div className="audit-manifest"><span>Record key</span><strong>{record._key ?? record._recordUid}</strong></div>
            <div className="audit-manifest"><span>Source</span><strong>{record._source ?? "Excel"}</strong></div>
            <div className="audit-manifest"><span>Source file</span><strong>{record._sourceFileName ?? "Workbook"}</strong></div>
            <div className="audit-manifest"><span>Rule version</span><strong>{record._ruleVersion ?? "Current"}</strong></div>
            <div className="audit-manifest"><span>Initial output</span><strong>{record._classification}</strong></div>
            <div className="audit-manifest"><span>Final output</span><strong>{classification}</strong></div>
            <div className="audit-manifest"><span>Confidence</span><strong>{number(Number(record._confidence || 0))}%</strong></div>
            <div className="audit-manifest"><span>Matched Excel</span><strong>{Number(record._matchedExcel || 0) ? "Yes" : "No"}</strong></div>
          </div>
          <div className="audit-note-box">
            <strong>Evidence</strong>
            <p>{record._evidence || "No evidence generated."}</p>
          </div>
        </article>

        <article className="audit-card">
          <div className="section-title">
            <h4>Timesheet Context</h4>
            <span>employee, week, project</span>
          </div>
          <div className="audit-manifest-grid compact">
            <div className="audit-manifest"><span>Employee</span><strong>{record.full_name || record.employee_id}</strong></div>
            <div className="audit-manifest"><span>Employee ID</span><strong>{record.employee_id}</strong></div>
            <div className="audit-manifest"><span>Team</span><strong>{record.team_name || "—"}</strong></div>
            <div className="audit-manifest"><span>Week</span><strong>{record.week_start_date} to {record.week_end_date}</strong></div>
            <div className="audit-manifest"><span>Project</span><strong>{record.project_code || "Unmapped"}</strong></div>
            <div className="audit-manifest"><span>Hours</span><strong>{number(Number(record.hours_allocated || 0))}</strong></div>
          </div>
          <div className="audit-note-box">
            <strong>Submission notes</strong>
            <p>{record.submission_notes || "No notes supplied."}</p>
          </div>
        </article>

        <article className="audit-card">
          <div className="section-title">
            <h4>Signal Ledger</h4>
            <span>direction and impact</span>
          </div>
          <div className="audit-signal-ledger">
            {(record._signals ?? []).length ? (record._signals ?? []).map((signal) => (
              <div className="audit-signal-row" key={`${signal.kind}-${signal.label}`}>
                <div>
                  <strong>{signal.label}</strong>
                  <span>{signal.kind}</span>
                </div>
                <b>{signal.impact > 0 ? "+" : ""}{signal.impact}</b>
              </div>
            )) : (
              <p className="audit-muted">No detailed signal ledger was attached to this record.</p>
            )}
          </div>
        </article>

        <article className="audit-card">
          <div className="section-title">
            <h4>Semantic Precedents</h4>
            <span>similar reviewed outcomes</span>
          </div>
          <div className="audit-precedent-list">
            {precedents.map((precedent) => (
              <div className="audit-precedent" key={precedent.id}>
                <div>
                  <strong>{precedent.title}</strong>
                  <span>{precedent.note}</span>
                </div>
                <em className={`badge ${classNameFor(precedent.label)}`}>{precedent.label} · {precedent.similarity}%</em>
              </div>
            ))}
          </div>
        </article>
      </div>

      {trace ? (
        <AgentFlow trace={trace} />
      ) : (
        <article className="audit-card">
          <div className="section-title">
            <h4>LangGraph Agent Flow</h4>
            <span>not available</span>
          </div>
          <p className="audit-muted">No agent trace is attached to this record. Re-ingest with the backend pipeline enabled to capture the full classification route.</p>
        </article>
      )}

      <article className="audit-card">
        <div className="section-title">
          <h4>Event Timeline</h4>
          <span>{events.length} persisted audit events</span>
        </div>
        <div className="audit-event-timeline">
          {events.length ? events.map((event, index) => (
            <div
              className={`audit-event-step ${auditEventTone(event.event_type)}`}
              key={event.id ?? `${event.event_type}-${index}`}
            >
              <div className="audit-event-marker" />
              <div className="audit-event-body">
                <div className="audit-event-head">
                  <strong>{event.event_type}</strong>
                  <em>{formatAuditTime(event.created_at)}</em>
                  {event.run_id && <span>run {event.run_id.slice(0, 8)}</span>}
                </div>
                <p>{auditEventSummary(event)}</p>
                <div className="audit-event-chip-list">
                  {auditPayloadChips(event).map(([key, value]) => (
                    <span className={value.length > 90 ? "wide" : ""} key={key}>
                      <b>{key}:</b> {value}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )) : (
            <p className="audit-muted">No persisted audit events were found for this record yet.</p>
          )}
        </div>
      </article>
    </div>
  );
}

function AuditView({
  records,
  selectedRecord,
  auditEvents,
  onSelectRecord
}: {
  records: RecordItem[];
  selectedRecord: RecordItem | null;
  auditEvents: AuditEvent[];
  onSelectRecord: (record: RecordItem) => void;
}) {
  const [expandedId, setExpandedId] = useState(selectedRecord?._recordUid ?? "");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const expandedRowRef = useRef<HTMLTableRowElement | null>(null);
  const pageCount = Math.max(Math.ceil(records.length / pageSize), 1);
  const currentPage = Math.min(page, pageCount);
  const pageStart = records.length ? (currentPage - 1) * pageSize : 0;
  const pageEnd = Math.min(pageStart + pageSize, records.length);
  const visibleRecords = records.slice(pageStart, pageEnd);

  useEffect(() => {
    if (!selectedRecord?._recordUid) return;
    setExpandedId(selectedRecord._recordUid);
    const selectedIndex = records.findIndex((record) => record._recordUid === selectedRecord._recordUid);
    if (selectedIndex >= 0) setPage(Math.floor(selectedIndex / pageSize) + 1);
  }, [selectedRecord?._recordUid, records, pageSize]);

  useEffect(() => {
    setPage((value) => Math.min(value, pageCount));
  }, [pageCount]);

  useEffect(() => {
    if (!expandedId || !expandedRowRef.current) return;
    const timer = window.setTimeout(() => {
      expandedRowRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
    }, 80);
    return () => window.clearTimeout(timer);
  }, [expandedId, currentPage, pageSize]);

  function toggleRecord(record: RecordItem) {
    const nextId = expandedId === record._recordUid ? "" : record._recordUid;
    setExpandedId(nextId);
    if (nextId) onSelectRecord(record);
  }

  return (
    <section className="page-stack">
      <div className="page-header">
        <div>
          <h2>Audit Trail</h2>
          <p>Click any record to expand classification trace, signal ledger, semantic precedents, agent route, and persisted audit events.</p>
        </div>
      </div>

      <div className="records-shell audit-shell">
        <div className="audit-toolbar">
          <span>{records.length} records under audit</span>
          <div>
            <button type="button" onClick={() => exportAuditCsv(records)}>Export CSV</button>
            <button type="button" onClick={() => exportAuditJson(records)}>Export JSON</button>
          </div>
        </div>

        {records.length ? (
          <>
            <div className="records-table-wrap">
              <table className="records-table audit-records-table">
                <thead>
                  <tr>
                    <th aria-label="Expand" />
                    <th>Record</th>
                    <th>Employee</th>
                    <th>Week</th>
                    <th>Project</th>
                    <th>Activity</th>
                    <th>Hours</th>
                    <th>Class</th>
                    <th>Confidence</th>
                    <th>Evidence</th>
                  </tr>
                </thead>
                <tbody>
                  {visibleRecords.map((record) => {
                    const expanded = expandedId === record._recordUid;
                    const events = selectedRecord?._recordUid === record._recordUid ? auditEvents : [];
                    return (
                      <Fragment key={record._recordUid}>
                        <tr
                          ref={expanded ? expandedRowRef : undefined}
                          className={expanded ? "expanded-parent" : ""}
                          onClick={() => toggleRecord(record)}
                        >
                          <td className="expand-cell">
                            <button
                              aria-label={expanded ? "Collapse audit record" : "Expand audit record"}
                              onClick={(event) => {
                                event.stopPropagation();
                                toggleRecord(record);
                              }}
                            >
                              {expanded ? "v" : ">"}
                            </button>
                          </td>
                          <td>
                            <strong className="record-id">{record._key ?? record.project_code ?? record._recordUid}</strong>
                            <span>{record._source ?? "Excel"} · {record._sourceFileName ?? "Workbook"}</span>
                          </td>
                          <td>
                            <strong>{record.employee_id}</strong>
                            <span>{record.full_name}</span>
                          </td>
                          <td>
                            <strong>{record.week_start_date}</strong>
                            <span>to {record.week_end_date}</span>
                          </td>
                          <td>{record.project_code || "—"}</td>
                          <td>{record.activity_type || "—"}</td>
                          <td>{number(Number(record.hours_allocated || 0))}</td>
                          <td><span className={`badge ${classNameFor(effectiveClassification(record))}`}>{effectiveClassification(record)}</span></td>
                          <td>
                            <span className={`confidence-pill ${record._confidence < 70 ? "low" : ""}`}>
                              {number(Number(record._confidence || 0))}
                            </span>
                          </td>
                          <td className="evidence-cell">{record._evidence}</td>
                        </tr>
                        {expanded && (
                          <tr className="expanded-row">
                            <td colSpan={10}>
                              <AuditTrailDetail record={record} events={events} />
                            </td>
                          </tr>
                        )}
                      </Fragment>
                    );
                  })}
                </tbody>
              </table>
            </div>

            <div className="pagination-bar">
              <span>
                Showing {records.length ? pageStart + 1 : 0}-{pageEnd} of {records.length}
              </span>
              <div className="pagination-controls">
                <label>
                  Rows
                  <select
                    value={pageSize}
                    onChange={(event) => {
                      setPageSize(Number(event.target.value));
                      setPage(1);
                    }}
                  >
                    <option value={10}>10</option>
                    <option value={25}>25</option>
                    <option value={50}>50</option>
                    <option value={100}>100</option>
                  </select>
                </label>
                <button disabled={currentPage <= 1} onClick={() => setPage(1)}>First</button>
                <button disabled={currentPage <= 1} onClick={() => setPage((value) => Math.max(value - 1, 1))}>
                  Previous
                </button>
                <strong>Page {currentPage} of {pageCount}</strong>
                <button disabled={currentPage >= pageCount} onClick={() => setPage((value) => Math.min(value + 1, pageCount))}>
                  Next
                </button>
                <button disabled={currentPage >= pageCount} onClick={() => setPage(pageCount)}>Last</button>
              </div>
            </div>
          </>
        ) : (
          <section className="approval-empty">
            <History size={24} />
            <strong>No audit records available</strong>
            <p>Upload Excel or form data to populate the auditable classification history.</p>
          </section>
        )}
      </div>
    </section>
  );
}

function LearningView({
  records,
  feedbackEvents,
  onAudit
}: {
  records: RecordItem[];
  feedbackEvents: RecordItem[];
  onAudit: (record: RecordItem) => void;
}) {
  const conflictRate = records.length ? Math.round((feedbackEvents.length / records.length) * 100) : 0;
  const capexOverrides = feedbackEvents.filter((record) => record._override === "CapEx").length;
  const opexOverrides = feedbackEvents.filter((record) => record._override === "OpEx").length;
  const reviewOverrides = feedbackEvents.filter((record) => record._override === "Review").length;
  const projectCorrections = Array.from(
    feedbackEvents.reduce((map, record) => {
      const key = record.project_code || "Unmapped";
      const current = map.get(key) ?? { projectCode: key, projectName: record.project_name || "No project name", count: 0 };
      current.count += 1;
      map.set(key, current);
      return map;
    }, new Map<string, { projectCode: string; projectName: string; count: number }>())
      .values()
  ).sort((left, right) => right.count - left.count).slice(0, 5);
  const avgConfidence = feedbackEvents.length
    ? feedbackEvents.reduce((sum, record) => sum + Number(record._confidence || 0), 0) / feedbackEvents.length
    : 0;

  return (
    <section className="page-stack">
      <div className="page-header">
        <div>
          <h2>Feedback Learning</h2>
          <p>Reviewer corrections are captured as labeled feedback. Conflict rate and override patterns are tracked for future calibration.</p>
        </div>
        <div className="source-header-icon">
          <RefreshCw size={22} />
        </div>
      </div>

      <section className="metric-grid learning-metrics">
        <Metric
          label="Conflict rate"
          value={`${conflictRate}%`}
          icon={AlertTriangle}
          tone={feedbackEvents.length ? "review" : undefined}
        />
        <Metric label="Total corrections" value={number(feedbackEvents.length)} icon={RefreshCw} tone="review" />
        <Metric label="CapEx corrections" value={number(capexOverrides)} icon={CheckCircle2} tone="capex" />
        <Metric label="OpEx corrections" value={number(opexOverrides)} icon={ShieldCheck} tone="opex" />
        <Metric label="Sent to review" value={number(reviewOverrides)} icon={AlertTriangle} tone="review" />
        <Metric label="Avg corrected confidence" value={feedbackEvents.length ? pct(avgConfidence) : "N/A"} icon={Gauge} />
      </section>

      <section className="learning-grid">
        <article className="panel">
          <div className="section-title">
            <h4>Correction Log</h4>
            <span>original output to reviewer decision</span>
          </div>
          {feedbackEvents.length ? (
            <div className="learning-correction-list">
              {feedbackEvents.map((record) => (
                <button
                  className="learning-correction-row"
                  key={record._recordUid}
                  onClick={() => onAudit(record)}
                >
                  <div>
                    <strong>{record.full_name || record.employee_id} · {record.project_code || "Unmapped"}</strong>
                    <span>
                      {record._classification} -&gt; {record._override}
                      {record._overrideNote ? ` · "${record._overrideNote}"` : ""}
                      {record._ruleVersion ? ` · ${record._ruleVersion}` : ""}
                    </span>
                  </div>
                  <em className={`badge ${classNameFor(record._override ?? "Review")}`}>{record._override}</em>
                  <b>{number(Number(record._confidence || 0))}</b>
                </button>
              ))}
            </div>
          ) : (
            <section className="approval-empty compact-empty">
              <RefreshCw size={22} />
              <strong>No corrections captured yet</strong>
              <p>Override records in Activity Records or Escalations to create feedback events for this log.</p>
            </section>
          )}
        </article>

        <article className="panel">
          <div className="section-title">
            <h4>Calibration Candidates</h4>
            <span>projects with the most reviewer changes</span>
          </div>
          {projectCorrections.length ? (
            <div className="learning-calib-list">
              {projectCorrections.map((project) => (
                <div className="learning-calib-card" key={project.projectCode}>
                  <div>
                    <strong>{project.projectCode}</strong>
                    <span>{project.projectName}</span>
                  </div>
                  <b>{project.count} {project.count === 1 ? "change" : "changes"}</b>
                </div>
              ))}
            </div>
          ) : (
            <section className="approval-empty compact-empty">
              <Target size={22} />
              <strong>No calibration candidates yet</strong>
              <p>Correction clusters will surface here as reviewers override classifications.</p>
            </section>
          )}
        </article>
      </section>
    </section>
  );
}

type ReviewLineEdit = {
  classification: Classification;
  project_code: string;
  submission_notes: string;
};

type WeekAttendanceEdit = {
  holiday_days: number;
  pto_days: number;
  sick_days: number;
};

function EmployeeReviewWorkspace({
  profiles,
  selectedEmployee,
  selectedEmployeeId,
  search,
  records,
  onSearch,
  onSelectEmployee,
  onAudit,
  onSaveLine,
  onSubmitDraft
}: {
  profiles: EmployeeProfile[];
  selectedEmployee?: EmployeeProfile;
  selectedEmployeeId: string;
  search: string;
  records: RecordItem[];
  onSearch: (value: string) => void;
  onSelectEmployee: (employeeId: string) => void;
  onAudit: (line: DraftLine) => void;
  onSaveLine: (recordUid: string, request: {
    classification?: Classification;
    project_code?: string;
    holiday_days?: number;
    pto_days?: number;
    sick_days?: number;
    submission_notes?: string;
    note?: string;
  }) => Promise<unknown>;
  onSubmitDraft: (recordUids: string[]) => Promise<void>;
}) {
  const [edits, setEdits] = useState<Record<string, ReviewLineEdit>>({});
  const [weekEdits, setWeekEdits] = useState<Record<string, WeekAttendanceEdit>>({});
  const [saving, setSaving] = useState(false);
  const sortedProfiles = useMemo(
    () =>
      profiles
        .map((profile) => ({
          profile,
          score: fuzzyScore(
            `${profile.employeeId} ${profile.employeeName} ${profile.jobTitle} ${profile.teamName} ${profile.managerId}`,
            search
          )
        }))
        .filter((item): item is { profile: EmployeeProfile; score: number } => item.score !== null)
        .sort((left, right) => {
          if (left.score !== right.score) return left.score - right.score;
          return left.profile.employeeId.localeCompare(right.profile.employeeId, undefined, { numeric: true });
        })
        .map((item) => item.profile),
    [profiles, search]
  );
  const selectedInSearch = sortedProfiles.find((profile) => profile.employeeId === selectedEmployeeId);
  const activeEmployee = selectedInSearch ?? sortedProfiles[0] ?? selectedEmployee ?? profiles[0];
  const activeWeeks = useMemo(() => activeEmployee?.weeks ?? [], [activeEmployee]);
  const activeLines = useMemo(() => activeWeeks.flatMap((week) => week.line_items), [activeWeeks]);
  const recordByUid = useMemo(() => new Map(records.map((record) => [record._recordUid, record])), [records]);
  const projectOptions = useMemo(
    () => Array.from(new Set(records.map((record) => record.project_code).filter(Boolean))).sort(),
    [records]
  );

  function recordsForWeek(week: Draft) {
    return week.line_items
      .map((line) => recordByUid.get(line.record_uid))
      .filter((record): record is RecordItem => Boolean(record));
  }

  function weekAttendanceFromData(week: Draft): WeekAttendanceEdit {
    const linkedRecords = recordsForWeek(week);
    const firstRecord = linkedRecords[0];
    return {
      holiday_days: Number(week.holiday_days ?? firstRecord?.holiday_days ?? 0),
      pto_days: Number(week.pto_days ?? firstRecord?.pto_days ?? 0),
      sick_days: Number(week.sick_days ?? firstRecord?.sick_days ?? 0)
    };
  }

  function workingDaysForWeek(week: Draft, edit?: WeekAttendanceEdit) {
    const linkedRecords = recordsForWeek(week);
    const firstRecord = linkedRecords[0];
    const attendance = edit ?? weekAttendanceFromData(week);
    const standardDays = Number(firstRecord?.standard_days ?? 0);
    if (standardDays) {
      return Math.max(0, standardDays - attendance.holiday_days - attendance.pto_days - attendance.sick_days);
    }
    return Number(week.actual_working_days ?? firstRecord?.actual_working_days ?? 0);
  }

  useEffect(() => {
    if (!activeEmployee) return;
    const next: Record<string, ReviewLineEdit> = {};
    const nextWeeks: Record<string, WeekAttendanceEdit> = {};
    for (const line of activeLines) {
      const record = recordByUid.get(line.record_uid);
      next[line.record_uid] = {
        classification: line.classification,
        project_code: record?.project_code ?? line.project_code ?? "",
        submission_notes: record?.submission_notes ?? ""
      };
    }
    for (const week of activeWeeks) {
      nextWeeks[draftKey(week)] = weekAttendanceFromData(week);
    }
    setEdits(next);
    setWeekEdits(nextWeeks);
  }, [activeEmployee, activeLines, activeWeeks, recordByUid]);

  if (!profiles.length || !activeEmployee) {
    return (
      <section className="approval-empty">
        <ClipboardCheck size={24} />
        <strong>No employee review drafts available</strong>
        <p>High-confidence CapEx and OpEx records appear here after ingestion, classification, and team-lead resolution.</p>
      </section>
    );
  }

  if (!sortedProfiles.length) {
    return (
      <section className="employee-directory-shell">
        <aside className="employee-directory">
          <div className="section-title">
            <h4>Employees</h4>
            <span>0 review packets</span>
          </div>
          <div className="directory-search">
            <input
              value={search}
              onChange={(event) => onSearch(event.target.value)}
              placeholder="Search employee, ID, title, team..."
            />
          </div>
          <p className="empty-note">No employees match this search.</p>
        </aside>
      </section>
    );
  }

  const activeKey = activeEmployee.employeeId;
  const totalRecovery = activeWeeks.reduce((sum, week) => sum + week.estimated_recovery_usd, 0);
  const firstWeek = activeWeeks[0]?.week_start ?? "";
  const lastWeek = activeWeeks[activeWeeks.length - 1]?.week_end ?? "";

  function updateEdit(recordUid: string, patch: Partial<ReviewLineEdit>) {
    setEdits((current) => ({
      ...current,
      [recordUid]: { ...current[recordUid], ...patch }
    }));
  }

  function updateWeekEdit(weekKey: string, patch: Partial<WeekAttendanceEdit>) {
    setWeekEdits((current) => ({
      ...current,
      [weekKey]: { ...current[weekKey], ...patch }
    }));
  }

  async function saveChanges(submitAfterSave: boolean) {
    setSaving(true);
    try {
      for (const week of activeWeeks) {
        const attendanceEdit = weekEdits[draftKey(week)];
        for (const line of week.line_items) {
          const edit = edits[line.record_uid];
          const record = recordByUid.get(line.record_uid);
          if (!edit || !record) continue;
          const request: {
            classification?: Classification;
            project_code?: string;
            holiday_days?: number;
            pto_days?: number;
            sick_days?: number;
            submission_notes?: string;
            note?: string;
          } = { note: submitAfterSave ? "Employee submitted correction" : "Employee saved draft correction" };
          if (edit.classification !== effectiveClassification(record)) request.classification = edit.classification;
          if (edit.project_code !== record.project_code) request.project_code = edit.project_code;
          if (attendanceEdit && attendanceEdit.holiday_days !== Number(record.holiday_days || 0)) {
            request.holiday_days = attendanceEdit.holiday_days;
          }
          if (attendanceEdit && attendanceEdit.pto_days !== Number(record.pto_days || 0)) {
            request.pto_days = attendanceEdit.pto_days;
          }
          if (attendanceEdit && attendanceEdit.sick_days !== Number(record.sick_days || 0)) {
            request.sick_days = attendanceEdit.sick_days;
          }
          if (edit.submission_notes !== (record.submission_notes ?? "")) request.submission_notes = edit.submission_notes;
          if (
            request.classification ||
            request.project_code !== undefined ||
            request.holiday_days !== undefined ||
            request.pto_days !== undefined ||
            request.sick_days !== undefined ||
            request.submission_notes !== undefined
          ) {
            await onSaveLine(line.record_uid, request);
          }
        }
      }
      if (submitAfterSave) {
        await onSubmitDraft(activeLines.map((line) => line.record_uid));
      }
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="employee-directory-shell">
      <aside className="employee-directory">
        <div className="directory-search">
          <input
            value={search}
            onChange={(event) => onSearch(event.target.value)}
            placeholder="Search employee, ID, title, team..."
          />
        </div>
        <div className="directory-count">{sortedProfiles.length} employees</div>
        <div className="employee-directory-list">
          {sortedProfiles.map((profile) => {
            const key = profile.employeeId;
            return (
              <button className={key === activeKey ? "active" : ""} key={key} onClick={() => onSelectEmployee(key)}>
                <span>
                  <strong>{profile.employeeName}</strong>
                  <em>{profile.employeeId} · {profile.teamName}</em>
                </span>
                <b>{pct(profile.capitalisationPct)}</b>
              </button>
            );
          })}
        </div>
      </aside>

      <article className="employee-review-panel">
        <div className="approval-hero">
          <div>
            <span className="eyebrow">Review-and-confirm packet</span>
            <h3>{activeEmployee.employeeName}</h3>
            <p>{activeEmployee.employeeId} · {activeEmployee.jobTitle} · {activeEmployee.teamName} · {firstWeek} to {lastWeek}</p>
          </div>
          <span className="approval-status">Ready for employee</span>
        </div>

        <div className="approval-summary-grid">
          <MiniMetric icon={ClipboardCheck} label="Total hours" value={number(activeEmployee.totalHours)} />
          <MiniMetric icon={CheckCircle2} label="CapEx hours" value={number(activeEmployee.capexHours)} tone="capex" />
          <MiniMetric icon={ShieldCheck} label="OpEx hours" value={number(activeEmployee.opexHours)} tone="opex" />
          <MiniMetric icon={Gauge} label="CapEx split" value={pct(activeEmployee.capitalisationPct)} />
          <MiniMetric icon={Database} label="Recovery estimate" value={money(totalRecovery)} />
          <MiniMetric icon={Layers3} label="Weeks" value={number(activeWeeks.length)} />
        </div>

        <section className="employee-review-lines">
          <div className="section-title">
            <h4>Editable Timesheet Lines</h4>
            <span>{activeLines.length} lines across all weeks for this employee</span>
          </div>
          {activeWeeks.map((week) => (
            <div className="employee-review-week" key={`${week.employee_id}-${week.week_start}`}>
              {(() => {
                const weekKey = draftKey(week);
                const attendanceEdit = weekEdits[weekKey] ?? weekAttendanceFromData(week);
                return (
                  <div className="review-week-header">
                    <div>
                      <strong>{week.week_start} to {week.week_end}</strong>
                      <span>{number(week.total_hours)}h · {pct(week.capitalisation_pct)} CapEx · {week.line_items.length} lines · {number(workingDaysForWeek(week, attendanceEdit))} work days</span>
                    </div>
                    <div className="review-week-attendance">
                      {([
                        ["holiday_days", "Holidays"],
                        ["pto_days", "PTO"],
                        ["sick_days", "Sick"]
                      ] as const).map(([field, label]) => (
                        <label key={field}>
                          {label}
                          <input
                            min="0"
                            step="0.5"
                            type="number"
                            value={attendanceEdit[field]}
                            onChange={(event) => updateWeekEdit(weekKey, { [field]: Number(event.target.value) })}
                          />
                        </label>
                      ))}
                    </div>
                  </div>
                );
              })()}
              {week.line_items.map((line) => {
                const record = recordByUid.get(line.record_uid);
                const edit = edits[line.record_uid] ?? {
                  classification: line.classification,
                  project_code: line.project_code,
                  submission_notes: record?.submission_notes ?? ""
                };
                return (
                  <article className="employee-review-line" key={line.record_uid}>
                    <div className="review-line-main">
                      <strong>{line.activity_type}</strong>
                      <span>{number(line.hours)}h · {line.project_name}</span>
                      <p>{line.evidence_summary}</p>
                    </div>
                    <label>
                      Classification
                      <select
                        value={edit.classification}
                        onChange={(event) => updateEdit(line.record_uid, { classification: event.target.value as Classification })}
                      >
                        <option value="CapEx">CapEx</option>
                        <option value="OpEx">OpEx</option>
                        <option value="Review">Review</option>
                      </select>
                    </label>
                    <label>
                      Project Code
                      <input
                        list="employee-review-projects"
                        value={edit.project_code}
                        onChange={(event) => updateEdit(line.record_uid, { project_code: event.target.value })}
                      />
                    </label>
                    <label className="review-notes">
                      Notes
                      <textarea
                        value={edit.submission_notes}
                        onChange={(event) => updateEdit(line.record_uid, { submission_notes: event.target.value })}
                        placeholder="Add employee clarification or correction notes"
                      />
                    </label>
                    <button className="review-audit-link" onClick={() => onAudit(line)}>Audit</button>
                  </article>
                );
              })}
            </div>
          ))}
          <datalist id="employee-review-projects">
            {projectOptions.map((projectCode) => (
              <option key={projectCode} value={projectCode} />
            ))}
          </datalist>
        </section>

        <div className="employee-review-actions">
          <button disabled={saving} onClick={() => saveChanges(false)}>Save Changes</button>
          <button disabled={saving} className="primary" onClick={() => saveChanges(true)}>
            {saving ? "Submitting..." : "Submit Draft"}
          </button>
        </div>
      </article>
    </section>
  );
}

function EmployeeDirectoryWorkspace({
  profiles,
  selectedEmployee,
  selectedEmployeeId,
  search,
  records,
  onSearch,
  onSelectEmployee,
  onAudit
}: {
  profiles: EmployeeProfile[];
  selectedEmployee?: EmployeeProfile;
  selectedEmployeeId: string;
  search: string;
  records: RecordItem[];
  onSearch: (value: string) => void;
  onSelectEmployee: (employeeId: string) => void;
  onAudit: (line: DraftLine) => void;
}) {
  const sortedProfiles = useMemo(
    () =>
      profiles
        .map((profile) => ({
          profile,
          score: fuzzyScore(
            `${profile.employeeId} ${profile.employeeName} ${profile.jobTitle} ${profile.teamName} ${profile.managerId}`,
            search
          )
        }))
        .filter((item): item is { profile: EmployeeProfile; score: number } => item.score !== null)
        .sort((left, right) => {
          if (left.score !== right.score) return left.score - right.score;
          return left.profile.employeeId.localeCompare(right.profile.employeeId, undefined, { numeric: true });
        })
        .map((item) => item.profile),
    [profiles, search]
  );
  const selectedInSearch = sortedProfiles.find((profile) => profile.employeeId === selectedEmployeeId);
  const activeEmployee = selectedInSearch ?? sortedProfiles[0] ?? selectedEmployee;

  if (!profiles.length) {
    return (
      <section className="approval-empty">
        <ClipboardCheck size={24} />
        <strong>No employee timesheets available</strong>
        <p>Confident CapEx and OpEx records will appear here after ingestion and classification.</p>
      </section>
    );
  }

  if (!activeEmployee) {
    return (
      <section className="employee-directory-shell">
        <aside className="employee-directory">
          <div className="directory-search">
            <input value={search} onChange={(event) => onSearch(event.target.value)} placeholder="Search employee, ID, title, team..." />
          </div>
          <p className="empty-note">No employees match this search.</p>
        </aside>
      </section>
    );
  }

  const lines = activeEmployee.weeks.flatMap((week) => week.line_items);
  const sourceRecords = lines
    .map((line) => records.find((record) => record._recordUid === line.record_uid))
    .filter((record): record is RecordItem => Boolean(record));
  const expectedHours = sourceRecords.reduce((sum, record) => {
    const key = `${record.employee_id}-${record.week_start_date}`;
    return sum + (sourceRecords.findIndex((item) => `${item.employee_id}-${item.week_start_date}` === key) === sourceRecords.indexOf(record)
      ? Number(record.actual_working_days || 0) * 8
      : 0);
  }, 0);
  const avgConfidence = lines.length ? lines.reduce((sum, line) => sum + line.confidence, 0) / lines.length : 0;
  const matchedEvidence = sourceRecords.filter((record) => Number(record._matchedExcel || 0) > 0).length;
  const topProject = activeEmployee.projectMix[0];

  return (
    <section className="employee-directory-shell">
      <aside className="employee-directory">
        <div className="directory-search">
          <input
            value={search}
            onChange={(event) => onSearch(event.target.value)}
            placeholder="Search employee, ID, title, team..."
          />
        </div>
        <div className="directory-count">{sortedProfiles.length} employees</div>
        <div className="employee-directory-list">
          {sortedProfiles.map((profile) => (
            <button
              className={activeEmployee.employeeId === profile.employeeId ? "active" : ""}
              key={profile.employeeId}
              onClick={() => onSelectEmployee(profile.employeeId)}
            >
              <span>
                <strong>{profile.employeeName}</strong>
                <em>{profile.employeeId} · {profile.teamName}</em>
              </span>
              <b>{pct(profile.capitalisationPct)}</b>
            </button>
          ))}
        </div>
      </aside>

      <article className="employee-profile-panel">
        <div className="employee-profile-hero">
          <div>
            <span className="eyebrow">Employee Timesheet Profile</span>
            <h3>{activeEmployee.employeeName}</h3>
            <p>{activeEmployee.jobTitle} · {activeEmployee.jobFamily} · {activeEmployee.teamName} · Manager {activeEmployee.managerId}</p>
          </div>
          <div
            className="approval-donut"
            style={{
              background: `conic-gradient(var(--capex) 0 ${activeEmployee.capitalisationPct}%, var(--opex-bg) ${activeEmployee.capitalisationPct}% 100%)`
            }}
          >
            <strong>{pct(activeEmployee.capitalisationPct)}</strong>
            <span>CapEx</span>
          </div>
        </div>

        <div className="approval-summary-grid">
          <MiniMetric icon={CalendarDays} label="Weeks" value={number(activeEmployee.weeks.length)} />
          <MiniMetric icon={ClipboardCheck} label="Total hours" value={number(activeEmployee.totalHours)} />
          <MiniMetric icon={CheckCircle2} label="CapEx hours" value={number(activeEmployee.capexHours)} tone="capex" />
          <MiniMetric icon={ShieldCheck} label="OpEx hours" value={number(activeEmployee.opexHours)} tone="opex" />
          <MiniMetric icon={Gauge} label="Avg confidence" value={number(avgConfidence)} />
          <MiniMetric icon={Database} label="Matched evidence" value={number(matchedEvidence)} />
        </div>

        <div className="employee-insight-grid">
          <section className="approval-visual-card">
            <div className="section-title">
              <h4>Project Contribution</h4>
              <span>{topProject ? `${topProject.name} leads at ${number(topProject.hours)}h` : "No project data"}</span>
            </div>
            <AllocationBars items={activeEmployee.projectMix} totalHours={activeEmployee.totalHours} />
          </section>

          <section className="approval-visual-card">
            <div className="section-title">
              <h4>Activity Mix</h4>
              <span>Work pattern by activity type</span>
            </div>
            <ActivityStack items={activeEmployee.activityMix} totalHours={activeEmployee.totalHours} />
          </section>

        </div>

        <section className="employee-week-history">
          <div className="section-title">
            <h4>Timesheet History Across Weeks</h4>
            <span>{number(expectedHours)} expected hours from working-day context</span>
          </div>
          <div className="employee-week-grid">
            {activeEmployee.weeks.map((week) => (
              <EmployeeWeekHistoryCard
                key={draftKey(week)}
                week={week}
                records={records}
                onAudit={onAudit}
              />
            ))}
          </div>
        </section>
      </article>
    </section>
  );
}

function EmployeeWeekHistoryCard({
  week,
  records,
  onAudit
}: {
  week: Draft;
  records: RecordItem[];
  onAudit: (line: DraftLine) => void;
}) {
  const firstRecord = week.line_items
    .map((line) => records.find((record) => record._recordUid === line.record_uid))
    .find((record): record is RecordItem => Boolean(record));

  return (
    <article className="employee-week-card">
      <div className="week-card-head">
        <CalendarDays size={16} />
        <strong>{week.week_start}</strong>
        <span>{number(week.total_hours)}h · {pct(week.capitalisation_pct)} CapEx</span>
      </div>
      <div className="week-availability-grid">
        <span><strong>{number(firstRecord?.actual_working_days ?? 0)}</strong> work days</span>
        <span><strong>{number(firstRecord?.pto_days ?? 0)}</strong> PTO</span>
        <span><strong>{number(firstRecord?.sick_days ?? 0)}</strong> sick</span>
        <span><strong>{number(firstRecord?.holiday_days ?? 0)}</strong> holiday</span>
      </div>
      <div className="week-classification-bar">
        <span className="capex" style={{ width: `${week.total_hours ? (week.capex_hours / week.total_hours) * 100 : 0}%` }} />
        <span className="opex" style={{ width: `${week.total_hours ? (week.opex_hours / week.total_hours) * 100 : 0}%` }} />
      </div>
      <div className="week-line-list compact">
        {week.line_items.map((line) => (
          <button key={line.record_uid} onClick={() => onAudit(line)}>
            <span className={`dot ${classNameFor(line.classification)}`} />
            <strong>{line.project_code}</strong>
            <span>{line.activity_type}</span>
            <em>{number(line.hours)}h</em>
          </button>
        ))}
      </div>
    </article>
  );
}

function EmployeeDraftApprovalWorkspace({
  drafts,
  selectedDraft,
  selectedKey,
  records,
  onSelectDraft,
  onAudit,
  onOpenEscalations
}: {
  drafts: Draft[];
  selectedDraft?: Draft;
  selectedKey: string;
  records: RecordItem[];
  onSelectDraft: (key: string) => void;
  onAudit: (line: DraftLine) => void;
  onOpenEscalations: () => void;
}) {
  if (!drafts.length || !selectedDraft) {
    return (
      <section className="approval-empty">
        <ClipboardCheck size={24} />
        <strong>No approval drafts available</strong>
        <p>Confident CapEx and OpEx records will appear here after ingestion and classification.</p>
      </section>
    );
  }

  const projectMap = new Map<string, NamedValue & { projectName: string; activities: Set<string> }>();
  const activityMap = new Map<string, NamedValue>();
  for (const line of selectedDraft.line_items) {
    const item = projectMap.get(line.project_code) ?? {
      name: line.project_code,
      projectName: line.project_name,
      hours: 0,
      capexHours: 0,
      opexHours: 0,
      confidenceTotal: 0,
      count: 0,
      activities: new Set<string>()
    };
    item.hours += line.hours;
    item.capexHours += line.classification === "CapEx" ? line.hours : 0;
    item.opexHours += line.classification === "OpEx" ? line.hours : 0;
    item.confidenceTotal += line.confidence;
    item.count += 1;
    item.activities.add(line.activity_type);
    projectMap.set(line.project_code, item);
    addNamedValue(activityMap, line.activity_type, line);
  }
  const projectCards = Array.from(projectMap.values()).sort((left, right) => right.hours - left.hours);
  const activityMix = topItems(activityMap);
  const topProject = projectCards[0];
  const approvalStatus = selectedDraft.capitalisation_pct >= 0 ? "Ready" : "Needs Review";
  const linkedRecords = selectedDraft.line_items
    .map((line) => records.find((record) => record._recordUid === line.record_uid))
    .filter((record): record is RecordItem => Boolean(record));
  const expectedHours = linkedRecords[0]?.actual_working_days ? linkedRecords[0].actual_working_days * 8 : selectedDraft.total_hours;
  const hourDelta = selectedDraft.total_hours - expectedHours;
  const avgConfidence = selectedDraft.line_items.length
    ? selectedDraft.line_items.reduce((sum, line) => sum + line.confidence, 0) / selectedDraft.line_items.length
    : 0;
  const keywordCloud = buildKeywordCloud(selectedDraft.line_items);

  return (
    <section className="approval-workspace">
      <aside className="approval-queue">
        <div className="section-title">
          <h4>Employee-Week Queue</h4>
          <span>{drafts.length} packets</span>
        </div>
        <div className="approval-queue-list">
          {drafts.map((draft) => {
            const key = draftKey(draft);
            const isActive = key === (selectedKey || draftKey(selectedDraft));
            return (
              <button className={isActive ? "active" : ""} key={key} onClick={() => onSelectDraft(key)}>
                <span>
                  <strong>{draft.employee_name}</strong>
                  <em>{draft.week_start} to {draft.week_end}</em>
                </span>
                <b>{number(draft.total_hours)}h</b>
                <small>{pct(draft.capitalisation_pct)} CapEx</small>
              </button>
            );
          })}
        </div>
      </aside>

      <article className="approval-packet">
        <div className="approval-hero">
          <div>
            <span className="eyebrow">Approval Packet</span>
            <h3>{selectedDraft.employee_name}</h3>
            <p>{selectedDraft.job_title} · {selectedDraft.team_name} · {selectedDraft.week_start} to {selectedDraft.week_end}</p>
          </div>
          <span className="approval-status">{approvalStatus}</span>
        </div>

        <div className="approval-summary-grid">
          <MiniMetric icon={ClipboardCheck} label="Total hours" value={number(selectedDraft.total_hours)} />
          <MiniMetric icon={CheckCircle2} label="CapEx hours" value={number(selectedDraft.capex_hours)} tone="capex" />
          <MiniMetric icon={ShieldCheck} label="OpEx hours" value={number(selectedDraft.opex_hours)} tone="opex" />
          <MiniMetric icon={Gauge} label="CapEx split" value={pct(selectedDraft.capitalisation_pct)} />
          <MiniMetric icon={Database} label="Recovery estimate" value={money(selectedDraft.estimated_recovery_usd)} />
          <MiniMetric icon={Layers3} label="Line items" value={number(selectedDraft.line_items.length)} />
        </div>

        <div className="approval-visual-grid">
          <section className="approval-visual-card">
            <div className="section-title">
              <h4>Capitalization Split</h4>
              <span>Employee-week outcome</span>
            </div>
            <div
              className="approval-donut"
              style={{
                background: `conic-gradient(var(--capex) 0 ${selectedDraft.capitalisation_pct}%, var(--opex-bg) ${selectedDraft.capitalisation_pct}% 100%)`
              }}
            >
              <strong>{pct(selectedDraft.capitalisation_pct)}</strong>
              <span>CapEx</span>
            </div>
          </section>

          <section className="approval-visual-card">
            <div className="section-title">
              <h4>Hours Check</h4>
              <span>Allocated vs expected</span>
            </div>
            <div className="hours-check">
              <div className="hours-check-row">
                <strong>{number(selectedDraft.total_hours)}h</strong>
                <span>allocated</span>
              </div>
              <div className="hours-track">
                <span style={{ width: `${expectedHours ? Math.min((selectedDraft.total_hours / expectedHours) * 100, 130) : 0}%` }} />
              </div>
              <p>{number(expectedHours)}h expected · {hourDelta === 0 ? "balanced" : `${number(Math.abs(hourDelta))}h ${hourDelta > 0 ? "over" : "under"}`}</p>
            </div>
          </section>

          <section className="approval-visual-card">
            <div className="section-title">
              <h4>Activity Mix</h4>
              <span>Hours by activity</span>
            </div>
            <ActivityStack items={activityMix} totalHours={selectedDraft.total_hours} />
          </section>

          <section className="approval-visual-card">
            <div className="section-title">
              <h4>Evidence Themes</h4>
              <span>Terms from notes and evidence</span>
            </div>
            <WordCloud words={keywordCloud} />
          </section>
        </div>

        <section className="approval-narrative">
          <strong>Draft Summary</strong>
          <p>
            {number(selectedDraft.total_hours)} hours are ready for approval for {selectedDraft.employee_name}.{" "}
            {number(selectedDraft.capex_hours)} hours are classified as CapEx and {number(selectedDraft.opex_hours)} hours as OpEx
            {topProject ? `, led by ${topProject.name} (${number(topProject.hours)}h).` : "."}
          </p>
          <div className="approval-actions">
            <button onClick={onOpenEscalations}>Open Escalations</button>
          </div>
        </section>

        <section className="approval-review-grid">
          <div className="approval-review-card">
            <div className="section-title">
              <h4>Confidence Strip</h4>
              <span>Line-level review signal · avg {number(avgConfidence)}</span>
            </div>
            <div className="confidence-strip">
              {selectedDraft.line_items.map((line) => (
                <button
                  key={line.record_uid}
                  className={line.confidence < 70 ? "low" : line.confidence < 85 ? "medium" : "high"}
                  style={{ width: `${Math.max(7, 100 / selectedDraft.line_items.length)}%` }}
                  onClick={() => onAudit(line)}
                  title={`${line.project_code} · ${line.activity_type} · ${number(line.confidence)} confidence`}
                />
              ))}
            </div>
          </div>

          <div className="approval-review-card">
            <div className="section-title">
              <h4>Chronological Line Sequence</h4>
              <span>Click any item for audit evidence</span>
            </div>
            <div className="approval-line-sequence">
              {selectedDraft.line_items.map((line) => (
                <button key={line.record_uid} onClick={() => onAudit(line)}>
                  <span className={`dot ${classNameFor(line.classification)}`} />
                  <strong>{line.project_code}</strong>
                  <em>{line.activity_type}</em>
                  <b>{number(line.hours)}h</b>
                </button>
              ))}
            </div>
          </div>
        </section>

        <section className="approval-projects">
          <div className="section-title">
            <h4>Project Allocation</h4>
            <span>Approval-ready project summary</span>
          </div>
          <div className="approval-project-grid">
            {projectCards.map((project) => {
              const capexPct = project.hours ? (project.capexHours / project.hours) * 100 : 0;
              return (
                <article className="approval-project-card" key={project.name}>
                  <div>
                    <strong>{project.name}</strong>
                    <span>{project.projectName}</span>
                  </div>
                  <div className="mini-bar">
                    <span style={{ width: `${capexPct}%` }} />
                  </div>
                  <div className="project-group-stats">
                    <span>{number(project.hours)}h</span>
                    <span>{pct(capexPct)} CapEx</span>
                    <span>{number(project.confidenceTotal / project.count)} confidence</span>
                  </div>
                  <p>{Array.from(project.activities).join(", ")}</p>
                </article>
              );
            })}
          </div>
        </section>

        <details className="source-record-details">
          <summary>Show source records</summary>
          <LineItems lines={selectedDraft.line_items} onAudit={onAudit} />
        </details>
      </article>
    </section>
  );
}

function EmployeeCommandCenter({
  profile,
  onAudit
}: {
  profile: EmployeeProfile;
  onAudit: (line: DraftLine) => void;
}) {
  const topProject = profile.projectMix[0];
  const projectFocus = profile.totalHours && topProject ? (topProject.hours / profile.totalHours) * 100 : 0;
  const lineCount = profile.weeks.flatMap((week) => week.line_items).length;
  const allocationDensity = profile.weeks.length ? lineCount / profile.weeks.length : 0;

  return (
    <section className="employee-command">
      <div className="employee-hero">
        <div>
          <span className="eyebrow">Employee Review</span>
          <h3>{profile.employeeName}</h3>
          <p>{profile.jobTitle} · {profile.jobFamily} · {profile.teamName}</p>
        </div>
        <div
          className="donut"
          style={{
            background: `conic-gradient(var(--capex) 0 ${profile.capitalisationPct}%, var(--opex-bg) ${profile.capitalisationPct}% 100%)`
          }}
          aria-label={`Capitalisation ${pct(profile.capitalisationPct)}`}
        >
          <strong>{pct(profile.capitalisationPct)}</strong>
          <span>CapEx</span>
        </div>
      </div>

      <div className="employee-kpis">
        <MiniMetric icon={ClipboardCheck} label="Total hours" value={number(profile.totalHours)} />
        <MiniMetric icon={CheckCircle2} label="CapEx hours" value={number(profile.capexHours)} tone="capex" />
        <MiniMetric icon={ShieldCheck} label="OpEx hours" value={number(profile.opexHours)} tone="opex" />
        <MiniMetric icon={Gauge} label="Avg confidence" value={number(profile.avgConfidence)} />
        <MiniMetric icon={Layers3} label="Project focus" value={pct(projectFocus)} />
        <MiniMetric icon={TrendingUp} label="Lines / week" value={number(allocationDensity)} />
      </div>

      <div className="employee-grid">
        <div className="insight-panel wide">
          <div className="section-title">
            <h4>Project Allocation</h4>
            <span>Hours by project and capitalization split</span>
          </div>
          <AllocationBars items={profile.projectMix} totalHours={profile.totalHours} />
        </div>

        <div className="insight-panel">
          <div className="section-title">
            <h4>Activity Mix</h4>
            <span>Where the week was spent</span>
          </div>
          <ActivityStack items={profile.activityMix} totalHours={profile.totalHours} />
        </div>

        <div className="insight-panel">
          <div className="section-title">
            <h4>Evidence Themes</h4>
            <span>Signals surfaced from explanations</span>
          </div>
          <WordCloud words={profile.keywordCloud} />
        </div>
      </div>

      <div className="insight-panel">
        <div className="section-title">
          <h4>Chronological Review</h4>
          <span>Week-by-week line item sequence</span>
        </div>
        <div className="week-timeline">
          {profile.weeks.map((week) => (
            <article className="week-card" key={`${week.employee_id}-${week.week_start}`}>
              <div className="week-card-head">
                <CalendarDays size={16} />
                <strong>{week.week_start}</strong>
                <span>{number(week.total_hours)}h · {pct(week.capitalisation_pct)} CapEx</span>
              </div>
              <div className="week-line-list">
                {week.line_items.map((line) => (
                  <button key={line.record_uid} onClick={() => onAudit(line)}>
                    <span className={`dot ${classNameFor(line.classification)}`} />
                    <strong>{line.project_code}</strong>
                    <span>{line.activity_type}</span>
                    <em>{number(line.hours)}h</em>
                  </button>
                ))}
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

function MiniMetric({
  icon: Icon,
  label,
  value,
  tone
}: {
  icon: LucideIcon;
  label: string;
  value: string;
  tone?: string;
}) {
  return (
    <div className={`mini-metric ${tone ?? ""}`}>
      <Icon size={16} />
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function AllocationBars({ items, totalHours }: { items: NamedValue[]; totalHours: number }) {
  return (
    <div className="allocation-list">
      {items.map((item) => {
        const width = totalHours ? (item.hours / totalHours) * 100 : 0;
        const capexPct = item.hours ? (item.capexHours / item.hours) * 100 : 0;
        return (
          <div className="allocation-row" key={item.name}>
            <div className="allocation-label">
              <strong>{item.name}</strong>
              <span>{number(item.hours)}h · {pct(capexPct)} CapEx · avg confidence {number(item.confidenceTotal / item.count)}</span>
            </div>
            <div className="allocation-track">
              <span className="total" style={{ width: `${Math.max(width, 2)}%` }} />
              <span className="capex-fill" style={{ width: `${Math.max((width * capexPct) / 100, 0)}%` }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}

function ActivityStack({ items, totalHours }: { items: NamedValue[]; totalHours: number }) {
  return (
    <div className="activity-stack">
      {items.map((item) => {
        const size = totalHours ? Math.max(52, Math.min(138, 44 + (item.hours / totalHours) * 220)) : 58;
        return (
          <div
            className="activity-bubble"
            key={item.name}
            style={{ width: `${size}px`, height: `${size}px` }}
          >
            <strong>{number(item.hours)}h</strong>
            <span>{item.name}</span>
          </div>
        );
      })}
    </div>
  );
}

function WordCloud({ words }: { words: Array<{ word: string; weight: number }> }) {
  if (!words.length) {
    return <p className="empty-note">Evidence terms appear after classification.</p>;
  }
  const max = Math.max(...words.map((word) => word.weight));
  return (
    <div className="word-cloud">
      {words.map((word) => (
        <span
          key={word.word}
          style={{ fontSize: `${12 + (word.weight / max) * 12}px` }}
        >
          {word.word}
        </span>
      ))}
    </div>
  );
}

function ProjectRecordExplorer({
  groups,
  selectedRecord,
  onSelectRecord,
  onAudit
}: {
  groups: ProjectRecordGroup[];
  selectedRecord: RecordItem | null;
  onSelectRecord: (record: RecordItem) => void;
  onAudit: (record: RecordItem) => void;
}) {
  const fallbackRecord = groups[0]?.employees[0]?.records[0] ?? null;
  const activeRecord = selectedRecord ?? fallbackRecord;
  const activeProject = groups.find((group) => group.projectCode === activeRecord?.project_code);
  const activeEmployee = activeProject?.employees.find((employee) => employee.employeeId === activeRecord?.employee_id);

  return (
    <section className="project-record-shell">
      <div className="section-title">
        <h4>Project Code Record Explorer</h4>
        <span>Grouped by project code, then employee, with Excel-row detail on selection</span>
      </div>
      <div className="project-record-grid">
        <div className="project-groups">
          {groups.map((group) => {
            const capexPct = group.totalHours ? (group.capexHours / group.totalHours) * 100 : 0;
            return (
              <article className="project-group" key={group.projectCode}>
                <div className="project-group-head">
                  <div>
                    <strong>{group.projectCode}</strong>
                    <span>{group.projectName}</span>
                  </div>
                  <em>{number(group.totalHours)}h</em>
                </div>
                <div className="mini-bar">
                  <span style={{ width: `${capexPct}%` }} />
                </div>
                <div className="project-group-stats">
                  <span>{pct(capexPct)} CapEx</span>
                  <span>{group.employees.length} employees</span>
                </div>
                <div className="employee-list">
                  {group.employees.map((employee) => {
                    const firstRecord = employee.records[0];
                    const isActive =
                      activeRecord?.project_code === group.projectCode &&
                      activeRecord?.employee_id === employee.employeeId;
                    return (
                      <button
                        className={isActive ? "active" : ""}
                        key={`${group.projectCode}-${employee.employeeId}`}
                        onClick={() => onSelectRecord(firstRecord)}
                      >
                        <span>
                          <strong>{employee.employeeName}</strong>
                          <em>{employee.jobTitle}</em>
                        </span>
                        <b>{number(employee.hours)}h</b>
                      </button>
                    );
                  })}
                </div>
              </article>
            );
          })}
        </div>
        <ExcelRecordDetail
          record={activeRecord}
          relatedRecords={activeEmployee?.records ?? []}
          onSelectRecord={onSelectRecord}
          onAudit={onAudit}
        />
      </div>
    </section>
  );
}

function ExcelRecordDetail({
  record,
  relatedRecords,
  onSelectRecord,
  onAudit
}: {
  record: RecordItem | null;
  relatedRecords: RecordItem[];
  onSelectRecord: (record: RecordItem) => void;
  onAudit: (record: RecordItem) => void;
}) {
  if (!record) {
    return (
      <aside className="excel-detail empty">
        <h3>No records loaded</h3>
        <p>Upload the May 22 workbook to inspect records by project code.</p>
      </aside>
    );
  }

  const identity: Array<[string, unknown]> = [
    ["Employee ID", record.employee_id],
    ["Full Name", record.full_name],
    ["Job Title", record.job_title],
    ["Job Family", record.job_family],
    ["Team", record.team_name],
    ["Org Unit", record.org_unit],
    ["Manager", record.manager_id]
  ];
  const week: Array<[string, unknown]> = [
    ["Week Start", record.week_start_date],
    ["Week End", record.week_end_date],
    ["Standard Days", record.standard_days],
    ["Holiday Days", record.holiday_days],
    ["PTO Days", record.pto_days],
    ["Sick Days", record.sick_days],
    ["Actual Working Days", record.actual_working_days]
  ];
  const signals: Array<[string, unknown]> = [
    ["Meetings", record.meeting_count],
    ["Tickets", record.ticket_count],
    ["Email Volume", record.email_volume],
    ["Code Commits", record.code_commit_count],
    ["System Activity", record.system_activity_score]
  ];
  const allocation: Array<[string, unknown]> = [
    ["Project Code", record.project_code],
    ["Project Name", record.project_name],
    ["Activity Type", record.activity_type],
    ["Hours Allocated", record.hours_allocated],
    ["Classification", effectiveClassification(record)],
    ["Confidence", record._confidence],
    ["Source", record._source ?? "Excel"]
  ];

  return (
    <aside className="excel-detail">
      <div className="excel-detail-head">
        <div>
          <span className="eyebrow">Excel Row Detail</span>
          <h3>{record.full_name}</h3>
          <p>{record.project_code} · {record.week_start_date}</p>
        </div>
        <span className={`badge ${classNameFor(effectiveClassification(record))}`}>
          {effectiveClassification(record)}
        </span>
      </div>

      <div className="excel-section-grid">
        <FieldSection title="Employee" rows={identity} />
        <FieldSection title="Week & Availability" rows={week} />
        <FieldSection title="Activity Signals" rows={signals} />
        <FieldSection title="Project Allocation" rows={allocation} />
      </div>

      <div className="detail-notes">
        <strong>Submission Notes</strong>
        <p>{record.submission_notes || "No notes supplied."}</p>
      </div>

      <div className="detail-notes">
        <strong>Evidence</strong>
        <p>{record._evidence}</p>
        <button onClick={() => onAudit(record)}>Open Audit Trail</button>
      </div>

      {relatedRecords.length > 1 && (
        <div className="related-records">
          <strong>Other rows for this employee under project</strong>
          {relatedRecords.map((item) => (
            <button
              className={item._recordUid === record._recordUid ? "active" : ""}
              key={item._recordUid}
              onClick={() => onSelectRecord(item)}
            >
              <span>{item.week_start_date}</span>
              <span>{item.activity_type}</span>
              <b>{number(Number(item.hours_allocated || 0))}h</b>
            </button>
          ))}
        </div>
      )}
    </aside>
  );
}

function FieldSection({ title, rows }: { title: string; rows: Array<[string, unknown]> }) {
  return (
    <section className="field-section">
      <h4>{title}</h4>
      <dl>
        {rows.map(([label, value]) => (
          <div key={label}>
            <dt>{label}</dt>
            <dd>{String(value ?? "—")}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

function agentStatusClass(status: string): string {
  const normalized = status.toLowerCase();
  if (normalized === "completed") return "completed";
  if (normalized === "fallback") return "fallback";
  if (normalized === "failed") return "failed";
  return "pending";
}

function agentOutputValue(value: unknown): string {
  if (value == null || value === "") return "—";
  if (Array.isArray(value)) return JSON.stringify(value);
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function AgentFlow({ trace }: { trace: NonNullable<RecordItem["_agentTrace"]> }) {
  const providerCopy = trace.provider === "stub"
    ? "Provider: local fallback"
    : trace.provider === "deterministic"
      ? "Provider: deterministic rules-only"
      : `Provider: ${trace.provider}${trace.model ? ` · ${trace.model}` : ""} · ${trace.steps.length} agents`;
  const adjustmentStep = trace.steps.find((step) => {
    const output = step.output ?? {};
    return output.confidence_adjusted !== undefined || output.confidenceAdjusted !== undefined;
  });
  const adjustmentOutput = adjustmentStep?.output ?? {};
  const originalConfidence = adjustmentOutput.confidence;
  const adjustedConfidence = adjustmentOutput.confidence_adjusted ?? adjustmentOutput.confidenceAdjusted;
  const hasAdjustment =
    originalConfidence !== undefined &&
    adjustedConfidence !== undefined &&
    String(originalConfidence) !== String(adjustedConfidence);

  return (
    <article className="panel agent-trace-panel">
      <div className="agent-trace-header">
        <div>
          <h4>Agent Pipeline Trace</h4>
          <p>{providerCopy}</p>
        </div>
        <Bot size={20} />
      </div>
      <div className="agent-flow">
        {trace.steps.map((step, index) => {
          const statusClass = agentStatusClass(step.status);
          const outputEntries = Object.entries(step.output ?? {});
          return (
            <div className="agent-step" key={`${step.agent}-${index}`}>
              <div className="agent-marker" />
              <div className="agent-step-body">
                <div className="agent-node">
                  <strong>{step.agent}</strong>
                  <em className={statusClass}>{step.status}</em>
                  {step.provider && step.provider !== "deterministic" && step.provider !== "error" && (
                    <span>{step.provider}</span>
                  )}
                </div>
                <p>{step.summary}</p>
                {outputEntries.length > 0 && (
                  <div className="agent-output-list">
                    {outputEntries.map(([key, value]) => (
                      <span
                        className={agentOutputValue(value).length > 90 ? "wide" : ""}
                        key={key}
                      >
                        <b>{key}:</b> {agentOutputValue(value)}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
      {hasAdjustment && (
        <div className="agent-confidence-note">
          LLM confidence adjustment applied: {String(originalConfidence)} -&gt; {String(adjustedConfidence)} (routing uses original {String(originalConfidence)})
        </div>
      )}
    </article>
  );
}

function Metric({
  label,
  value,
  icon: Icon,
  tone
}: {
  label: string;
  value: string;
  icon: LucideIcon;
  tone?: string;
}) {
  return (
    <div className={`metric ${tone ?? ""}`}>
      <Icon size={19} />
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function UploadPanel({
  title,
  subtitle,
  icon: Icon,
  accept,
  disabled,
  onFile
}: {
  title: string;
  subtitle: string;
  icon: LucideIcon;
  accept: string;
  disabled: boolean;
  onFile: (file?: File) => void;
}) {
  return (
    <label className={`upload-panel ${disabled ? "disabled" : ""}`}>
      <input
        type="file"
        accept={accept}
        disabled={disabled}
        onChange={(event: ChangeEvent<HTMLInputElement>) => onFile(event.target.files?.[0])}
      />
      <Icon size={22} />
      <strong>{title}</strong>
      <span>{subtitle}</span>
      <em><UploadCloud size={16} /> Upload</em>
    </label>
  );
}

function ComingSoonSources() {
  const sources: Array<{
    name: string;
    description: string;
    payload: string;
    icon: LucideIcon;
  }> = [
    {
      name: "Calendar",
      description: "Meeting load, planning ceremonies, field appointments, and delivery checkpoints.",
      payload: "Events, attendees, duration, project tags",
      icon: CalendarDays
    },
    {
      name: "Jira",
      description: "Ticket movement, sprint work, backlog items, defect resolution, and story delivery.",
      payload: "Issues, status changes, story points, links",
      icon: ClipboardCheck
    },
    {
      name: "GitHub",
      description: "Engineering contribution signals for build, automation, testing, and release work.",
      payload: "Commits, pull requests, reviews, repositories",
      icon: Layers3
    },
    {
      name: "Slack",
      description: "Collaboration themes and project-context evidence for timesheet explanations.",
      payload: "Channels, thread metadata, project references",
      icon: FileText
    },
    {
      name: "BigQuery",
      description: "Enterprise warehouse tables for workforce, project, finance, and allocation history.",
      payload: "SQL datasets, project marts, finance joins",
      icon: Database
    },
    {
      name: "Google Sheets",
      description: "Team-maintained planning sheets, allocation trackers, and project coding workbooks.",
      payload: "Sheets, ranges, tabs, named tables",
      icon: FileSpreadsheet
    }
  ];

  return (
    <section className="coming-soon-panel">
      <div className="section-title">
        <h4>Additional Connectors</h4>
        <span>Planned sources for stronger labor evidence and automated matching</span>
      </div>
      <div className="connector-card-grid">
        {sources.map((source) => {
          const Icon = source.icon;
          return (
            <article className="connector-card disabled-card" key={source.name}>
              <div className="connector-icon">
                <Icon size={20} />
              </div>
              <div>
                <div className="connector-card-head">
                  <strong>{source.name}</strong>
                  <span>Coming Soon</span>
                </div>
                <p>{source.description}</p>
              </div>
              <em>{source.payload}</em>
            </article>
          );
        })}
      </div>
    </section>
  );
}

function LineItems({ lines, onAudit }: { lines: DraftLine[]; onAudit: (line: DraftLine) => void }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Project</th>
            <th>Activity</th>
            <th>Hours</th>
            <th>Class</th>
            <th>Confidence</th>
            <th>Evidence</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {lines.map((line) => (
            <tr key={line.record_uid}>
              <td>
                <strong>{line.project_code}</strong>
                <span>{line.project_name}</span>
              </td>
              <td>{line.activity_type}</td>
              <td>{line.hours}</td>
              <td><span className={`badge ${classNameFor(line.classification)}`}>{line.classification}</span></td>
              <td>{line.confidence}</td>
              <td>{line.evidence_summary}</td>
              <td><button onClick={() => onAudit(line)}>Audit</button></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
