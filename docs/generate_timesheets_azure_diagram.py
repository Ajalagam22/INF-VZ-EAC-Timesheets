"""
Generate a professional Azure architecture diagram for EAC Labor Timesheets.
Outputs:
  docs/EAC_Timesheets_Azure_Architecture.png
  docs/EAC_Timesheets_Azure_Architecture.pdf
"""
from __future__ import annotations

import os
from pathlib import Path

OUT_DIR = Path(__file__).parent
os.environ.setdefault("MPLCONFIGDIR", str(OUT_DIR / ".mplconfig"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
PNG_OUT = OUT_DIR / "EAC_Timesheets_Azure_Architecture.png"
PDF_OUT = OUT_DIR / "EAC_Timesheets_Azure_Architecture.pdf"

C = {
    "bg": "#0d1117",
    "panel": "#161b22",
    "border": "#30363d",
    "blue": "#1f6feb",
    "blue_light": "#388bfd",
    "green": "#238636",
    "green_light": "#2ea043",
    "orange": "#d29922",
    "purple": "#8957e5",
    "red": "#da3633",
    "teal": "#0d7488",
    "white": "#e6edf3",
    "gray": "#8b949e",
    "label_bg": "#21262d",
    "vnet": "#1a2030",
}

FIG_W, FIG_H = 28, 18
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
ax.set_facecolor(C["bg"])
fig.patch.set_facecolor(C["bg"])
ax.set_xlim(0, FIG_W)
ax.set_ylim(0, FIG_H)
ax.axis("off")


def box(x, y, w, h, color, alpha=1.0, radius=0.22, lw=1.2, edge=None):
    edge = edge or color
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        linewidth=lw,
        edgecolor=edge,
        facecolor=color,
        alpha=alpha,
        zorder=2,
    )
    ax.add_patch(patch)


def txt(x, y, text, size=8.5, color=C["white"], weight="normal", ha="center", va="center", z=5):
    ax.text(
        x,
        y,
        text,
        fontsize=size,
        color=color,
        fontweight=weight,
        ha=ha,
        va=va,
        zorder=z,
        fontfamily="sans-serif",
        clip_on=False,
    )


def zone(x, y, w, h, face, edge, title):
    box(x, y, w, h, color=face, edge=edge, lw=1.2, alpha=0.40, radius=0.3)
    box(x, y + h - 0.52, w, 0.52, color=edge, edge=edge, lw=0, alpha=0.92, radius=0.2)
    txt(x + w / 2, y + h - 0.26, title, size=8.8, weight="bold")


def node(cx, cy, w, h, face=C["panel"], edge=C["gray"], title="", sub=""):
    box(cx - w / 2, cy - h / 2, w, h, color=face, edge=edge, lw=1.4)
    txt(cx, cy + (0.13 if sub else 0), title, size=8.2, weight="bold")
    if sub:
        txt(cx, cy - 0.22, sub, size=7.0, color=C["gray"])


def arr(x1, y1, x2, y2, color=C["gray"], lw=1.3, head=8):
    ax.annotate(
        "",
        xy=(x2, y2),
        xytext=(x1, y1),
        arrowprops=dict(arrowstyle="->", color=color, lw=lw, mutation_scale=head),
        zorder=4,
    )


box(0, FIG_H - 1.05, FIG_W, 1.05, color="#062147", edge=C["blue"], lw=2.0, radius=0)
txt(
    FIG_W / 2,
    FIG_H - 0.43,
    "EAC Labor Timesheets  —  Azure Cloud Architecture",
    size=17,
    weight="bold",
)
txt(
    FIG_W / 2,
    FIG_H - 0.76,
    "UC-2  Project Coder Weekly Timesheet Pre-Population   |   FastAPI + LangGraph + Azure OpenAI   |   Next.js 14",
    size=9,
    color=C["gray"],
)

# VNet boundary
box(3.3, 0.9, 14.6, 15.7, color=C["vnet"], edge="#2a3f6f", lw=1.5, alpha=0.35, radius=0.4)
txt(10.6, 1.15, "Azure Virtual Network  10.0.0.0/16  —  Private Endpoints for Data Services", size=7.5, color="#4a6fa5")

# Client zone
Z1x, Z1w = 0.2, 2.9
zone(Z1x, 1.0, Z1w, 15.6, face="#081428", edge=C["blue"], title="CLIENT  (Browser / Vercel)")
node(Z1x + Z1w / 2, 15.3, 2.4, 0.72, face="#0d2040", edge=C["blue_light"], title="Employee", sub="Weekly review-and-confirm")
node(Z1x + Z1w / 2, 14.3, 2.4, 0.72, face="#0d2040", edge=C["blue_light"], title="Team Lead", sub="Review Queue resolution")
node(Z1x + Z1w / 2, 13.3, 2.4, 0.78, face="#0f2340", edge=C["blue"], title="Next.js 14 SPA", sub="Vercel CDN  |  TypeScript")
for i, (pg, sub) in enumerate([
    ("Overview", "project-level KPIs"),
    ("Activity Records", "canonical rows + evidence"),
    ("Review Queue", "low-confidence items"),
    ("Employee Review", "all weeks in one view"),
    ("Employee Directory", "employee history"),
    ("Analytics", "spend by project | weekly bars"),
    ("Audit Trail", "trace viewer"),
    ("Data Sources", "upload + validation"),
    ("Feedback Learning", "correction log | calibration"),
]):
    node(Z1x + Z1w / 2, 12.1 - i * 1.18, 2.4, 0.78, face=C["panel"], edge=C["border"], title=pg, sub=sub)

# Azure Front Door
Z2x, Z2w = 3.4, 2.6
zone(Z2x, 10.5, Z2w, 6.1, face="#1a0e05", edge=C["orange"], title="AZURE FRONT DOOR")
node(Z2x + Z2w / 2, 15.7, 2.2, 0.78, face="#2a1a05", edge=C["orange"], title="Azure Front Door", sub="Global CDN  |  DDoS protection")
node(Z2x + Z2w / 2, 14.6, 2.2, 0.78, face=C["panel"], edge=C["orange"], title="WAF Policy", sub="OWASP 3.2  |  rate limiting")
node(Z2x + Z2w / 2, 13.5, 2.2, 0.78, face=C["panel"], edge=C["orange"], title="SSL/TLS Termination", sub="HTTPS enforced")
node(Z2x + Z2w / 2, 12.4, 2.2, 0.78, face=C["panel"], edge=C["orange"], title="CORS Policy", sub="Vercel origin allowed")
node(Z2x + Z2w / 2, 11.3, 2.2, 0.78, face=C["panel"], edge=C["orange"], title="Health Probes", sub="liveness + readiness")

# Container Apps environment
Z3x, Z3w = 6.2, 6.6
zone(Z3x, 1.0, Z3w, 15.6, face="#0a1e10", edge=C["green"], title="AZURE CONTAINER APPS ENVIRONMENT  (VNet integrated | managed identity)")
box(Z3x + 0.15, 10.0, Z3w - 0.3, 6.1, color="#0d2218", edge=C["green_light"], lw=1.0, alpha=0.6, radius=0.2)
txt(Z3x + Z3w / 2, 15.85, "eac-api Container  (HTTP ingress | min 1, max 10 replicas)", size=7.8, weight="bold", color=C["green_light"])
node(Z3x + Z3w / 2, 15.2, 5.9, 0.72, face="#0a2e18", edge=C["green_light"], title="FastAPI Router", sub="records | drafts | audit | connectors")
node(Z3x + 1.6, 14.0, 2.65, 0.72, face=C["panel"], edge=C["orange"], title="Ingestion API", sub="POST /upload/excel|forms")
node(Z3x + 4.6, 14.0, 2.65, 0.72, face=C["panel"], edge=C["orange"], title="Job Status API", sub="GET /jobs/{id}")
node(Z3x + 1.6, 12.85, 2.65, 0.72, face=C["panel"], edge=C["green_light"], title="Records API", sub="GET /records | overrides")
node(Z3x + 4.6, 12.85, 2.65, 0.72, face=C["panel"], edge=C["red"], title="Review Queue API", sub="low-confidence routing")
node(Z3x + Z3w / 2, 11.8, 5.9, 0.72, face="#1a0a10", edge=C["red"], title="Audit Service", sub="append-only event log | agent trace")
node(Z3x + Z3w / 2, 10.75, 5.9, 0.72, face="#1a1805", edge=C["orange"], title="Form Validation Service", sub="field comparisons | match rate")

box(Z3x + 0.15, 6.15, Z3w - 0.3, 3.6, color="#090f1e", edge=C["blue_light"], lw=1.0, alpha=0.65, radius=0.2)
txt(Z3x + Z3w / 2, 9.55, "LangGraph  6-Node Agentic Pipeline", size=7.8, weight="bold", color=C["blue_light"])
for i, (st, sub) in enumerate([
    ("Harvest", "record + HR"),
    ("Context", "activity context"),
    ("Retrieve", "precedents"),
    ("Policy", "GAAP / IAS 16"),
    ("Classify", "deterministic rules"),
    ("Route", "Cap / Op / Review"),
]):
    px = Z3x + 0.62 + i * 1.03
    node(px, 8.7, 0.92, 1.15, face="#0d2040", edge=C["blue_light"], title=st, sub=sub)
    if i < 5:
        arr(px + 0.46, 8.7, px + 0.57, 8.7, color=C["blue_light"], lw=0.9, head=6)

node(Z3x + Z3w / 2, 7.45, 5.9, 0.78, face="#1a0e2a", edge=C["purple"], title="Hybrid Classifier", sub="policy-led decisioning | confidence | evidence")
node(Z3x + Z3w / 2, 6.6, 5.9, 0.72, face=C["panel"], edge=C["purple"], title="Signal Ledger + Confidence Scorer", sub="0-100 confidence | routing threshold")

box(Z3x + 0.15, 1.8, Z3w - 0.3, 3.9, color="#0d2018", edge=C["green_light"], lw=1.0, alpha=0.6, radius=0.2)
txt(Z3x + Z3w / 2, 5.5, "eac-worker Container  (Queue-triggered | Azure Service Bus | scale 0-20)", size=7.8, weight="bold", color=C["green_light"])
node(Z3x + Z3w / 2, 4.85, 5.9, 0.72, face="#0a2e10", edge=C["green_light"], title="Flow Orchestrator", sub="asyncio.gather | chunking | semaphore")
node(Z3x + 1.6, 3.75, 2.65, 0.72, face=C["panel"], edge=C["teal"], title="Excel Connector", sub="pandas | schema validation")
node(Z3x + 4.6, 3.75, 2.65, 0.72, face=C["panel"], edge=C["teal"], title="DOCX Connector", sub="python-docx | regex extract")
node(Z3x + Z3w / 2, 2.65, 5.9, 0.72, face=C["panel"], edge=C["green_light"], title="Run Manifest Producer", sub="processed | classified | escalated | failed")

# Azure AI services
Z4x, Z4w = 13.1, 3.9
zone(Z4x, 7.5, Z4w, 9.1, face="#130d1e", edge=C["purple"], title="AZURE AI SERVICES")
node(Z4x + Z4w / 2, 15.7, 3.4, 0.78, face="#1e0d3a", edge=C["purple"], title="Azure OpenAI Service", sub="LLM enrichment and explanation")
node(Z4x + Z4w / 2, 14.6, 3.4, 0.78, face="#1a0d2e", edge=C["purple"], title="Model: gpt-4.1-mini", sub="API versioned and configurable")
node(Z4x + Z4w / 2, 13.5, 3.4, 0.78, face="#0f1c30", edge=C["blue_light"], title="litellm acompletion", sub="async | per-record")
node(Z4x + Z4w / 2, 12.4, 3.4, 0.78, face="#0d1826", edge=C["blue_light"], title="Single Combined Prompt", sub="signals + policy + evidence")
node(Z4x + Z4w / 2, 11.3, 3.4, 0.78, face="#0d1e26", edge=C["teal"], title="LLM Skip Threshold", sub="high confidence => stub")
node(Z4x + Z4w / 2, 10.2, 3.4, 0.78, face="#0d2e1a", edge=C["green"], title="Stub Fallback", sub="deterministic only when needed")
node(Z4x + Z4w / 2, 9.1, 3.4, 0.78, face="#130d1e", edge=C["purple"], title="Azure AI Search", sub="semantic precedent retrieval (prod)")
node(Z4x + Z4w / 2, 8.2, 3.4, 0.72, face=C["panel"], edge=C["purple"], title="OpenAI Embeddings", sub="future vector indexing")

# Data services
Z5x, Z5w = 13.1, 3.9
zone(Z5x, 1.0, Z5w, 6.0, face="#0a1e1a", edge=C["teal"], title="AZURE DATA SERVICES")
for i, (title, sub, edge) in enumerate([
    ("Azure Database for PostgreSQL", "Flexible Server | pgvector", C["teal"]),
    ("Azure Blob Storage", "file uploads | staging | lifecycle policy", C["teal"]),
    ("Azure Service Bus Premium", "dead-letter | KEDA trigger", C["orange"]),
    ("Azure Cache for Redis", "session cache | progress counters", C["red"]),
    ("Azure Cosmos DB", "append-only audit archive", C["purple"]),
]):
    node(Z5x + Z5w / 2, 6.2 - i * 1.03, 3.4, 0.78, face=C["panel"], edge=edge, title=title, sub=sub)

# Platform services
Z6x, Z6w = 17.3, 4.2
zone(Z6x, 1.0, Z6w, 15.6, face="#0a0d18", edge=C["gray"], title="AZURE PLATFORM SERVICES")
for i, (title, sub, edge) in enumerate([
    ("Azure Container Registry", "private images | vulnerability scan", C["blue"]),
    ("Azure Key Vault", "API keys | DB strings | certs", C["blue"]),
    ("Azure Entra ID (AAD)", "OIDC | employee / lead / finance roles", C["blue_light"]),
    ("Azure API Management", "rate limit | LLM gateway (prod)", C["blue"]),
    ("Azure Monitor", "metrics | alerts | dashboards", C["green"]),
    ("Application Insights", "distributed traces | agent spans", C["green"]),
    ("Log Analytics Workspace", "KQL | retention | central logs", C["green"]),
    ("Azure Policy", "guardrails | compliance", C["orange"]),
    ("Azure Container Apps Jobs", "nightly scheduler | cron trigger", C["green_light"]),
    ("Private DNS Zones", "private endpoint resolution", "#4a6fa5"),
]):
    node(Z6x + Z6w / 2, 15.6 - i * 1.36, 3.7, 0.84, face=C["panel"], edge=edge, title=title, sub=sub)

# Arrows
arr(Z1x + Z1w, 13.25, Z2x, 13.25, color=C["blue_light"], lw=1.6, head=10)
arr(Z2x, 12.95, Z1x + Z1w, 12.95, color=C["green_light"], lw=1.3, head=8)
arr(Z2x + 1.25, 12.86, Z2x + 1.25, 12.29, color=C["orange"], lw=1.2)
arr(Z2x + 3.5, 12.86, Z2x + 3.5, 12.29, color=C["orange"], lw=1.2)
arr(Z3x + Z3w / 2, 11.0, Z4x, 11.0, color=C["purple"], lw=1.4, head=9)
arr(Z3x + Z3w / 2, 3.8, Z5x, 3.8, color=C["orange"], lw=1.4, head=9)
arr(Z3x + Z3w, 4.1, Z6x, 4.1, color=C["gray"], lw=1.1, head=8)
arr(Z4x + Z4w / 2, 8.0, Z5x, 6.0, color=C["teal"], lw=1.2, head=8)
arr(Z5x + Z5w / 2, 3.0, Z6x, 3.0, color=C["blue_light"], lw=1.2, head=8)

fig.savefig(PNG_OUT, dpi=200, facecolor=fig.get_facecolor(), bbox_inches="tight")
fig.savefig(PDF_OUT, dpi=200, facecolor=fig.get_facecolor(), bbox_inches="tight")
print(f"Wrote {PNG_OUT}")
print(f"Wrote {PDF_OUT}")
