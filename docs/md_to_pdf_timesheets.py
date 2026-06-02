"""
Generate a polished architecture PDF for EAC Labor Timesheets.

Output:
  docs/EAC_Timesheets_Architecture_Document.pdf

This script expects the Timesheets Azure diagram to exist at:
  docs/EAC_Timesheets_Azure_Architecture.png
"""
from __future__ import annotations

import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import LETTER, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    Image,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

DIR = Path(__file__).parent
INPUT = DIR / "architecture_document.md"
DIAG = DIR / "EAC_Timesheets_Azure_Architecture.png"
WORKFLOW_DIAG = DIR / "EAC_Agentic_Workflow_Diagram.png"
OUTPUT = DIR / "EAC_Timesheets_Architecture_Document.pdf"

PORT = LETTER
LAND = landscape(LETTER)

AZURE = colors.HexColor("#0078d4")
AZURE_L = colors.HexColor("#388bfd")
NAVY = colors.HexColor("#0d1b2e")
DARK = colors.HexColor("#1a2a3a")
BODY_C = colors.HexColor("#1a1a1a")
GRAY = colors.HexColor("#6b7280")
LGRAY = colors.HexColor("#f3f4f6")
WHITE = colors.white
F_REG = "Helvetica"
F_BOLD = "Helvetica-Bold"
F_MONO = "Courier"


def _cover_page(canvas, doc):
    w, h = PORT
    canvas.saveState()
    canvas.setFillColor(colors.white)
    canvas.rect(0, 0, w, h, fill=1, stroke=0)
    canvas.setFillColor(AZURE)
    canvas.rect(0, h - 1.9 * inch, w, 1.9 * inch, fill=1, stroke=0)
    canvas.setFont(F_BOLD, 22)
    canvas.setFillColor(colors.white)
    canvas.drawString(0.75 * inch, h - 0.95 * inch, "EAC Labor Timesheets")
    canvas.drawString(0.75 * inch, h - 1.30 * inch, "Architecture Document")
    canvas.setFont(F_REG, 12)
    canvas.setFillColor(colors.HexColor("#bfdbfe"))
    canvas.drawString(0.75 * inch, h - 1.62 * inch, "Azure Cloud Architecture & Design Document")
    canvas.setStrokeColor(AZURE)
    canvas.setLineWidth(0.5)
    canvas.line(0.75 * inch, h - 2.1 * inch, w - 0.75 * inch, h - 2.1 * inch)
    canvas.setFillColor(AZURE)
    canvas.rect(0, 0, w, 0.4 * inch, fill=1, stroke=0)
    canvas.setFont(F_REG, 8)
    canvas.setFillColor(colors.white)
    canvas.drawString(0.75 * inch, 0.14 * inch, "UC-2  Project Coder Weekly Timesheet Pre-Population  |  Confidential")
    canvas.drawRightString(w - 0.75 * inch, 0.14 * inch, "May 25, 2026")
    canvas.restoreState()


def _diag_page(canvas, doc):
    w, h = LAND
    canvas.saveState()
    canvas.setFillColor(colors.HexColor("#0d1117"))
    canvas.rect(0, 0, w, h, fill=1, stroke=0)
    canvas.setFont(F_REG, 7)
    canvas.setFillColor(colors.HexColor("#8b949e"))
    canvas.drawString(0.4 * inch, 0.22 * inch, "EAC Labor Timesheets, Azure Cloud Architecture")
    canvas.drawRightString(w - 0.4 * inch, 0.22 * inch, f"Page {doc.page}")
    canvas.restoreState()


def _text_page(canvas, doc):
    w, h = PORT
    canvas.saveState()
    canvas.setStrokeColor(AZURE)
    canvas.setLineWidth(1.2)
    canvas.line(0.75 * inch, h - 0.55 * inch, w - 0.75 * inch, h - 0.55 * inch)
    canvas.setFont(F_REG, 7.5)
    canvas.setFillColor(GRAY)
    canvas.drawString(0.75 * inch, h - 0.46 * inch, "EAC Labor Timesheets, Azure Cloud Architecture")
    canvas.drawRightString(w - 0.75 * inch, h - 0.46 * inch, "Architecture & Design Document")
    canvas.setLineWidth(0.4)
    canvas.setStrokeColor(colors.HexColor("#dddddd"))
    canvas.line(0.75 * inch, 0.55 * inch, w - 0.75 * inch, 0.55 * inch)
    canvas.setFont(F_REG, 7.5)
    canvas.setFillColor(GRAY)
    canvas.drawString(0.75 * inch, 0.37 * inch, "UC-2 · Project Coder Weekly Timesheet Pre-Population")
    canvas.drawRightString(w - 0.75 * inch, 0.37 * inch, f"Page {doc.page}")
    canvas.restoreState()


def _styles():
    ss = getSampleStyleSheet()
    add = ss.add
    add(ParagraphStyle("CoverTitle", fontName=F_BOLD, fontSize=28, leading=34, textColor=WHITE, alignment=TA_LEFT, spaceAfter=10))
    add(ParagraphStyle("CoverSub", fontName=F_REG, fontSize=13, leading=18, textColor=colors.HexColor("#93c5fd"), alignment=TA_LEFT, spaceAfter=6))
    add(ParagraphStyle("CoverMeta", fontName=F_REG, fontSize=10, leading=14, textColor=colors.HexColor("#9ca3af"), alignment=TA_LEFT, spaceAfter=4))
    add(ParagraphStyle("CoverLabel", fontName=F_BOLD, fontSize=8.5, leading=12, textColor=AZURE_L, alignment=TA_LEFT, spaceAfter=2))
    add(ParagraphStyle("DocH1", fontName=F_BOLD, fontSize=17, leading=22, textColor=AZURE, spaceBefore=22, spaceAfter=8, borderPad=0))
    add(ParagraphStyle("DocH2", fontName=F_BOLD, fontSize=13, leading=17, textColor=DARK, spaceBefore=14, spaceAfter=5))
    add(ParagraphStyle("DocH3", fontName=F_BOLD, fontSize=11, leading=15, textColor=DARK, spaceBefore=10, spaceAfter=3))
    add(ParagraphStyle("DocH4", fontName=F_BOLD, fontSize=10, leading=14, textColor=NAVY, spaceBefore=8, spaceAfter=2))
    add(ParagraphStyle("DocBody", fontName=F_REG, fontSize=10, leading=15.5, textColor=BODY_C, alignment=TA_JUSTIFY, spaceAfter=6))
    add(ParagraphStyle("DocBullet", fontName=F_REG, fontSize=10, leading=14, textColor=BODY_C, leftIndent=20, spaceAfter=3))
    add(ParagraphStyle("DocCode", fontName=F_MONO, fontSize=8.2, leading=12, textColor=colors.HexColor("#1f2937"), backColor=LGRAY, leftIndent=14, rightIndent=14, spaceAfter=6, spaceBefore=4))
    add(ParagraphStyle("DocMeta", fontName=F_REG, fontSize=10, leading=14, textColor=GRAY, alignment=TA_CENTER, spaceAfter=3))
    add(ParagraphStyle("FigCaption", fontName=F_REG, fontSize=8, leading=11, textColor=GRAY, alignment=TA_CENTER, spaceAfter=10, spaceBefore=4))
    return ss


def _esc(t: str) -> str:
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _inline(t: str) -> str:
    t = _esc(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"\*(.+?)\*", r"<i>\1</i>", t)
    t = re.sub(r"`(.+?)`", r'<font name="Courier">\1</font>', t)
    return t


def _cover_story(styles):
    s = []
    s.append(Spacer(1, 1.85 * inch))
    meta_style = ParagraphStyle("CMeta", fontName=F_REG, fontSize=10, textColor=BODY_C, leading=16, spaceAfter=3)
    label_style = ParagraphStyle("CLabel", fontName=F_BOLD, fontSize=8, textColor=AZURE, leading=12, spaceAfter=1, spaceBefore=5)
    meta_fields = [
        ("SUBMISSION", "UC-2  Project Coder Weekly Timesheet Pre-Population"),
        ("AUTHOR", "Ajith Jalagam"),
        ("DATE", "May 25, 2026"),
        ("VERSION", "1.0, Azure Architecture"),
        ("STACK", "FastAPI  ·  LangGraph  ·  Azure Container Apps  ·  Azure OpenAI  ·  Next.js 14"),
    ]
    for lbl, val in meta_fields:
        s.append(Paragraph(lbl, label_style))
        s.append(Paragraph(val, meta_style))
    s.append(Spacer(1, 0.35 * inch))
    s.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#e5e7eb"), spaceAfter=14))
    s.append(Paragraph("CONTENTS", ParagraphStyle("TOCHead", fontName=F_BOLD, fontSize=8, textColor=AZURE, leading=12, spaceAfter=8)))
    toc_items = [
        ("1", "Problem Statement Analysis"),
        ("2", "Azure Architecture Strategy"),
        ("3", "System Architecture Overview"),
        ("4", "Connector Framework"),
        ("5", "Data Model and Canonical Schema"),
        ("6", "Agent Pipeline and Classification"),
        ("7", "Employee Review and Audit Flow"),
        ("8", "Security and Governance"),
        ("9", "Production Deployment Path"),
        ("10", "Observability and Reliability"),
        ("11", "Known Production Gaps"),
    ]
    toc_num = ParagraphStyle("TOCNum", fontName=F_BOLD, fontSize=9, textColor=AZURE, leading=14)
    toc_text = ParagraphStyle("TOCText", fontName=F_REG, fontSize=9, textColor=colors.HexColor("#374151"), leading=14)
    toc_rows = [[Paragraph(n, toc_num), Paragraph(t, toc_text)] for n, t in toc_items]
    tbl = Table(toc_rows, colWidths=[0.3 * inch, 5.9 * inch], spaceBefore=0)
    tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        *[("ROWBACKGROUNDS", (0, i), (1, i), [colors.HexColor("#f9fafb")]) for i in range(0, len(toc_rows), 2)],
    ]))
    s.append(tbl)
    return s


def _diag_story(styles):
    s = []
    if not DIAG.exists():
        s.append(Paragraph("[Azure diagram not found]", styles["DocBody"]))
        return s
    dw = 10.0 * inch
    dh = dw * (18 / 28)
    s.append(Image(str(DIAG), width=dw, height=dh))
    s.append(Spacer(1, 0.08 * inch))
    s.append(Paragraph(
        "Figure 1 — EAC Labor Timesheets Azure architecture: Azure Front Door, Azure Container Apps, LangGraph pipeline, Azure OpenAI, PostgreSQL, Blob Storage, Service Bus, Key Vault, Entra ID, and monitoring services.",
        styles["FigCaption"],
    ))
    return s


def _workflow_diag_story(styles):
    s = []
    if not WORKFLOW_DIAG.exists():
        s.append(Paragraph("[Agentic workflow diagram not found — run generate_agentic_workflow_diagram.py]", styles["DocBody"]))
        return s
    dw = LAND[0] - 0.8 * inch
    dh = dw * (13 / 24)
    s.append(Image(str(WORKFLOW_DIAG), width=dw, height=dh))
    s.append(Spacer(1, 0.08 * inch))
    s.append(Paragraph(
        "Figure 2 — EAC Agentic Workflow Diagram (REQ-53): 7 pipeline stages from Data Sources through Reconciliation & Reporting Agent, with 3 output channels. Self-explanatory standalone deliverable.",
        styles["FigCaption"],
    ))
    return s


def _parse_md(md: str, styles):
    story = []
    lines = md.splitlines()
    i = 0
    in_code = False
    code_buf = []
    in_table = False
    table_rows = []
    title_done = False

    def flush_code():
        nonlocal code_buf
        if code_buf:
            story.append(Paragraph("<br/>".join(_esc(l) for l in code_buf), styles["DocCode"]))
            story.append(Spacer(1, 4))
            code_buf.clear()

    def flush_table():
        nonlocal table_rows, in_table
        if not table_rows:
            in_table = False
            return
        ncols = max(len(r) for r in table_rows)
        rows = [r + [""] * (ncols - len(r)) for r in table_rows]
        pw = PORT[0] - 1.7 * inch
        cw = pw / ncols
        tbl = Table(rows, colWidths=[cw] * ncols, repeatRows=1)
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), AZURE),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), F_BOLD),
            ("FONTSIZE", (0, 0), (-1, -1), 8.2),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LGRAY]),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#d1d5db")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(tbl)
        story.append(Spacer(1, 8))
        table_rows.clear()
        in_table = False

    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("```"):
            in_code = not in_code
            if not in_code:
                flush_code()
            i += 1
            continue
        if in_code:
            code_buf.append(line)
            i += 1
            continue
        if line.strip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if all(re.match(r"^-+$", c.replace(":", "")) for c in cells if c):
                i += 1
                continue
            in_table = True
            table_rows.append([Paragraph(_inline(c), styles["DocBody"]) for c in cells])
            i += 1
            continue
        elif in_table:
            flush_table()
        stripped = line.strip()
        if not stripped:
            story.append(Spacer(1, 4))
            i += 1
            continue
        if re.match(r"^-{3,}$", stripped):
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#d1d5db"), spaceAfter=8))
            i += 1
            continue
        hm = re.match(r"^(#{1,4})\s+(.*)", stripped)
        if hm:
            lvl = len(hm.group(1))
            text = _inline(hm.group(2))
            if lvl == 1 and not title_done:
                title_done = True
            elif lvl == 1:
                story.append(Paragraph(text, styles["DocH1"]))
            elif lvl == 2:
                story.append(Paragraph(text, styles["DocH2"]))
            elif lvl == 3:
                story.append(Paragraph(text, styles["DocH3"]))
            else:
                story.append(Paragraph(f"<b>{text}</b>", styles["DocBody"]))
            i += 1
            continue
        if stripped.startswith("**") and "**" in stripped[2:]:
            story.append(Paragraph(_inline(stripped), styles["DocMeta"]))
            i += 1
            continue
        bm = re.match(r"^(\s*)([-*+]|\d+\.)\s+(.*)", line)
        if bm:
            indent = len(bm.group(1))
            text = _inline(bm.group(3))
            extra = (indent // 2) * 14
            story.append(Paragraph(f"<bullet>&bull;</bullet>{text}", ParagraphStyle("_Bul", parent=styles["DocBullet"], leftIndent=20 + extra, bulletIndent=8 + extra)))
            i += 1
            continue
        story.append(Paragraph(_inline(stripped), styles["DocBody"]))
        i += 1

    if in_code:
        flush_code()
    if in_table:
        flush_table()
    return story


def _upgrade_h1s(story, styles):
    out = []
    for item in story:
        if getattr(item, "style", None) and item.style.name == "DocH1":
            raw = re.sub(r"<[^>]+>", "", item.text)
            box_row = Table([[Paragraph(f"<b>{_inline(raw)}</b>", ParagraphStyle("H1Box", parent=styles["DocH1"], textColor=WHITE, spaceBefore=0, spaceAfter=0))]], colWidths=[PORT[0] - 1.7 * inch])
            box_row.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), AZURE),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("ROUNDEDCORNERS", [4, 4, 4, 4]),
            ]))
            out.append(Spacer(1, 14))
            out.append(box_row)
            out.append(Spacer(1, 6))
        else:
            out.append(item)
    return out


def main():
    styles = _styles()
    cover_frame = Frame(0.75 * inch, 0.75 * inch, PORT[0] - 1.5 * inch, PORT[1] - 1.5 * inch, id="cover")
    cover_tmpl = PageTemplate(id="Cover", frames=[cover_frame], pagesize=PORT, onPage=_cover_page)
    diag_frame = Frame(0.35 * inch, 0.35 * inch, LAND[0] - 0.7 * inch, LAND[1] - 0.7 * inch, id="diag")
    diag_tmpl = PageTemplate(id="Diagram", frames=[diag_frame], pagesize=LAND, onPage=_diag_page)
    text_frame = Frame(0.75 * inch, 0.70 * inch, PORT[0] - 1.5 * inch, PORT[1] - 1.55 * inch, id="text")
    text_tmpl = PageTemplate(id="Text", frames=[text_frame], pagesize=PORT, onPage=_text_page)
    doc = BaseDocTemplate(
        str(OUTPUT),
        pageTemplates=[cover_tmpl, diag_tmpl, text_tmpl],
        title="EAC Labor Timesheets — Azure Architecture & Design Document",
        author="Ajith Jalagam",
        subject="UC-2 Project Coder Weekly Timesheet Pre-Population",
    )

    story = []
    story += _cover_story(styles)
    story.append(NextPageTemplate("Diagram"))
    story.append(PageBreak())
    story += _diag_story(styles)
    story.append(NextPageTemplate("Diagram"))
    story.append(PageBreak())
    story += _workflow_diag_story(styles)
    story.append(NextPageTemplate("Text"))
    story.append(PageBreak())
    md = INPUT.read_text(encoding="utf-8")
    md_story = _upgrade_h1s(_parse_md(md, styles), styles)
    story += md_story
    doc.build(story)
    print(f"PDF written to: {OUTPUT} ({OUTPUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
