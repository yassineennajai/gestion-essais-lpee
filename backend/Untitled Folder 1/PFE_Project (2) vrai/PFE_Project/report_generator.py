"""
report_generator.py
───────────────────
Generates a PDF sales report on demand.

When the user asks for a "report" or "summary document", the orchestrator
calls generate_report() which:
  1. Runs 5 key analyses on the dataset
  2. Saves 3 charts
  3. Builds a clean PDF using ReportLab
  4. Returns the PDF URL path

Dependencies: pip install reportlab
"""
import os
import uuid
from datetime import datetime

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image,
    Table, TableStyle, HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from config import CHART_DIR, REPORTS_DIR, PALETTE
from analytics import df, NUMERIC_COLS, CATEGORICAL_COLS, date_col, best_num_col, best_cat_col


# ── Internal chart helpers ────────────────────────────────────
def _style_ax(ax, title, xlabel="", ylabel=""):
    ax.figure.patch.set_facecolor("#0f1117")
    ax.set_facecolor("#1a1d27")
    ax.set_title(title, color="#e8eaf0", fontsize=12, pad=10, fontweight="bold")
    ax.set_xlabel(xlabel, color="#9ca3af", fontsize=9)
    ax.set_ylabel(ylabel, color="#9ca3af", fontsize=9)
    ax.tick_params(colors="#9ca3af", labelsize=8)
    for spine in ax.spines.values():
        spine.set_edgecolor("#2d3047")
    ax.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda x, _: f"{x:,.0f}" if abs(x) >= 1 else f"{x:.2f}")
    )
    ax.grid(axis="y", color="#2d3047", linewidth=0.5, linestyle="--", alpha=0.6)

def _save_chart(fig) -> str:
    fname = f"rpt_{uuid.uuid4().hex[:8]}.png"
    fpath = os.path.join(CHART_DIR, fname)
    plt.savefig(fpath, dpi=120, bbox_inches="tight", facecolor="#0f1117")
    plt.close("all")
    return fpath


# ── Generate all report charts ────────────────────────────────
def _make_charts(col: str, cat_col: str) -> dict:
    charts = {}

    # Chart 1 — Top 10 bar chart
    top = df.groupby(cat_col)[col].sum().sort_values(ascending=False).head(10)
    fig, ax = plt.subplots(figsize=(8, 3.5))
    ax.bar(range(len(top)), top.values,
           color=[PALETTE[i % len(PALETTE)] for i in range(len(top))],
           edgecolor="#0f1117", linewidth=0.5)
    ax.set_xticks(range(len(top)))
    ax.set_xticklabels(top.index, rotation=35, ha="right")
    _style_ax(ax, f"Top 10 {cat_col.replace('_',' ').title()} by {col.replace('_',' ').title()}", cat_col, col)
    fig.tight_layout()
    charts["top10"] = _save_chart(fig)

    # Chart 2 — Trend over time (only if date column exists)
    if date_col:
        trend = df.set_index(date_col)[col].resample("ME").sum().dropna()
        if not trend.empty:
            fig, ax = plt.subplots(figsize=(8, 3))
            ax.fill_between(trend.index, trend.values, alpha=0.15, color=PALETTE[0])
            ax.plot(trend.index, trend.values, color=PALETTE[0],
                    linewidth=2, marker="o", markersize=3, markerfacecolor=PALETTE[2])
            _style_ax(ax, f"Monthly {col.replace('_',' ').title()} Trend", "Date", col)
            fig.tight_layout()
            charts["trend"] = _save_chart(fig)

    # Chart 3 — Pie share
    pie_data = df.groupby(cat_col)[col].sum().sort_values(ascending=False).head(6)
    fig, ax = plt.subplots(figsize=(5, 5))
    _, texts, autotexts = ax.pie(
        pie_data.values, labels=pie_data.index,
        autopct="%1.1f%%", colors=PALETTE[:len(pie_data)],
        startangle=140, pctdistance=0.8
    )
    for t in texts:     t.set_color("#9ca3af"); t.set_fontsize(9)
    for t in autotexts: t.set_color("#0f1117"); t.set_fontsize(8); t.set_fontweight("bold")
    ax.set_title(f"{col.replace('_',' ').title()} Share by {cat_col.replace('_',' ').title()}",
                 color="#e8eaf0", fontsize=12, pad=12)
    fig.patch.set_facecolor("#0f1117")
    fig.tight_layout()
    charts["pie"] = _save_chart(fig)

    return charts


# ── Build KPI summary ─────────────────────────────────────────
def _kpi_summary(col: str, cat_col: str) -> dict:
    top = df.groupby(cat_col)[col].sum().sort_values(ascending=False)
    return {
        "total":      df[col].sum(),
        "average":    df[col].mean(),
        "count":      len(df),
        "top_item":   top.index[0] if not top.empty else "N/A",
        "top_value":  top.iloc[0]  if not top.empty else 0,
        "num_cats":   df[cat_col].nunique(),
    }


# ── PDF builder ───────────────────────────────────────────────
def _build_pdf(charts: dict, kpis: dict, col: str, cat_col: str) -> str:
    fname  = f"report_{uuid.uuid4().hex[:8]}.pdf"
    fpath  = os.path.join(REPORTS_DIR, fname)
    doc    = SimpleDocTemplate(fpath, pagesize=A4,
                               leftMargin=2*cm, rightMargin=2*cm,
                               topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story  = []

    # ── Styles ────────────────────────────────────────────────
    title_style = ParagraphStyle(
        "Title", parent=styles["Title"],
        fontSize=22, textColor=colors.HexColor("#1F3864"),
        spaceAfter=6, alignment=TA_CENTER
    )
    sub_style = ParagraphStyle(
        "Sub", parent=styles["Normal"],
        fontSize=10, textColor=colors.HexColor("#6b7591"),
        alignment=TA_CENTER, spaceAfter=16
    )
    h2_style = ParagraphStyle(
        "H2", parent=styles["Heading2"],
        fontSize=14, textColor=colors.HexColor("#2E75B6"),
        spaceBefore=16, spaceAfter=8
    )
    body_style = ParagraphStyle(
        "Body", parent=styles["Normal"],
        fontSize=10, leading=16,
        textColor=colors.HexColor("#333333"), spaceAfter=8
    )

    # ── Cover ─────────────────────────────────────────────────
    story.append(Spacer(1, 1.5*cm))
    story.append(Paragraph("📊 Sales Intelligence Report", title_style))
    story.append(Paragraph(
        f"Generated on {datetime.now().strftime('%B %d, %Y at %H:%M')} · NexusAI Agent",
        sub_style
    ))
    story.append(HRFlowable(width="100%", thickness=2,
                             color=colors.HexColor("#2E75B6"), spaceAfter=20))

    # ── KPI Cards ─────────────────────────────────────────────
    story.append(Paragraph("Key Performance Indicators", h2_style))

    kpi_data = [
        ["Metric", "Value"],
        ["Total " + col.replace("_", " ").title(), f"{kpis['total']:,.2f}"],
        ["Average per Record",                       f"{kpis['average']:,.2f}"],
        ["Total Records",                            f"{kpis['count']:,}"],
        [f"Top {cat_col.replace('_',' ').title()}",  str(kpis['top_item'])],
        [f"Top {cat_col.replace('_',' ').title()} Value", f"{kpis['top_value']:,.2f}"],
        [f"Unique {cat_col.replace('_',' ').title()}s", str(kpis['num_cats'])],
    ]
    kpi_table = Table(kpi_data, colWidths=[9*cm, 8*cm])
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), colors.HexColor("#1F3864")),
        ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, 0), 11),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.HexColor("#EAF2FB"), colors.white]),
        ("FONTSIZE",    (0, 1), (-1, -1), 10),
        ("GRID",        (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("LEFTPADDING",  (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING",   (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 7),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 0.5*cm))

    # ── Top 10 Chart ──────────────────────────────────────────
    story.append(Paragraph(
        f"Top 10 {cat_col.replace('_',' ').title()} by {col.replace('_',' ').title()}",
        h2_style
    ))
    story.append(Image(charts["top10"], width=16*cm, height=7*cm))
    story.append(Spacer(1, 0.4*cm))

    # ── Trend Chart ───────────────────────────────────────────
    if "trend" in charts:
        story.append(Paragraph(f"Monthly {col.replace('_',' ').title()} Trend", h2_style))
        story.append(Image(charts["trend"], width=16*cm, height=6*cm))
        story.append(Spacer(1, 0.4*cm))

    story.append(PageBreak())

    # ── Pie Chart ─────────────────────────────────────────────
    story.append(Paragraph(f"{col.replace('_',' ').title()} Distribution", h2_style))
    story.append(Image(charts["pie"], width=10*cm, height=10*cm))
    story.append(Spacer(1, 0.5*cm))

    # ── Top 10 Data Table ─────────────────────────────────────
    story.append(Paragraph("Detailed Top 10 Breakdown", h2_style))
    top_df = (df.groupby(cat_col)[col]
              .sum()
              .sort_values(ascending=False)
              .head(10)
              .reset_index())
    top_df.columns = [cat_col.replace("_", " ").title(), col.replace("_", " ").title()]
    total = top_df.iloc[:, 1].sum()
    top_df["Share %"] = (top_df.iloc[:, 1] / total * 100).map("{:.1f}%".format)
    top_df.iloc[:, 1] = top_df.iloc[:, 1].map("{:,.2f}".format)

    tbl_data = [list(top_df.columns)] + top_df.values.tolist()
    det_table = Table(tbl_data, colWidths=[8*cm, 5*cm, 4*cm])
    det_table.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), colors.HexColor("#2E75B6")),
        ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.HexColor("#EAF2FB"), colors.white]),
        ("FONTSIZE",    (0, 0), (-1, -1), 9),
        ("GRID",        (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
        ("LEFTPADDING",  (0, 0), (-1, -1), 8),
        ("TOPPADDING",   (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
    ]))
    story.append(det_table)
    story.append(Spacer(1, 0.5*cm))

    # ── Footer note ───────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1,
                             color=colors.HexColor("#CCCCCC"), spaceBefore=10))
    story.append(Paragraph(
        f"Report generated by NexusAI Sales Intelligence Agent · "
        f"{datetime.now().strftime('%Y-%m-%d %H:%M')}",
        ParagraphStyle("footer", parent=styles["Normal"],
                       fontSize=8, textColor=colors.HexColor("#999999"),
                       alignment=TA_CENTER)
    ))

    doc.build(story)
    return f"/static/reports/{fname}"


# ── Public entry point ────────────────────────────────────────
def generate_report() -> dict:
    """
    Called by the orchestrator when the user asks for a report.
    Returns {"text": "...", "chart": None, "report_url": "/static/reports/..."}
    """
    try:
        col     = best_num_col()
        cat_col = best_cat_col()

        if col is None:
            return {"text": "❌ No numeric column found to build a report.", "chart": None}

        charts = _make_charts(col, cat_col)
        kpis   = _kpi_summary(col, cat_col)
        url    = _build_pdf(charts, kpis, col, cat_col)

        summary = (
            f"✅ Sales report generated successfully!\n\n"
            f"📊 Key highlights:\n"
            f"  • Total {col}: {kpis['total']:,.2f}\n"
            f"  • Records analysed: {kpis['count']:,}\n"
            f"  • Top performer: {kpis['top_item']} ({kpis['top_value']:,.2f})\n"
            f"  • Unique {cat_col}s: {kpis['num_cats']}\n\n"
            f"📄 Download your report below."
        )
        return {"text": summary, "chart": None, "report_url": url}

    except Exception as e:
        print(f"[report ERROR] {e}")
        return {"text": f"⚠️ Could not generate report: {e}", "chart": None}