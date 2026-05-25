from __future__ import annotations

from typing import Any, Dict, List, Tuple

from app.config.settings import get_settings
from app.enrichment.pipeline import clean_text, to_number

SETTINGS = get_settings()
RULE_VERSION = SETTINGS.rule_version

PROJECT_REGISTRY: Dict[str, Dict[str, str]] = {
    "PRJ-5G-BUILD": {
        "name": "5G Network Infrastructure Build-Out",
        "designation": "CapEx",
        "funding_category": "Network Build",
        "phase": "Build",
    },
    "PRJ-FIBER-EXP": {
        "name": "Fiber Expansion Program",
        "designation": "CapEx",
        "funding_category": "Network Build",
        "phase": "Build",
    },
    "PRJ-SW-PLAT": {
        "name": "Software Platform Development",
        "designation": "CapEx",
        "funding_category": "Application Development",
        "phase": "Development",
    },
    "PRJ-INFRA-UPG": {
        "name": "Infrastructure Modernisation Program",
        "designation": "CapEx",
        "funding_category": "Infrastructure Modernisation",
        "phase": "Architecture",
    },
    "PRJ-PROD-LAUNCH": {
        "name": "New Product Development & Launch",
        "designation": "CapEx",
        "funding_category": "Product Development",
        "phase": "Pre-launch",
    },
    "PRJ-TOOL-DEV": {
        "name": "Internal Developer Tooling Initiative",
        "designation": "CapEx",
        "funding_category": "Internal Software",
        "phase": "Development",
    },
    "PRJ-CLOUD-MIG": {
        "name": "Cloud Migration & Re-architecture",
        "designation": "CapEx",
        "funding_category": "Cloud Re-architecture",
        "phase": "Migration",
    },
    "PRJ-NET-OPS": {
        "name": "Network Operations & Maintenance",
        "designation": "OpEx",
        "funding_category": "Operations",
        "phase": "Run",
    },
    "PRJ-IT-SUPP": {
        "name": "IT Support & Helpdesk Services",
        "designation": "OpEx",
        "funding_category": "Support",
        "phase": "Run",
    },
    "PRJ-OPS-ADMIN": {
        "name": "Operations Administration",
        "designation": "OpEx",
        "funding_category": "Administration",
        "phase": "Run",
    },
    "PRJ-CUST-ENG": {
        "name": "Customer Engineering Support",
        "designation": "OpEx",
        "funding_category": "Customer Support",
        "phase": "Run",
    },
    "PRJ-GEN-MAINT": {
        "name": "General Maintenance Activities",
        "designation": "OpEx",
        "funding_category": "Maintenance",
        "phase": "Run",
    },
}

CAPITALIZABLE_ACTIVITIES = {
    "detailed design",
    "build / development",
    "requirements gathering",
    "architecture review",
    "testing & qa",
    "technical documentation",
}

ALWAYS_OPEX_ACTIVITIES = {
    "maintenance & support",
    "administration",
    "incident response",
    "training & development",
}

CONDITIONAL_ACTIVITIES = {"meetings & coordination"}


def _signal(label: str, impact: int, kind: str) -> Dict[str, Any]:
    return {"label": label, "impact": impact, "kind": kind}


def _email_score(email_volume: str) -> int:
    return {"low": 0, "medium": 4, "high": 8}.get(email_volume.lower(), 0)


def evaluate_record(record: Dict[str, Any]) -> Tuple[int, List[Dict[str, Any]], str]:
    project_code = clean_text(record.get("project_code"))
    activity = clean_text(record.get("activity_type")).lower()
    job_family = clean_text(record.get("job_family"))
    notes = clean_text(record.get("submission_notes")).lower()
    hours = to_number(record.get("hours_allocated"))
    meeting_count = to_number(record.get("meeting_count"))
    ticket_count = to_number(record.get("ticket_count"))
    code_commits = to_number(record.get("code_commit_count"))
    system_score = to_number(record.get("system_activity_score"))
    email_volume = clean_text(record.get("email_volume"))

    signals: List[Dict[str, Any]] = []
    registry = PROJECT_REGISTRY.get(project_code)

    if not registry:
        signals.append(_signal(f"project code {project_code or 'missing'} is not in the project registry", -35, "quality"))
        return 25, signals, "Project code is unmapped; route to team lead before employee review."

    designation = registry["designation"]
    score = 50

    if designation == "CapEx":
        score += 22
        signals.append(_signal(f"{project_code} is registered as a CapEx-funded project", 22, "capex"))
    else:
        score -= 28
        signals.append(_signal(f"{project_code} is registered as an OpEx project", -28, "opex"))

    if activity in CAPITALIZABLE_ACTIVITIES:
        score += 22
        signals.append(_signal(f"activity '{record.get('activity_type')}' is capitalizable when tied to a build or development project", 22, "capex"))
    elif activity in ALWAYS_OPEX_ACTIVITIES:
        score -= 28
        signals.append(_signal(f"activity '{record.get('activity_type')}' is treated as operating expense under fixed-asset policy", -28, "opex"))
    elif activity in CONDITIONAL_ACTIVITIES:
        score -= 6
        signals.append(_signal("meetings and coordination are conditional; project context and signals are needed", -6, "policy"))
    else:
        score -= 10
        signals.append(_signal("unknown activity type lowers policy confidence", -10, "quality"))

    if code_commits >= 10:
        score += 12
        signals.append(_signal(f"{int(code_commits)} code commits indicate build or testing work", 12, "capex"))
    elif code_commits <= 1 and activity in CAPITALIZABLE_ACTIVITIES:
        score -= 4
        signals.append(_signal("low code activity weakens a build/development capitalization signal", -4, "quality"))

    if ticket_count >= 15:
        score += 8
        signals.append(_signal(f"{int(ticket_count)} tickets indicate substantive project execution", 8, "capex"))
    elif ticket_count <= 5 and designation == "OpEx":
        score -= 5
        signals.append(_signal("low ticket volume aligns with support/admin operating activity", -5, "opex"))

    if meeting_count >= 9 and activity in {"architecture review", "requirements gathering", "meetings & coordination", "technical documentation"}:
        score += 7
        signals.append(_signal(f"{int(meeting_count)} meetings support planning/design evidence", 7, "capex"))

    if system_score >= 75:
        score += 6
        signals.append(_signal(f"system activity score {int(system_score)} shows high digital work intensity", 6, "quality"))
    elif system_score <= 45 and designation == "OpEx":
        score -= 5
        signals.append(_signal(f"system activity score {int(system_score)} is consistent with low-intensity operational work", -5, "opex"))

    email_impact = _email_score(email_volume)
    if email_impact and activity in {"requirements gathering", "architecture review", "technical documentation"}:
        score += email_impact
        signals.append(_signal(f"{email_volume} email volume supports collaboration-heavy project work", email_impact, "capex"))

    if any(term in notes for term in ("maintenance", "support", "incident", "helpdesk", "training", "admin")):
        score -= 8
        signals.append(_signal("submission notes include operating/support language", -8, "opex"))
    if any(term in notes for term in ("build", "design", "development", "testing", "architecture", "migration", "feature")):
        score += 8
        signals.append(_signal("submission notes include build/design/development language", 8, "capex"))

    if hours <= 0:
        score -= 30
        signals.append(_signal("missing or zero allocated hours makes the line item invalid", -30, "quality"))

    if job_family:
        signals.append(_signal(f"job family context: {job_family}", 2, "quality"))

    bounded = max(0, min(100, int(round(score))))
    evidence = "; ".join(
        signal["label"]
        for signal in sorted(signals, key=lambda s: abs(s["impact"]), reverse=True)[:4]
    )
    return bounded, signals, evidence or "No strong classification signal available."


def classify_score(score: int, review_threshold: int | None = None) -> str:
    threshold = review_threshold if review_threshold is not None else SETTINGS.review_threshold
    if score >= 66:
        classification = "CapEx"
    elif score <= 44:
        classification = "OpEx"
    else:
        classification = "Review"
    if classification == "CapEx" and score < threshold:
        return "Review"
    return classification
