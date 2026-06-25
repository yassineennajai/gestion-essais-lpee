"""
analytics.py
────────────
All data analysis and chart generation.
Receives a routing decision dict from the orchestrator,
runs the correct calculation on the DataFrame, and returns
{"text": "...", "chart": "/static/charts/xxxx.png" | None}
"""
import uuid
import os

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from config import CHART_DIR, CSV_PATH, PALETTE

# ── Load & prepare dataset once at startup ────────────────────
def _load_df(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"❌ Sales_Data.csv not found at: {path}\n"
            "   Place it inside the KnowledgeBase/ folder."
        )
    frame = pd.read_csv(path)
    frame.columns = (frame.columns
                     .str.strip()
                     .str.lower()
                     .str.replace(" ", "_"))
    return frame

df = _load_df(CSV_PATH)

# Detect and parse the date column
date_col = next((c for c in df.columns if "date" in c), None)
if date_col:
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df["order_year"]       = df[date_col].dt.year
    df["order_month"]      = df[date_col].dt.month
    df["order_month_name"] = df[date_col].dt.strftime("%b")

# Column groups
NUMERIC_COLS     = df.select_dtypes(include="number").columns.tolist()
CATEGORICAL_COLS = df.select_dtypes(include="object").columns.tolist()
DATE_COLS        = [c for c in df.columns if "date" in c]
ALL_COLS         = list(df.columns)

import json
SAMPLE_ROWS = json.loads(df.head(3).to_json(orient="records", date_format="iso"))

print(f"✅ Dataset: {len(df)} rows | columns: {ALL_COLS}")


# ── Helpers ───────────────────────────────────────────────────
def best_cat_col() -> str:
    """Return the most useful categorical column (2–50 unique values)."""
    for c in CATEGORICAL_COLS:
        if 2 <= df[c].nunique() <= 50:
            return c
    return CATEGORICAL_COLS[0] if CATEGORICAL_COLS else ALL_COLS[0]

def best_num_col() -> str | None:
    """Return the most likely revenue/sales numeric column."""
    preferred = ["sales", "revenue", "profit", "quantity", "amount", "total", "price"]
    for p in preferred:
        for c in NUMERIC_COLS:
            if p in c:
                return c
    return NUMERIC_COLS[0] if NUMERIC_COLS else None


# ── Chart helpers ─────────────────────────────────────────────
def _save_fig() -> str:
    """Save current matplotlib figure and return its URL path."""
    fname = f"{uuid.uuid4().hex}.png"
    fpath = os.path.join(CHART_DIR, fname)
    plt.savefig(fpath, dpi=130, bbox_inches="tight", facecolor="#0f1117")
    plt.close("all")
    return f"/static/charts/{fname}"

def _style(ax, title: str, xlabel: str = "", ylabel: str = ""):
    """Apply dark theme to an axes object."""
    ax.figure.patch.set_facecolor("#0f1117")
    ax.set_facecolor("#1a1d27")
    ax.set_title(title, color="#e8eaf0", fontsize=13, pad=12, fontweight="bold")
    ax.set_xlabel(xlabel, color="#9ca3af", fontsize=10)
    ax.set_ylabel(ylabel, color="#9ca3af", fontsize=10)
    ax.tick_params(colors="#9ca3af", labelsize=9)
    for spine in ax.spines.values():
        spine.set_edgecolor("#2d3047")
    ax.yaxis.set_major_formatter(
        mticker.FuncFormatter(
            lambda x, _: f"{x:,.0f}" if abs(x) >= 1 else f"{x:.2f}"
        )
    )
    ax.grid(axis="y", color="#2d3047", linewidth=0.6, linestyle="--", alpha=0.7)


# ── Main entry point ──────────────────────────────────────────
def handle_analytics(parsed: dict) -> dict:
    """
    Execute the analytics request described in `parsed`.
    Returns {"text": str, "chart": str | None}
    """
    metric      = parsed.get("metric") or "sum"
    columns     = parsed.get("columns") or []
    filters     = parsed.get("filters") or {}
    group_by    = parsed.get("group_by") or []
    top_n       = int(parsed.get("top_n") or 5)
    chart_type  = parsed.get("chart_type")
    time_period = parsed.get("time_period")

    data = df.copy()

    # Resolve the best numeric column
    col = next(
        (c for c in columns if c in data.columns and c in NUMERIC_COLS),
        best_num_col()
    )
    if col is None:
        return {"text": "❌ No numeric column found in the dataset.", "chart": None}

    # Validate group_by columns
    group_by = [g for g in group_by if g in data.columns]

    # Apply filters
    for fc, fv in filters.items():
        if fc in data.columns:
            try:
                data = data[data[fc].astype(str).str.lower() == str(fv).lower()]
            except Exception as fe:
                print(f"[filter error] {fe}")

    if data.empty:
        return {"text": f"⚠️ No data after applying filters: {filters}", "chart": None}

    # ── DISTRIBUTION ─────────────────────────────────────────
    if metric == "distribution" or chart_type == "hist":
        fig, ax = plt.subplots(figsize=(9, 4))
        ax.hist(data[col].dropna(), bins=25, color=PALETTE[0],
                edgecolor="#0f1117", alpha=0.9)
        _style(ax, f"Distribution of {col}", col, "Frequency")
        fig.tight_layout()
        text = (
            f"Distribution of {col}:\n"
            f"  Mean   = {data[col].mean():,.2f}\n"
            f"  Median = {data[col].median():,.2f}\n"
            f"  Std    = {data[col].std():,.2f}\n"
            f"  Min    = {data[col].min():,.2f} | Max = {data[col].max():,.2f}"
        )
        return {"text": text, "chart": _save_fig()}

    # ── CORRELATION ──────────────────────────────────────────
    if metric == "correlation":
        num_data = data[[c for c in NUMERIC_COLS if c in data.columns]].dropna()
        corr = num_data.corr()
        fig, ax = plt.subplots(figsize=(8, 6))
        im = ax.imshow(corr.values, cmap="coolwarm", vmin=-1, vmax=1, aspect="auto")
        plt.colorbar(im, ax=ax)
        ax.set_xticks(range(len(corr.columns)))
        ax.set_xticklabels(corr.columns, rotation=45, ha="right", color="#9ca3af")
        ax.set_yticks(range(len(corr.columns)))
        ax.set_yticklabels(corr.columns, color="#9ca3af")
        ax.set_title("Correlation Matrix", color="#e8eaf0", fontsize=13)
        ax.figure.patch.set_facecolor("#0f1117")
        ax.set_facecolor("#1a1d27")
        fig.tight_layout()
        return {"text": "Correlation matrix for all numeric columns.", "chart": _save_fig()}

    # ── TREND ────────────────────────────────────────────────
    if metric == "trend" or chart_type == "line":
        dc = date_col
        if dc is None:
            return {"text": "No date column found for trend analysis.", "chart": None}
        freq = {"monthly": "ME", "yearly": "YE", "daily": "D"}.get(time_period, "ME")
        trend = data.set_index(dc)[col].resample(freq).sum().dropna()
        if trend.empty:
            return {"text": f"Not enough date data to show trend for {col}.", "chart": None}

        fig, ax = plt.subplots(figsize=(10, 4))
        ax.fill_between(trend.index, trend.values, alpha=0.12, color=PALETTE[0])
        ax.plot(trend.index, trend.values, color=PALETTE[0], linewidth=2.5,
                marker="o", markersize=4, markerfacecolor=PALETTE[2])
        _style(ax, f"{col.replace('_',' ').title()} Over Time", "Date", col)
        fig.tight_layout()

        peak_label = (trend.idxmax().strftime("%Y-%m")
                      if hasattr(trend.idxmax(), "strftime") else str(trend.idxmax()))
        text = (
            f"{(time_period or 'monthly').capitalize()} trend of {col}.\n"
            f"  Total = {data[col].sum():,.2f}\n"
            f"  Peak  = {trend.max():,.2f} ({peak_label})"
        )
        return {"text": text, "chart": _save_fig()}

    # ── TOP N ────────────────────────────────────────────────
    if metric == "top_n":
        grp = (group_by[0] if group_by else best_cat_col())
        top = data.groupby(grp)[col].sum().sort_values(ascending=False).head(top_n)
        if top.empty:
            return {"text": f"No data to rank for {grp}.", "chart": None}

        fig, ax = plt.subplots(figsize=(9, 4))
        colors = [PALETTE[i % len(PALETTE)] for i in range(len(top))]
        bars = ax.bar(range(len(top)), top.values,
                      color=colors, edgecolor="#0f1117", linewidth=0.5)
        ax.set_xticks(range(len(top)))
        ax.set_xticklabels(top.index, rotation=35, ha="right")
        _style(ax,
               f"Top {top_n} {grp.replace('_',' ').title()} by {col.replace('_',' ').title()}",
               grp, col)
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, h * 1.01,
                    f"{h:,.0f}", ha="center", va="bottom", color="#e8eaf0", fontsize=8)
        fig.tight_layout()

        rows = "\n".join(
            f"  {i+1}. {k}: {v:,.2f}" for i, (k, v) in enumerate(top.items())
        )
        return {"text": f"Top {top_n} {grp} by {col}:\n{rows}", "chart": _save_fig()}

    # ── PIE ──────────────────────────────────────────────────
    if chart_type == "pie":
        grp = (group_by[0] if group_by else best_cat_col())
        pie_data = data.groupby(grp)[col].sum().sort_values(ascending=False).head(8)
        fig, ax = plt.subplots(figsize=(7, 7))
        _, texts, autotexts = ax.pie(
            pie_data.values, labels=pie_data.index,
            autopct="%1.1f%%", colors=PALETTE[:len(pie_data)],
            startangle=140, pctdistance=0.8
        )
        for t in texts:     t.set_color("#9ca3af"); t.set_fontsize(10)
        for t in autotexts: t.set_color("#0f1117"); t.set_fontsize(9); t.set_fontweight("bold")
        ax.set_title(
            f"{col.replace('_',' ').title()} by {grp.replace('_',' ').title()}",
            color="#e8eaf0", fontsize=13, pad=16
        )
        fig.patch.set_facecolor("#0f1117")
        fig.tight_layout()
        return {"text": f"Pie chart: {col} by {grp}.", "chart": _save_fig()}

    # ── STANDARD AGGREGATIONS (sum / average / count / max / min) ──
    if metric in ("sum", "average", "count", "max", "min"):
        agg = {"sum": "sum", "average": "mean",
               "count": "count", "max": "max", "min": "min"}[metric]

        if group_by and group_by[0] in data.columns:
            grp    = group_by[0]
            result = getattr(data.groupby(grp)[col], agg)().sort_values(ascending=False)
            top_r  = result.head(15)

            fig, ax = plt.subplots(figsize=(9, 4))
            ax.bar(range(len(top_r)), top_r.values,
                   color=[PALETTE[i % len(PALETTE)] for i in range(len(top_r))],
                   edgecolor="#0f1117")
            ax.set_xticks(range(len(top_r)))
            ax.set_xticklabels(top_r.index, rotation=35, ha="right")
            _style(ax,
                   f"{metric.capitalize()} of {col.replace('_',' ').title()} "
                   f"by {grp.replace('_',' ').title()}",
                   grp, col)
            fig.tight_layout()

            rows = "\n".join(f"  {k}: {v:,.2f}" for k, v in result.head(10).items())
            return {
                "text": f"{metric.capitalize()} of {col} by {grp}:\n{rows}",
                "chart": _save_fig()
            }
        else:
            val = getattr(data[col], agg)()
            return {"text": f"{metric.capitalize()} of {col} = {val:,.2f}", "chart": None}

    # ── FALLBACK ─────────────────────────────────────────────
    return {"text": f"⚠️ Metric '{metric}' is not supported yet.", "chart": None}