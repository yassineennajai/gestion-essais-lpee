from flask import Flask, request, jsonify, render_template
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import uuid, os, boto3, json, re

# ===============================================================
# CONFIG
# ===============================================================
REGION    = "us-east-1"
KB_ID     = "E4ZNPDMCPC"
MODEL_ID  = "anthropic.claude-3-haiku-20240307-v1:0"
CHART_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "charts")
os.makedirs(CHART_DIR, exist_ok=True)

# ===============================================================
# AWS CLIENTS
# ===============================================================
bedrock_runtime = boto3.client("bedrock-runtime",       region_name=REGION)
agent_client    = boto3.client("bedrock-agent-runtime", region_name=REGION)

# ===============================================================
# LOAD & ENRICH DATASET
# ===============================================================
# Always resolve path relative to this file, not the working directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(BASE_DIR, "Sales_Data.csv")
if not os.path.exists(csv_path):
    raise FileNotFoundError(f"❌ Sales_Data.csv not found at: {csv_path}\n"
                            f"   Make sure Sales_Data.csv is in the same folder as app.py")
df = pd.read_csv(csv_path)
df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

# Normalize date column - find it automatically
date_col = next((c for c in df.columns if "date" in c), None)
if date_col:
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df["order_year"]       = df[date_col].dt.year
    df["order_month"]      = df[date_col].dt.month
    df["order_month_name"] = df[date_col].dt.strftime("%b")

NUMERIC_COLS     = df.select_dtypes(include="number").columns.tolist()
CATEGORICAL_COLS = df.select_dtypes(include="object").columns.tolist()
DATE_COLS        = [c for c in df.columns if "date" in c]
ALL_COLS         = list(df.columns)
# Show 3 sample rows but convert dates to string so JSON serialization never fails
SAMPLE_ROWS = json.loads(df.head(3).to_json(orient="records", date_format="iso"))

print("✅ Dataset loaded:", len(df), "rows |", ALL_COLS)
print("   Numeric :", NUMERIC_COLS)
print("   Categorical:", CATEGORICAL_COLS)

# ===============================================================
# MEMORY
# ===============================================================
memory_store = {}

# ===============================================================
# HELPERS
# ===============================================================
CHART_KW = [
    "show","visualize","chart","graph","plot","display","draw",
    "bar","line","trend","top","compare","distribution","breakdown",
    "evolution","monthly","yearly","over time","pie","histogram","visual"
]

def wants_chart(q: str) -> bool:
    q = q.lower()
    return any(k in q for k in CHART_KW)

def best_cat_col():
    """Return the most useful categorical column (low cardinality)."""
    for c in CATEGORICAL_COLS:
        n = df[c].nunique()
        if 2 <= n <= 50:
            return c
    return CATEGORICAL_COLS[0] if CATEGORICAL_COLS else ALL_COLS[0]

def best_num_col():
    """Return the most likely sales/revenue numeric column."""
    preferred = ["sales","revenue","profit","quantity","amount","total","price"]
    for p in preferred:
        for c in NUMERIC_COLS:
            if p in c:
                return c
    return NUMERIC_COLS[0] if NUMERIC_COLS else None

# ===============================================================
# CHART STYLE
# ===============================================================
PALETTE = ["#4F8EF7","#F76C5E","#43C59E","#F9A825","#AB47BC",
           "#26C6DA","#EF5350","#66BB6A","#FFA726","#5C6BC0"]

def _save_fig() -> str:
    filename = f"{uuid.uuid4().hex}.png"
    path = os.path.join(CHART_DIR, filename)
    plt.savefig(path, dpi=130, bbox_inches="tight", facecolor="#0f1117")
    plt.close("all")
    return "/" + path

def _style(ax, title, xlabel="", ylabel=""):
    ax.figure.patch.set_facecolor("#0f1117")
    ax.set_facecolor("#1a1d27")
    ax.set_title(title, color="#e8eaf0", fontsize=13, pad=12, fontweight="bold")
    ax.set_xlabel(xlabel, color="#9ca3af", fontsize=10)
    ax.set_ylabel(ylabel, color="#9ca3af", fontsize=10)
    ax.tick_params(colors="#9ca3af", labelsize=9)
    for spine in ax.spines.values():
        spine.set_edgecolor("#2d3047")
    ax.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda x, _: f"{x:,.0f}" if abs(x) >= 1 else f"{x:.2f}"))
    ax.grid(axis="y", color="#2d3047", linewidth=0.6, linestyle="--", alpha=0.7)

# ===============================================================
# 1. PARSE QUESTION
# ===============================================================
def parse_question(question: str, session_id: str = None) -> dict:
    mem = ""
    if session_id and session_id in memory_store:
        for qa in memory_store[session_id][-3:]:
            mem += f"Q: {qa['question']}\nA: {str(qa['answer'])[:100]}\n"

    wants = wants_chart(question)

    prompt = f"""You are a data analyst. You have a pandas DataFrame called df.

DataFrame info:
- All columns: {ALL_COLS}
- Numeric columns: {NUMERIC_COLS}
- Categorical columns: {CATEGORICAL_COLS}
- Date columns: {DATE_COLS}
- Sample rows: {json.dumps(SAMPLE_ROWS)}

Recent conversation:
{mem if mem else "None"}

User question: "{question}"
{"⚠️ The user WANTS a chart or visual output." if wants else ""}

Return ONLY a single JSON object. No markdown. No explanation. Just the JSON.

JSON structure:
{{
  "type": "analytics",
  "intent": "short description of what user wants",
  "metric": "top_n",
  "columns": ["sales"],
  "filters": {{}},
  "group_by": ["product_name"],
  "top_n": 5,
  "chart_type": "bar",
  "time_period": null
}}

Field rules:
- "type" must be one of: "analytics", "rag", "freeform_analytics"
  • analytics = any question about data numbers, rankings, sums, charts
  • rag = company info, policies, product descriptions, FAQ — things NOT in the CSV
  • freeform_analytics = complex multi-step data question that needs custom code
- "metric" must be one of: "sum", "average", "count", "max", "min", "trend", "top_n", "distribution", "correlation"
- "columns" → ONLY use names from: {NUMERIC_COLS}
- "group_by" → ONLY use names from: {CATEGORICAL_COLS}
- "chart_type" → one of: "bar", "line", "pie", "hist", null
- If user says "show", "chart", "plot", "visualize", "top", "compare" → set chart_type to "bar" or "line"
- If user says "trend", "over time", "monthly", "yearly" → metric="trend", chart_type="line"
- If user says "top N" or "best" or "ranking" → metric="top_n", chart_type="bar"
- If user says "distribution" or "histogram" → metric="distribution", chart_type="hist"
- If user says "pie" or "share" or "proportion" → chart_type="pie"
- If user says "correlation" → metric="correlation"
- "time_period": "monthly", "yearly", "daily", or null
- "top_n": integer, default 5
"""

    try:
        resp = bedrock_runtime.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 600,
                "messages": [{"role": "user", "content": prompt}]
            })
        )
        raw = json.loads(resp["body"].read())["content"][0]["text"].strip()
        print(f"[parser raw] {raw[:300]}")

        # Strip markdown fences if present
        raw = re.sub(r"```json|```", "", raw).strip()
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if not m:
            raise ValueError("No JSON found in LLM response")

        parsed = json.loads(m.group())

        # ── SAFETY NETS ──────────────────────────────────────────
        # 1. Force analytics if chart keywords used
        if wants and parsed.get("type") == "rag":
            parsed["type"]       = "analytics"
            parsed["metric"]     = parsed.get("metric") or "top_n"
            parsed["chart_type"] = parsed.get("chart_type") or "bar"

        # 2. Validate columns exist, else use fallbacks
        cols = parsed.get("columns") or []
        parsed["columns"] = [c for c in cols if c in NUMERIC_COLS] or [best_num_col()]

        grps = parsed.get("group_by") or []
        parsed["group_by"] = [g for g in grps if g in df.columns] or []

        # 3. If metric is top_n but no group_by, assign best categorical
        if parsed.get("metric") == "top_n" and not parsed["group_by"]:
            parsed["group_by"] = [best_cat_col()]

        # 4. If metric is sum/average/etc with group_by, always generate chart
        if parsed.get("metric") in ["sum","average","count","max","min"] and parsed["group_by"]:
            if not parsed.get("chart_type"):
                parsed["chart_type"] = "bar"

        print(f"[parsed] {parsed}")
        return parsed

    except Exception as e:
        print(f"[parse_question ERROR] {e}")
        # Last resort fallback
        if wants:
            return {
                "type": "analytics", "metric": "top_n",
                "columns": [best_num_col()], "group_by": [best_cat_col()],
                "chart_type": "bar", "top_n": 5, "filters": {}
            }
        return {"type": "rag"}

# ===============================================================
# 2. ANALYTICS ENGINE
# ===============================================================
def handle_analytics(parsed: dict) -> dict:
    metric      = parsed.get("metric") or "sum"
    columns     = parsed.get("columns") or [best_num_col()]
    filters     = parsed.get("filters") or {}
    group_by    = parsed.get("group_by") or []
    top_n       = int(parsed.get("top_n") or 5)
    chart_type  = parsed.get("chart_type")
    time_period = parsed.get("time_period")

    data = df.copy()

    # Resolve numeric column
    col = next((c for c in columns if c in data.columns and c in NUMERIC_COLS), best_num_col())
    if col is None:
        return {"text": "❌ No numeric column found in your dataset.", "chart": None}

    # Apply filters
    for fc, fv in (filters or {}).items():
        if fc in data.columns:
            try:
                data = data[data[fc].astype(str).str.lower() == str(fv).lower()]
            except Exception as fe:
                print(f"[filter error] {fe}")

    if data.empty:
        return {"text": f"⚠️ No data found after filters: {filters}", "chart": None}

    # ── DISTRIBUTION ─────────────────────────────────────────
    if metric == "distribution" or chart_type == "hist":
        fig, ax = plt.subplots(figsize=(9, 4))
        ax.hist(data[col].dropna(), bins=25, color=PALETTE[0], edgecolor="#0f1117", alpha=0.9)
        _style(ax, f"Distribution of {col}", col, "Frequency")
        fig.tight_layout()
        summary = (f"Distribution of {col}:\n"
                   f"  Mean = {data[col].mean():,.2f}\n"
                   f"  Median = {data[col].median():,.2f}\n"
                   f"  Std = {data[col].std():,.2f}\n"
                   f"  Min = {data[col].min():,.2f} | Max = {data[col].max():,.2f}")
        return {"text": summary, "chart": _save_fig()}

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
        return {"text": "Correlation matrix of all numeric columns.", "chart": _save_fig()}

    # ── TREND ────────────────────────────────────────────────
    if metric == "trend" or chart_type == "line":
        dc = date_col or next((c for c in data.columns if "date" in c), None)
        if dc is None:
            return {"text": "No date column found for trend analysis.", "chart": None}

        freq_map = {"monthly": "ME", "yearly": "YE", "daily": "D"}
        freq = freq_map.get(time_period, "ME")

        trend = data.set_index(dc)[col].resample(freq).sum().dropna()
        if trend.empty:
            return {"text": f"Not enough dated data to show trend for {col}.", "chart": None}

        fig, ax = plt.subplots(figsize=(10, 4))
        ax.fill_between(trend.index, trend.values, alpha=0.12, color=PALETTE[0])
        ax.plot(trend.index, trend.values, color=PALETTE[0], linewidth=2.5,
                marker="o", markersize=4, markerfacecolor=PALETTE[2])
        _style(ax, f"{col.replace('_',' ').title()} Over Time", "Date", col)
        fig.tight_layout()

        period_label = time_period or "monthly"
        return {
            "text": (f"{period_label.capitalize()} trend of {col}.\n"
                     f"  Total = {data[col].sum():,.2f}\n"
                     f"  Peak  = {trend.max():,.2f} ({trend.idxmax().strftime('%Y-%m') if hasattr(trend.idxmax(),'strftime') else trend.idxmax()})"),
            "chart": _save_fig()
        }

    # ── TOP N ────────────────────────────────────────────────
    if metric == "top_n":
        grp = group_by[0] if group_by else best_cat_col()
        if grp not in data.columns:
            grp = best_cat_col()

        top = data.groupby(grp)[col].sum().sort_values(ascending=False).head(top_n)
        if top.empty:
            return {"text": f"No data to rank for {grp}.", "chart": None}

        fig, ax = plt.subplots(figsize=(9, 4))
        colors = [PALETTE[i % len(PALETTE)] for i in range(len(top))]
        bars = ax.bar(range(len(top)), top.values, color=colors, edgecolor="#0f1117", linewidth=0.5)
        ax.set_xticks(range(len(top)))
        ax.set_xticklabels(top.index, rotation=35, ha="right")
        _style(ax, f"Top {top_n} {grp.replace('_',' ').title()} by {col.replace('_',' ').title()}", grp, col)
        # Value labels
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, h * 1.01,
                    f"{h:,.0f}", ha="center", va="bottom", color="#e8eaf0", fontsize=8)
        fig.tight_layout()

        rows = "\n".join([f"  {i+1}. {k}: {v:,.2f}" for i, (k, v) in enumerate(top.items())])
        return {"text": f"Top {top_n} {grp} by {col}:\n{rows}", "chart": _save_fig()}

    # ── PIE ──────────────────────────────────────────────────
    if chart_type == "pie":
        grp = group_by[0] if group_by else best_cat_col()
        if grp not in data.columns:
            grp = best_cat_col()

        pie_data = data.groupby(grp)[col].sum().sort_values(ascending=False).head(8)
        fig, ax = plt.subplots(figsize=(7, 7))
        wedges, texts, autotexts = ax.pie(
            pie_data.values, labels=pie_data.index,
            autopct="%1.1f%%", colors=PALETTE[:len(pie_data)],
            startangle=140, pctdistance=0.8)
        for t in texts:      t.set_color("#9ca3af"); t.set_fontsize(10)
        for t in autotexts:  t.set_color("#0f1117"); t.set_fontsize(9); t.set_fontweight("bold")
        ax.set_title(f"{col.replace('_',' ').title()} by {grp.replace('_',' ').title()}",
                     color="#e8eaf0", fontsize=13, pad=16)
        fig.patch.set_facecolor("#0f1117")
        fig.tight_layout()
        return {"text": f"Pie chart: {col} distribution by {grp}.", "chart": _save_fig()}

    # ── STANDARD METRICS (sum/avg/count/max/min) ─────────────
    if metric in ["sum", "average", "count", "max", "min"]:
        agg_map = {"sum": "sum", "average": "mean", "count": "count",
                   "max": "max", "min": "min"}
        agg = agg_map[metric]

        if group_by and group_by[0] in data.columns:
            grp = group_by[0]
            result = getattr(data.groupby(grp)[col], agg)().sort_values(ascending=False)

            # Always make a bar chart for grouped results
            fig, ax = plt.subplots(figsize=(9, 4))
            top_r = result.head(15)
            ax.bar(range(len(top_r)), top_r.values,
                   color=[PALETTE[i % len(PALETTE)] for i in range(len(top_r))],
                   edgecolor="#0f1117")
            ax.set_xticks(range(len(top_r)))
            ax.set_xticklabels(top_r.index, rotation=35, ha="right")
            _style(ax, f"{metric.capitalize()} of {col.replace('_',' ').title()} by {grp.replace('_',' ').title()}", grp, col)
            fig.tight_layout()

            rows = "\n".join([f"  {k}: {v:,.2f}" for k, v in result.head(10).items()])
            return {
                "text": f"{metric.capitalize()} of {col} grouped by {grp}:\n{rows}",
                "chart": _save_fig()
            }
        else:
            val = getattr(data[col], agg)()
            # Even for single values, make a small summary chart if it's interesting
            return {"text": f"{metric.capitalize()} of {col} = {val:,.2f}", "chart": None}

    # ── FALLBACK: run as freeform ────────────────────────────
    return handle_freeform(parsed.get("intent", "") or "Analyze the data")

# ===============================================================
# 3. FREEFORM ANALYTICS (LLM writes + executes pandas code)
# ===============================================================
def handle_freeform(question: str) -> dict:
    code_prompt = f"""You have a pandas DataFrame called `df`.
Columns: {ALL_COLS}
Numeric: {NUMERIC_COLS}
Categorical: {CATEGORICAL_COLS}
Date col: {date_col}
Sample: {json.dumps(SAMPLE_ROWS)}

Task: "{question}"

Write Python code that:
1. Analyzes df to answer the task
2. Stores a clear string answer in `result_text`
3. Saves ONE chart to `chart_path` (full string path) if a visual helps
4. Sets `chart_path = None` if no chart needed
5. Uses CHART_DIR variable for saving: os.path.join(CHART_DIR, uuid.uuid4().hex + ".png")

Chart dark style to use:
  fig, ax = plt.subplots(figsize=(9,4))
  # ... your plot code ...
  fig.patch.set_facecolor("#0f1117")
  ax.set_facecolor("#1a1d27")
  ax.tick_params(colors="#9ca3af")
  ax.set_title("Title", color="#e8eaf0", fontsize=13)
  ax.set_xlabel("x", color="#9ca3af")
  ax.set_ylabel("y", color="#9ca3af")
  for spine in ax.spines.values(): spine.set_edgecolor("#2d3047")
  fig.tight_layout()
  chart_path = os.path.join(CHART_DIR, uuid.uuid4().hex + ".png")
  plt.savefig(chart_path, dpi=130, bbox_inches="tight", facecolor="#0f1117")
  plt.close("all")

Rules:
- No imports (pandas as pd, numpy as np, matplotlib.pyplot as plt, os, uuid already available)
- No markdown, no explanation — ONLY Python code
- result_text must be a readable string with actual numbers/values
"""
    try:
        resp = bedrock_runtime.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1500,
                "messages": [{"role": "user", "content": code_prompt}]
            })
        )
        code = json.loads(resp["body"].read())["content"][0]["text"].strip()
        code = re.sub(r"```python|```", "", code).strip()
        print(f"[freeform code]\n{code[:400]}")

        local_vars = {
            "df": df.copy(), "CHART_DIR": CHART_DIR,
            "pd": pd, "np": np, "plt": plt,
            "os": os, "uuid": uuid,
            "result_text": "Analysis complete.", "chart_path": None
        }
        exec(code, local_vars)

        result_text = str(local_vars.get("result_text", "Done."))
        chart_path  = local_vars.get("chart_path")
        chart_url   = ("/" + str(chart_path).replace("\\", "/")) if chart_path else None
        return {"text": result_text, "chart": chart_url}

    except Exception as e:
        print(f"[freeform ERROR] {e}")
        return {"text": f"⚠️ Could not compute: {e}", "chart": None}

# ===============================================================
# 4. RAG (Amazon Bedrock Knowledge Base)
# ===============================================================
def ask_rag(question: str) -> dict:
    try:
        resp = agent_client.retrieve_and_generate(
            input={"text": question},
            retrieveAndGenerateConfiguration={
                "type": "KNOWLEDGE_BASE",
                "knowledgeBaseConfiguration": {
                    "knowledgeBaseId": KB_ID,
                    "modelArn": f"arn:aws:bedrock:{REGION}::foundation-model/{MODEL_ID}",
                    "retrievalConfiguration": {
                        "vectorSearchConfiguration": {"numberOfResults": 5}
                    }
                }
            }
        )
        answer = resp.get("output", {}).get("text", "")
        if not answer:
            answer = "I couldn't find an answer in the knowledge base for that question."

        # Append source file names
        citations = []
        for ref in resp.get("citations", []):
            for loc in ref.get("retrievedReferences", []):
                uri = loc.get("location", {}).get("s3Location", {}).get("uri", "")
                if uri:
                    citations.append(uri.split("/")[-1])
        if citations:
            answer += f"\n\n📎 Sources: {', '.join(set(citations))}"

        return {"text": answer, "chart": None}
    except Exception as e:
        return {"text": f"⚠️ Knowledge base error: {e}", "chart": None}

# ===============================================================
# 5. MANUS WORKFLOW ORCHESTRATOR
# ===============================================================
class AgentWorkflow:
    """
    Manus-style orchestrator with 3 routes:
      analytics         → structured pandas + matplotlib
      freeform_analytics → LLM-generated pandas code
      rag               → Amazon Bedrock Knowledge Base
    """
    def run(self, question: str, session_id: str) -> dict:
        parsed = parse_question(question, session_id)
        q_type = parsed.get("type", "rag")
        print(f"[workflow] type={q_type} | metric={parsed.get('metric')} | col={parsed.get('columns')} | grp={parsed.get('group_by')}")

        if q_type == "analytics":
            result = handle_analytics(parsed)
        elif q_type == "freeform_analytics":
            result = handle_freeform(question)
        else:
            result = ask_rag(question)

        # If analytics returned no chart but question wanted one → retry as freeform
        if q_type in ["analytics"] and wants_chart(question) and not result.get("chart"):
            print("[workflow] No chart from analytics → retrying as freeform")
            freeform_result = handle_freeform(question)
            if freeform_result.get("chart"):
                result = freeform_result
                q_type = "freeform_analytics"

        return {"route_task": result, "type": q_type, "parsed": parsed}

agent_workflow = AgentWorkflow()

# ===============================================================
# 6. FLASK
# ===============================================================
app = Flask(__name__, static_url_path="", static_folder="static")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/schema")
def schema():
    return jsonify({
        "columns": ALL_COLS,
        "numeric": NUMERIC_COLS,
        "categorical": CATEGORICAL_COLS,
        "rows": len(df),
        "sample": SAMPLE_ROWS
    })

@app.route("/ask", methods=["POST"])
def ask():
    body       = request.get_json()
    question   = (body.get("question") or "").strip()
    session_id = body.get("session_id") or str(uuid.uuid4())

    if not question:
        return jsonify({"error": "No question provided."})

    results      = agent_workflow.run(question=question, session_id=session_id)
    route_result = results.get("route_task", {})
    answer       = route_result.get("text", "No answer.")
    chart        = route_result.get("chart")
    q_type       = results.get("type", "rag")
    parsed       = results.get("parsed", {})

    memory_store.setdefault(session_id, []).append(
        {"question": question, "answer": answer[:300]}
    )

    return jsonify({
        "session_id": session_id,
        "answer":     answer,
        "chart":      chart,
        "category":   q_type,
        "intent":     parsed.get("intent", ""),
        "last_qa":    memory_store[session_id][-5:]
    })

@app.route("/clear", methods=["POST"])
def clear_session():
    sid = (request.get_json() or {}).get("session_id")
    if sid in memory_store:
        del memory_store[sid]
    return jsonify({"status": "cleared"})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
