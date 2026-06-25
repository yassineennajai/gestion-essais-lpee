from flask import Flask, request, jsonify, render_template
import pandas as pd
import matplotlib.pyplot as plt
import uuid
import os
import boto3
import json
import re
from manus_tasks import agent_workflow

# ===============================
# CONFIG
# ===============================
REGION = "us-east-1"
KB_ID = "E4ZNPDMCPC"
MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"
CHART_DIR = "static/charts"
os.makedirs(CHART_DIR, exist_ok=True)

# ===============================
# CLIENTS
# ===============================
bedrock_runtime = boto3.client("bedrock-runtime", region_name=REGION)
agent_client = boto3.client("bedrock-agent-runtime", region_name=REGION)

# ===============================
# LOAD DATASET
# ===============================
df = pd.read_csv("Sales_Data.csv")
df["order_date"] = pd.to_datetime(df["order_date"])
df["order_year"] = df["order_date"].dt.year
df["order_month"] = df["order_date"].dt.month

# ===============================
# MEMORY STORE
# ===============================
memory_store = {}  # session_id -> list of {"question": ..., "answer": ...}

# ===============================
# 1️⃣ PARSE QUESTION
# ===============================
def parse_question_with_llm(question: str, session_id: str = None):
    # Include recent memory
    memory_context = ""
    if session_id and session_id in memory_store:
        memory_context = "Previous interactions:\n"
        for qa in memory_store[session_id][-5:]:
            memory_context += f"Q: {qa['question']}\nA: {qa['answer']}\n"

    prompt = f"""
    You are a data analyst. The dataframe is named df.
    {memory_context}
    Analyze this user question and return ONLY a valid JSON with:
    - type: "analytics" or "rag"
    - metric: sum | average | count | max | min | trend | top_n | null
    - columns: list of columns to aggregate
    - filters: dictionary of column_name -> value for filtering
    - group_by: list of columns for grouping (optional)
    - top_n: number of top items for top_n chart (optional)
    Question: {question}
    """

    try:
        response = bedrock_runtime.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 500,
                "messages": [{"role": "user", "content": prompt}]
            })
        )
        result = json.loads(response["body"].read())
        text = result["content"][0]["text"].strip()
        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return {"type": "rag"}
    except Exception:
        return {"type": "rag"}

# ===============================
# 2️⃣ LOCAL ANALYTICS + CHARTS
# ===============================
def handle_analytics(parsed: dict):
    metric = parsed.get("metric")
    columns = parsed.get("columns", ["sales"])
    filters = parsed.get("filters", {})
    group_by = parsed.get("group_by", [])
    top_n = parsed.get("top_n", 5)
    
    data = df.copy()
    col = columns[0]

    # Apply filters
    for f_col, f_val in filters.items():
        if f_col in data.columns:
            data = data[data[f_col] == f_val]

    if data.empty:
        return {"text": "No data found for the given filters.", "chart": None}

    chart_url = None
    result_text = ""

    # Top N chart
    if metric == "top_n" and group_by:
        top_data = data.groupby(group_by)[col].sum().sort_values(ascending=False).head(top_n)
        plt.figure(figsize=(8,4))
        top_data.plot(kind="bar")
        plt.title(f"Top {top_n} {', '.join(group_by)} by {col}")
        plt.ylabel(col)
        plt.xlabel(", ".join(group_by))
        filename = f"{uuid.uuid4().hex}.png"
        path = os.path.join(CHART_DIR, filename)
        plt.savefig(path)
        plt.close()
        chart_url = "/" + path
        result_text = f"Top {top_n} chart generated."

    # Trend chart
    elif metric == "trend":
        trend_data = data.groupby("order_date")[col].sum()
        plt.figure(figsize=(8,4))
        trend_data.plot(kind="line", marker="o")
        plt.title(f"{col} Trend")
        plt.xlabel("Date")
        plt.ylabel(col)
        filename = f"{uuid.uuid4().hex}.png"
        path = os.path.join(CHART_DIR, filename)
        plt.savefig(path)
        plt.close()
        chart_url = "/" + path
        result_text = "Trend chart generated."

    # Standard metrics
    elif metric in ["sum", "average", "count", "max", "min"]:
        if group_by:
            grouped = data.groupby(group_by)[col]
            if metric == "sum":
                result = grouped.sum().sort_values(ascending=False)
            elif metric == "average":
                result = grouped.mean().sort_values(ascending=False)
            elif metric == "count":
                result = grouped.count().sort_values(ascending=False)
            elif metric == "max":
                result = grouped.max().sort_values(ascending=False)
            elif metric == "min":
                result = grouped.min().sort_values(ascending=False)
            result_text = f"{metric.capitalize()} by {group_by}: {result.to_dict()}"
        else:
            if metric == "sum":
                result_text = f"Total {col} = {data[col].sum()}"
            elif metric == "average":
                result_text = f"Average {col} = {data[col].mean()}"
            elif metric == "count":
                result_text = f"Number of transactions = {data[col].count()}"
            elif metric == "max":
                result_text = f"Max {col} = {data[col].max()}"
            elif metric == "min":
                result_text = f"Min {col} = {data[col].min()}"
    else:
        result_text = "Metric not supported."

    return {"text": result_text, "chart": chart_url}

# ===============================
# 3️⃣ RAG FUNCTION
# ===============================
def ask_with_rag(question: str):
    try:
        response = agent_client.retrieve_and_generate(
            input={"text": question},
            retrieveAndGenerateConfiguration={
                "type": "KNOWLEDGE_BASE",
                "knowledgeBaseConfiguration": {
                    "knowledgeBaseId": KB_ID,
                    "modelArn": f"arn:aws:bedrock:{REGION}::foundation-model/{MODEL_ID}",
                    "retrievalConfiguration": {"vectorSearchConfiguration": {"numberOfResults": 5}}
                }
            }
        )
        return response.get("output", {}).get("text", "")
    except Exception as e:
        return f"Error calling RAG: {e}"

# ===============================
# 4️⃣ FLASK APP
# ===============================
app = Flask(__name__, static_url_path="", static_folder="static")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    question = data.get("question", "")
    session_id = data.get("session_id", str(uuid.uuid4()))

    if not question:
        return jsonify({"error": "No question provided."})

    # Run Manus workflow
    results = agent_workflow.run(question=question, session_id=session_id)

    # Extract results
    if isinstance(results, dict):
        answer = results.get("route_task", {}).get("text") or results.get("route_task")
        chart = results.get("route_task", {}).get("chart") if isinstance(results.get("route_task"), dict) else None
    else:
        answer = str(results)
        chart = None

    # Save to memory
    if session_id not in memory_store:
        memory_store[session_id] = []
    memory_store[session_id].append({"question": question, "answer": answer})

    last_qa = memory_store[session_id][-5:]

    return jsonify({
        "session_id": session_id,
        "answer": answer,
        "chart": chart,
        "last_qa": last_qa
    })
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)