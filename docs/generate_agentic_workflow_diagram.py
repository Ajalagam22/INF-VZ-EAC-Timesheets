"""
Generate the EAC Agentic Workflow Diagram (REQ-53).

Outputs:
  docs/EAC_Agentic_Workflow_Diagram.png   — standalone visual PNG
  docs/EAC_Agentic_Workflow_Diagram.pdf   — standalone visual PDF
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

PNG_OUT = OUT_DIR / "EAC_Agentic_Workflow_Diagram.png"
PDF_OUT = OUT_DIR / "EAC_Agentic_Workflow_Diagram.pdf"

C = {
    "bg":           "#0d1117",
    "header":       "#062147",
    "white":        "#e6edf3",
    "gray":         "#8b949e",
    "muted":        "#484f58",
    "blue":         "#388bfd",
    "blue_dark":    "#0d2040",
    "blue_edge":    "#1f6feb",
    "green":        "#2ea043",
    "green_dark":   "#0a1f10",
    "green_edge":   "#238636",
    "orange":       "#d97706",
    "orange_dark":  "#2a1600",
    "orange_edge":  "#b45309",
    "purple":       "#8b5cf6",
    "purple_dark":  "#12082a",
    "purple_edge":  "#7c3aed",
    "zone_src":     "#060d1a",
    "zone_pipe":    "#080d14",
    "zone_out":     "#060d0a",
}

FIG_W, FIG_H = 24, 13
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
fig.patch.set_facecolor(C["bg"])
ax.set_facecolor(C["bg"])
ax.set_xlim(0, FIG_W)
ax.set_ylim(0, FIG_H)
ax.axis("off")


def box(x, y, w, h, color, edge=None, lw=1.2, radius=0.22, alpha=1.0):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        linewidth=lw, edgecolor=edge or color,
        facecolor=color, alpha=alpha, zorder=2,
    ))


def txt(x, y, t, size=8.5, color=None, weight="normal", ha="center", va="center", z=5):
    ax.text(x, y, t, fontsize=size, color=color or C["white"],
            fontweight=weight, ha=ha, va=va, zorder=z,
            fontfamily="sans-serif", clip_on=False)


def arr(x1, y1, x2, y2, color=None, lw=1.4, head=10, ls="-"):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->", color=color or C["gray"],
                                lw=lw, mutation_scale=head, linestyle=ls), zorder=4)


def badge(x, y, w, h, face, label, text_color="#fff"):
    box(x, y, w, h, color=face, edge=face, lw=0, radius=0.08)
    txt(x + w / 2, y + h / 2, label, size=6.5, color=text_color, weight="bold")


# ── Header ───────────────────────────────────────────────────────────────────
box(0, FIG_H - 1.15, FIG_W, 1.15, color=C["header"], edge=C["blue"], lw=2.0, radius=0)
txt(FIG_W / 2, FIG_H - 0.46, "EAC Labor Timesheets  —  Agentic Workflow Diagram", size=19, weight="bold")
txt(FIG_W / 2, FIG_H - 0.85,
    "UC-2  ·  AI-Enabled CapEx / OpEx Activity Classification  ·  7 Pipeline Stages  ·  3 Output Channels  ·  REQ-53",
    size=9, color=C["gray"])

# ── Footer ───────────────────────────────────────────────────────────────────
box(0, 0, FIG_W, 0.40, color=C["header"], edge=C["blue"], lw=0, radius=0)
txt(FIG_W / 2, 0.20,
    "EAC Labor Timesheets  ·  Standalone Agentic Workflow Deliverable  ·  May 2026  ·  InfoVision",
    size=7.5, color=C["gray"])

# ── Zone layout ───────────────────────────────────────────────────────────────
ZY, ZH = 0.50, FIG_H - 1.15 - 0.50 - 0.10   # zone bottom-y and height

SRC_X, SRC_W   = 0.25,  4.6
PIPE_X, PIPE_W = 5.30,  13.0
OUT_X,  OUT_W  = 18.65,  5.0

ZONE_TITLE_H = 0.65

for zx, zw, zface, zedge, ztitle in [
    (SRC_X,  SRC_W,  C["zone_src"],  C["blue_edge"],   "① DATA SOURCES"),
    (PIPE_X, PIPE_W, C["zone_pipe"], C["blue"],         "EAC AGENTIC PIPELINE  ·  7 Specialist Agents"),
    (OUT_X,  OUT_W,  C["zone_out"],  C["green_edge"],   "OUTPUT CHANNELS"),
]:
    box(zx, ZY, zw, ZH, color=zface, edge=zedge, lw=1.3, alpha=0.60, radius=0.4)
    box(zx, ZY + ZH - ZONE_TITLE_H, zw, ZONE_TITLE_H,
        color=zedge, edge=zedge, lw=0, alpha=0.88, radius=0.3)
    txt(zx + zw / 2, ZY + ZH - ZONE_TITLE_H / 2, ztitle, size=9.2, weight="bold")


# ── Source boxes ──────────────────────────────────────────────────────────────
SCX = SRC_X + SRC_W / 2
SBW, SBH = SRC_W - 0.50, 1.30
SOURCES = [
    (8.60, C["blue_dark"],  C["blue_edge"],   "Excel Dataset Connector",  "Structured activity records",       "per employee · per week",  "ACTIVE"),
    (6.70, C["blue_dark"],  C["blue_edge"],   "DOCX Form Parser",         "Raw timesheet documents",           "& semi-structured forms",  "ACTIVE"),
    (4.55, "#131720",       C["muted"],       "Coming Soon",              "BigQuery · HR Systems",             "Project Registries · Git · Jira", ""),
]

for cy, face, edge, title, sub1, sub2, bdg in SOURCES:
    bx, by = SCX - SBW / 2, cy - SBH / 2
    box(bx, by, SBW, SBH, color=face, edge=edge, lw=1.6, radius=0.22)
    if bdg:
        badge(bx + SBW - 0.96, by + SBH - 0.33, 0.88, 0.24, C["green"], bdg)
    else:
        badge(bx + SBW - 1.20, by + SBH - 0.33, 1.12, 0.24, "#222", "COMING SOON", "#666")
    txt(SCX, cy + 0.28, title, size=9.0, weight="bold")
    txt(SCX, cy + 0.00, sub1, size=7.5, color=C["gray"])
    txt(SCX, cy - 0.26, sub2, size=7.0, color=C["muted"])


# ── Agent boxes ───────────────────────────────────────────────────────────────
PCX = PIPE_X + PIPE_W / 2
PBW, PBH = PIPE_W - 0.55, 1.15

AGENTS = [
    # cy,  face,             edge,           num, title,                         sub1,                                         sub2
    (9.05, C["blue_dark"],   C["blue_edge"], "②", "DATA HARVESTING AGENT",       "Ingestion · Schema validation · Staging",    "Excel Connector + DOCX Parser active   ·   Malformed records → quarantine"),
    (7.60, "#101828",        "#4493f8",      "③", "CONTEXT BUILDING AGENT",      "Per-employee 7-day activity digest · Rolling weekly window construction",  "Employee profile · Project registry metadata · Activity-type context"),
    (6.15, "#160f28",        C["purple"],    "④", "CLASSIFICATION AGENT",        "CapEx / OpEx / Review decision   ·   Confidence score 0–100",              "Evidence trail generated   ·   Signal ledger attached to each record"),
    (4.70, C["green_dark"],  C["green"],     "⑤", "POLICY & RULES AGENT",        "Accounting rule overlay   ·   Project code constraint enforcement",        "Persona configuration   ·   Rule version stamped on every record"),
    (3.25, C["orange_dark"], C["orange"],    "⑥", "CONFIDENCE & ROUTING AGENT",  "High-confidence → Employee Review Queue",    "Low-confidence → Team Lead Escalation Queue   ·   Threshold: configurable per persona"),
    (1.75, C["purple_dark"], C["purple"],    "⑦", "RECONCILIATION & REPORTING AGENT", "Post-classification aggregation · Roll up to cost centre · Count completions", "Compute CapEx / OpEx deltas vs 100% OpEx baseline   ·   Finance-facing report"),
]

for cy, face, edge, num, title, sub1, sub2 in AGENTS:
    bx, by = PCX - PBW / 2, cy - PBH / 2
    box(bx, by, PBW, PBH, color=face, edge=edge, lw=1.8, radius=0.22)
    badge(bx + 0.14, by + PBH - 0.36, 0.38, 0.28, edge, num)
    txt(PCX, cy + 0.27, title, size=10.0, weight="bold")
    txt(PCX, cy + 0.00, sub1, size=8.0, color=C["gray"])
    txt(PCX, cy - 0.27, sub2, size=7.2, color=C["muted"])


# ── Output boxes ─────────────────────────────────────────────────────────────
OCX = OUT_X + OUT_W / 2
OBW, OBH = OUT_W - 0.45, 1.55

OUTPUTS = [
    # cy,  face,             edge,           label, title,                      sub1,                               sub2,                                   audience
    (7.80, C["blue_dark"],   C["blue_edge"], "(a)", "EMPLOYEE\nTIMESHEET DRAFT",  "Pre-populated weekly draft",        "High-confidence classified records",  "Individual employees"),
    (5.10, C["orange_dark"], C["orange"],    "(b)", "TEAM LEAD\nESCALATION VIEW", "Low-confidence & ambiguous records", "Requires team lead resolution",       "Team leads / managers"),
    (2.40, C["green_dark"],  C["green"],     "(c)", "FINANCE / TAX\nREPORT",      "Cost-centre roll-up · Completions", "CapEx/OpEx deltas vs 100% OpEx",      "Finance · Tax · Accounting"),
]

for cy, face, edge, lbl, title, sub1, sub2, audience in OUTPUTS:
    bx, by = OCX - OBW / 2, cy - OBH / 2
    box(bx, by, OBW, OBH, color=face, edge=edge, lw=1.8, radius=0.22)
    txt(OCX, cy + 0.50, lbl, size=8.5, color=edge, weight="bold")
    txt(OCX, cy + 0.18, title, size=8.8, weight="bold", color=C["white"])
    txt(OCX, cy - 0.13, sub1, size=7.2, color=C["gray"])
    txt(OCX, cy - 0.36, sub2, size=7.0, color=C["muted"])
    box(bx + 0.12, by + 0.07, OBW - 0.24, 0.28,
        color=edge, edge=edge, lw=0, radius=0.1, alpha=0.22)
    txt(OCX, by + 0.21, f"Audience: {audience}", size=7, color=edge, weight="bold")


# ── Arrows ────────────────────────────────────────────────────────────────────
PIPE_LEFT  = PCX - PBW / 2
PIPE_RIGHT = PCX + PBW / 2
OUT_LEFT   = OCX - OBW / 2
SRC_RIGHT  = SCX + SBW / 2
A5_CY = 3.25   # Routing
A6_CY = 1.75   # Reconciliation

# Sources → Harvesting Agent (left edge of pipeline)
A1_CY = 9.05
arr(SRC_RIGHT, 8.60,  PIPE_LEFT, A1_CY - 0.15, color=C["blue"],  lw=1.6)
arr(SRC_RIGHT, 6.70,  PIPE_LEFT, A1_CY,         color=C["blue"],  lw=1.6)
arr(SRC_RIGHT, 4.55,  PIPE_LEFT, A1_CY + 0.18,  color=C["muted"], lw=1.2, ls="--")
txt((SRC_RIGHT + PIPE_LEFT) / 2, (4.55 + A1_CY + 0.18) / 2 + 0.22, "future", size=7, color=C["muted"])

# Agent → Agent vertical arrows (centre of pipeline zone)
for i in range(len(AGENTS) - 1):
    top_cy = AGENTS[i][0]
    bot_cy = AGENTS[i + 1][0]
    arr(PCX, top_cy - PBH / 2, PCX, bot_cy + PBH / 2, color=C["muted"], lw=1.6, head=9)

# Routing (A5) → Employee Draft (O1) — "approved"
arr(PIPE_RIGHT, A5_CY + 0.35, OUT_LEFT, 7.80, color=C["blue"], lw=1.6, head=11)
txt((PIPE_RIGHT + OUT_LEFT) / 2 + 0.3, (A5_CY + 0.35 + 7.80) / 2 + 0.22,
    "approved  ↑", size=8, color=C["blue"], weight="bold")

# Routing (A5) → Team Lead (O2) — "review"
arr(PIPE_RIGHT, A5_CY - 0.20, OUT_LEFT, 5.10, color=C["orange"], lw=1.6, head=11)
txt((PIPE_RIGHT + OUT_LEFT) / 2 + 0.1, (A5_CY - 0.20 + 5.10) / 2 + 0.22,
    "review  ↓", size=8, color=C["orange"], weight="bold")

# Reconciliation (A6) → Finance Report (O3)
arr(PIPE_RIGHT, A6_CY, OUT_LEFT, 2.40, color=C["purple"], lw=1.6, head=11)
txt((PIPE_RIGHT + OUT_LEFT) / 2, (A6_CY + 2.40) / 2 + 0.2,
    "reconciliation\nreport", size=7.5, color=C["purple"])


# ── Save ──────────────────────────────────────────────────────────────────────
plt.tight_layout(pad=0)
for out_path, fmt in [(PNG_OUT, "png"), (PDF_OUT, "pdf")]:
    fig.savefig(str(out_path), format=fmt, dpi=150 if fmt == "png" else None,
                bbox_inches="tight", facecolor=C["bg"])
    print(f"{fmt.upper()} written: {out_path} ({out_path.stat().st_size // 1024} KB)")
plt.close()
