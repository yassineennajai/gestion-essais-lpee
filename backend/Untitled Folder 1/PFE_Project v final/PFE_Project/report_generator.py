"""
report_generator.py
───────────────────
Generates a custom PDF sales report based on the user's request.

Examples:
  "make a report of sales by state"          → col=sales,  cat_col=state
  "report showing profit per category"       → col=profit, cat_col=category
  "give me a report"                         → auto-detects best columns

Fixes:
  - NaTType crash: all values go through _safe_str() before PDF rendering
  - Custom conditions: user question parsed to pick the right columns
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
from reportlab.lib.enums import TA_CENTER

from config import CHART_DIR, REPORTS_DIR, PALETTE
from analytics import df, NUMERIC_COLS, CATEGORICAL_COLS, date_col, best_num_col, best_cat_col


# ══════════════════════════════════════════════════════════════
# 1. PARSE USER REQUEST → find which columns they want
# ══════════════════════════════════════════════════════════════

def _parse_report_request(question: str) -> tuple:
    """
    Try to find which numeric and categorical column the user mentioned.

    "sales by state"        → (sales_col, state_col)
    "profit per category"   → (profit_col, category_col)
    "give me a report"      → (best_num_col, best_cat_col)
    """
    q = question.lower()

    found_num = None
    for col in NUMERIC_COLS:
        words = col.replace("_", " ").split()
        if any(w in q for w in words):
            found_num = col
            break

    found_cat = None
    for col in CATEGORICAL_COLS:
        words = col.replace("_", " ").split()
        if any(w in q for w in words):
            found_cat = col
            break

    final_num = found_num or best_num_col()
    final_cat = found_cat or best_cat_col()
    print(f"[report_parser] num={final_num} | cat={final_cat}")
    return final_num, final_cat


# ══════════════════════════════════════════════════════════════
# 2. SAFE STRING CONVERTER  ← fixes NaTType crash
# ══════════════════════════════════════════════════════════════

def _safe_str(val) -> str:
    """
    Convert any value to a plain string safe for ReportLab.
    Handles NaT, NaN, datetime, Timestamp, and regular values.
    """
    if val is None:
        return ""
    # Check for float NaN
    if isinstance(val, float) and pd.isna(val):
        return ""
    # Check for pandas NaT / NaN generically
    try:
        if pd.isnull(val):
            return ""
    except (TypeError, ValueError):
        pass
    # Format datetimes nicely
    if hasattr(val, "strftime"):
        return val.strftime("%Y-%m-%d")
    return str(val)


# ══════════════════════════════════════════════════════════════
# 3. CHART HELPERS
# ══════════════════════════════════════════════════════════════

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


def _make_charts(data: pd.DataFrame, col: str, cat_col: str) -> dict:
    charts = {}

    # Chart 1 — Bar: all categories
    top = data.groupby(cat_col)[col].sum().sort_values(ascending=False).head(15)
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.bar(range(len(top)), top.values,
           color=[PALETTE[i % len(PALETTE)] for i in range(len(top))],
           edgecolor="#0f1117", linewidth=0.5)
    ax.set_xticks(range(len(top)))
    ax.set_xticklabels(top.index, rotation=40, ha="right", fontsize=8)
    for i, v in enumerate(top.values):
        ax.text(i, v * 1.01, f"{v:,.0f}", ha="center", va="bottom",
                color="#e8eaf0", fontsize=7)
    _style_ax(ax,
              f"{col.replace('_',' ').title()} by {cat_col.replace('_',' ').title()}",
              cat_col, col)
    fig.tight_layout()
    charts["bar"] = _save_chart(fig)

    # Chart 2 — Pie: top 8 share
    pie_data = data.groupby(cat_col)[col].sum().sort_values(ascending=False).head(8)
    fig, ax = plt.subplots(figsize=(6, 6))
    _, texts, autotexts = ax.pie(
        pie_data.values, labels=pie_data.index,
        autopct="%1.1f%%", colors=PALETTE[:len(pie_data)],
        startangle=140, pctdistance=0.82
    )
    for t in texts:     t.set_color("#9ca3af"); t.set_fontsize(9)
    for t in autotexts: t.set_color("#0f1117"); t.set_fontsize(8); t.set_fontweight("bold")
    ax.set_title(
        f"Share by {cat_col.replace('_',' ').title()}",
        color="#e8eaf0", fontsize=11, pad=14
    )
    fig.patch.set_facecolor("#0f1117")
    fig.tight_layout()
    charts["pie"] = _save_chart(fig)

    # Chart 3 — Trend (only if date column exists)
    if date_col and date_col in data.columns:
        # FIX: drop NaT rows before resampling
        dated = data[[date_col, col]].copy()
        dated[date_col] = pd.to_datetime(dated[date_col], errors="coerce")
        dated = dated.dropna(subset=[date_col])
        if not dated.empty:
            trend = dated.set_index(date_col)[col].resample("ME").sum().dropna()
            if len(trend) >= 2:
                fig, ax = plt.subplots(figsize=(9, 3.5))
                ax.fill_between(trend.index, trend.values, alpha=0.15, color=PALETTE[0])
                ax.plot(trend.index, trend.values, color=PALETTE[0],
                        linewidth=2, marker="o", markersize=4,
                        markerfacecolor=PALETTE[2])
                _style_ax(ax, f"Monthly {col.replace('_',' ').title()} Trend", "Date", col)
                fig.tight_layout()
                charts["trend"] = _save_chart(fig)

    return charts


# ══════════════════════════════════════════════════════════════
# 4. KPI SUMMARY
# ══════════════════════════════════════════════════════════════

def _kpi_summary(data: pd.DataFrame, col: str, cat_col: str) -> dict:
    grouped = data.groupby(cat_col)[col].sum().sort_values(ascending=False)
    return {
        "total":     data[col].sum(),
        "average":   data[col].mean(),
        "count":     len(data),
        "top_item":  grouped.index[0]  if not grouped.empty else "N/A",
        "top_value": grouped.iloc[0]   if not grouped.empty else 0,
        "num_cats":  data[cat_col].nunique(),
    }


# ══════════════════════════════════════════════════════════════
# 5. PDF BUILDER
# ══════════════════════════════════════════════════════════════

def _build_pdf(charts: dict, kpis: dict, data: pd.DataFrame,
               col: str, cat_col: str, title_note: str) -> str:

    fname = f"report_{uuid.uuid4().hex[:8]}.pdf"
    fpath = os.path.join(REPORTS_DIR, fname)

    doc = SimpleDocTemplate(fpath, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story  = []

    title_style = ParagraphStyle("RPTTitle", parent=styles["Title"],
        fontSize=20, textColor=colors.HexColor("#1F3864"),
        spaceAfter=4, alignment=TA_CENTER)
    sub_style = ParagraphStyle("RPTSub", parent=styles["Normal"],
        fontSize=10, textColor=colors.HexColor("#6b7591"),
        alignment=TA_CENTER, spaceAfter=12)
    scope_style = ParagraphStyle("RPTScope", parent=styles["Normal"],
        fontSize=9, textColor=colors.HexColor("#444444"),
        leftIndent=4, spaceAfter=14,
        backColor=colors.HexColor("#EAF2FB"), borderPadding=6)
    h2_style = ParagraphStyle("RPTH2", parent=styles["Heading2"],
        fontSize=13, textColor=colors.HexColor("#2E75B6"),
        spaceBefore=14, spaceAfter=8)
    footer_style = ParagraphStyle("RPTFooter", parent=styles["Normal"],
        fontSize=8, textColor=colors.HexColor("#999999"), alignment=TA_CENTER)

    # ── Cover ─────────────────────────────────────────────────
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph("Sales Intelligence Report", title_style))
    story.append(Paragraph(
        f"Generated on {datetime.now().strftime('%B %d, %Y at %H:%M')} · NexusAI Agent",
        sub_style
    ))
    if title_note:
        story.append(Paragraph(f"Report scope: {title_note}", scope_style))
    story.append(HRFlowable(width="100%", thickness=2,
                             color=colors.HexColor("#2E75B6"), spaceAfter=16))

    # ── KPI table ─────────────────────────────────────────────
    story.append(Paragraph("Key Performance Indicators", h2_style))
    kpi_rows = [
        ["Metric", "Value"],
        [f"Total {col.replace('_',' ').title()}",               f"{kpis['total']:,.2f}"],
        [f"Average {col.replace('_',' ').title()} per record",  f"{kpis['average']:,.2f}"],
        ["Total records analysed",                              f"{kpis['count']:,}"],
        [f"Top {cat_col.replace('_',' ').title()}",             _safe_str(kpis['top_item'])],
        [f"Top {cat_col.replace('_',' ').title()} value",       f"{kpis['top_value']:,.2f}"],
        [f"Unique {cat_col.replace('_',' ').title()}s",         str(kpis['num_cats'])],
    ]
    kpi_t = Table(kpi_rows, colWidths=[9*cm, 8*cm])
    kpi_t.setStyle(TableStyle([
        ("BACKGROUND",     (0,0), (-1,0), colors.HexColor("#1F3864")),
        ("TEXTCOLOR",      (0,0), (-1,0), colors.white),
        ("FONTNAME",       (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",       (0,0), (-1,0), 11),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.HexColor("#EAF2FB"), colors.white]),
        ("FONTSIZE",       (0,1), (-1,-1), 10),
        ("GRID",           (0,0), (-1,-1), 0.5, colors.HexColor("#CCCCCC")),
        ("LEFTPADDING",    (0,0), (-1,-1), 10),
        ("RIGHTPADDING",   (0,0), (-1,-1), 10),
        ("TOPPADDING",     (0,0), (-1,-1), 7),
        ("BOTTOMPADDING",  (0,0), (-1,-1), 7),
    ]))
    story.append(kpi_t)
    story.append(Spacer(1, 0.5*cm))

    # ── Bar chart ─────────────────────────────────────────────
    story.append(Paragraph(
        f"{col.replace('_',' ').title()} by {cat_col.replace('_',' ').title()}", h2_style))
    story.append(Image(charts["bar"], width=16*cm, height=7*cm))
    story.append(Spacer(1, 0.4*cm))

    # ── Trend chart ───────────────────────────────────────────
    if "trend" in charts:
        story.append(Paragraph(f"Monthly {col.replace('_',' ').title()} Trend", h2_style))
        story.append(Image(charts["trend"], width=16*cm, height=6*cm))
        story.append(Spacer(1, 0.4*cm))

    story.append(PageBreak())

    # ── Pie chart ─────────────────────────────────────────────
    story.append(Paragraph(f"Distribution of {col.replace('_',' ').title()}", h2_style))
    story.append(Image(charts["pie"], width=10*cm, height=10*cm))
    story.append(Spacer(1, 0.4*cm))

    # ── Full breakdown table (ALL rows, not just top 10) ──────
    story.append(Paragraph(
        f"Complete Breakdown: {col.replace('_',' ').title()} "
        f"by {cat_col.replace('_',' ').title()}", h2_style))

    summary = (
        data.groupby(cat_col)[col]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    total_val = summary[col].sum()
    summary["Share %"] = (summary[col] / total_val * 100).map("{:.1f}%".format)
    summary[col]       = summary[col].map("{:,.2f}".format)
    summary.columns    = [
        cat_col.replace("_", " ").title(),
        col.replace("_", " ").title(),
        "Share %"
    ]

    # Convert every cell to safe string → prevents NaTType crash
    tbl_rows = [list(summary.columns)]
    for _, row in summary.iterrows():
        tbl_rows.append([_safe_str(v) for v in row])

    det_t = Table(tbl_rows, colWidths=[8*cm, 5*cm, 4*cm], repeatRows=1)
    det_t.setStyle(TableStyle([
        ("BACKGROUND",     (0,0), (-1,0), colors.HexColor("#2E75B6")),
        ("TEXTCOLOR",      (0,0), (-1,0), colors.white),
        ("FONTNAME",       (0,0), (-1,0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.HexColor("#EAF2FB"), colors.white]),
        ("FONTSIZE",       (0,0), (-1,-1), 9),
        ("GRID",           (0,0), (-1,-1), 0.4, colors.HexColor("#CCCCCC")),
        ("LEFTPADDING",    (0,0), (-1,-1), 8),
        ("TOPPADDING",     (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",  (0,0), (-1,-1), 5),
    ]))
    story.append(det_t)
    story.append(Spacer(1, 0.5*cm))

    # ── Footer ────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1,
                             color=colors.HexColor("#CCCCCC"), spaceBefore=10))
    story.append(Paragraph(
        f"NexusAI Sales Intelligence Agent · {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        footer_style
    ))

    doc.build(story)
    return f"/static/reports/{fname}"


# ══════════════════════════════════════════════════════════════
# 6. PUBLIC ENTRY POINT
# ══════════════════════════════════════════════════════════════

def generate_report(question: str = "", lang: str = "en") -> dict:
    """
    Called by the orchestrator.

    Parameters
    ----------
    question : str  — user's original message (used to detect columns)
    lang     : str  — "fr" or "en" for the response message

    Returns
    -------
    {"text": str, "chart": None, "report_url": "/static/reports/xxx.pdf"}
    """
    try:
        # Step 1 — detect which columns the user wants
        col, cat_col = _parse_report_request(question)

        if col is None:
            msg = ("❌ Aucune colonne numérique trouvée."
                   if lang == "fr" else
                   "❌ No numeric column found to build a report.")
            return {"text": msg, "chart": None}

        # Step 2 — build a clean working copy
        keep_cols = [col, cat_col] + ([date_col] if date_col else [])
        data = df[keep_cols].copy().dropna(subset=[col, cat_col])

        if data.empty:
            msg = (f"⚠️ Aucune donnée pour {col} par {cat_col}."
                   if lang == "fr" else
                   f"⚠️ No data available for {col} by {cat_col}.")
            return {"text": msg, "chart": None}

        # Step 3 — charts → KPIs → PDF
        charts     = _make_charts(data, col, cat_col)
        kpis       = _kpi_summary(data, col, cat_col)
        title_note = question.strip() or "Full sales overview"
        url        = _build_pdf(charts, kpis, data, col, cat_col, title_note)

        # Step 4 — summary message
        if lang == "fr":
            summary = (
                f"✅ Rapport généré avec succès !\n\n"
                f"📊 Points clés :\n"
                f"  • Total {col} : {kpis['total']:,.2f}\n"
                f"  • Enregistrements : {kpis['count']:,}\n"
                f"  • Meilleur {cat_col} : {_safe_str(kpis['top_item'])} "
                f"({kpis['top_value']:,.2f})\n"
                f"  • {cat_col}s uniques : {kpis['num_cats']}\n\n"
                f"📄 Téléchargez votre rapport ci-dessous."
            )
        else:
            summary = (
                f"✅ Report generated successfully!\n\n"
                f"📊 Key highlights:\n"
                f"  • Total {col}: {kpis['total']:,.2f}\n"
                f"  • Records analysed: {kpis['count']:,}\n"
                f"  • Top {cat_col}: {_safe_str(kpis['top_item'])} "
                f"({kpis['top_value']:,.2f})\n"
                f"  • Unique {cat_col}s: {kpis['num_cats']}\n\n"
                f"📄 Download your report below."
            )

        return {"text": summary, "chart": None, "report_url": url}

    except Exception as e:
        import traceback; traceback.print_exc()
        msg = (f"⚠️ Impossible de générer le rapport : {e}"
               if lang == "fr" else
               f"⚠️ Could not generate report: {e}")
        return {"text": msg, "chart": None}