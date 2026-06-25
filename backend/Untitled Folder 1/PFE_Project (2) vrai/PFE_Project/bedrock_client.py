"""
bedrock_client.py
─────────────────
All communication with AWS Bedrock:
  - invoke_llm()      → sends a prompt, gets text back
  - parse_question()  → classifies user question into a routing decision
  - ask_rag()         → searches the Knowledge Base and generates an answer
"""
import json
import re
import boto3

from config import (
    AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_KEY,
    BEDROCK_MODEL_ID, KNOWLEDGE_BASE_ID
)

# ── AWS clients ───────────────────────────────────────────────
_session = boto3.Session(
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_KEY,
)
bedrock_runtime = _session.client("bedrock-runtime")
bedrock_agent   = _session.client("bedrock-agent-runtime")


# ── 1. Raw LLM call ───────────────────────────────────────────
def invoke_llm(prompt: str, max_tokens: int = 800) -> str:
    """
    Send a plain text prompt to Claude Haiku.
    Returns the response text as a string.
    """
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}]
    }
    resp = bedrock_runtime.invoke_model(
        modelId=BEDROCK_MODEL_ID,
        body=json.dumps(body)
    )
    return json.loads(resp["body"].read())["content"][0]["text"].strip()


# ── 2. Question classifier ────────────────────────────────────
def parse_question(question: str, df_meta: dict, memory: list) -> dict:
    """
    Ask Bedrock to classify the user's question and return a routing
    decision as a JSON dict.

    df_meta keys expected: all_cols, numeric_cols, categorical_cols,
                           date_cols, sample_rows
    memory: list of last 3 {"question", "answer"} dicts
    """
    # Format recent conversation for context
    mem_text = "None"
    if memory:
        mem_text = "\n".join(
            f"Q: {m['question']}\nA: {str(m['answer'])[:120]}"
            for m in memory[-3:]
        )

    chart_keywords = [
        "show", "visualize", "chart", "graph", "plot", "display",
        "bar", "line", "trend", "top", "compare", "distribution",
        "evolution", "monthly", "yearly", "over time", "pie",
        "histogram", "visual", "breakdown"
    ]
    wants_chart = any(kw in question.lower() for kw in chart_keywords)

    prompt = f"""You are a data analyst assistant. You have access to a pandas DataFrame.

DataFrame info:
- All columns      : {df_meta['all_cols']}
- Numeric columns  : {df_meta['numeric_cols']}
- Categorical cols : {df_meta['categorical_cols']}
- Date columns     : {df_meta['date_cols']}
- Sample rows      : {json.dumps(df_meta['sample_rows'])}

Recent conversation:
{mem_text}

User question: "{question}"
{"⚠️ The user WANTS a chart or visual." if wants_chart else ""}

Return ONLY a JSON object. No markdown. No explanation.

{{
  "type": "analytics",
  "intent": "short description",
  "metric": "top_n",
  "columns": ["sales"],
  "filters": {{}},
  "group_by": ["product_name"],
  "top_n": 5,
  "chart_type": "bar",
  "time_period": null
}}

Rules:
- "type": "analytics" (data/charts) | "rag" (company info, FAQ, policies) | "report" (user asks for a report/summary document)
- "metric": sum | average | count | max | min | trend | top_n | distribution | correlation
- "columns"  → ONLY from: {df_meta['numeric_cols']}
- "group_by" → ONLY from: {df_meta['categorical_cols']}
- "chart_type": bar | line | pie | hist | null
- trend/over time/monthly → metric=trend, chart_type=line
- top/best/ranking       → metric=top_n, chart_type=bar
- distribution/histogram → metric=distribution, chart_type=hist
- pie/share/proportion   → chart_type=pie
- "time_period": monthly | yearly | daily | null
- report/summary/export  → type=report
"""
    try:
        raw = invoke_llm(prompt, max_tokens=600)
        raw = re.sub(r"```json|```", "", raw).strip()
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            raise ValueError("No JSON in LLM response")
        return json.loads(match.group())

    except Exception as e:
        print(f"[parse_question ERROR] {e}")
        # Safe fallback
        if wants_chart:
            return {"type": "analytics", "metric": "top_n",
                    "chart_type": "bar", "top_n": 5,
                    "columns": [], "group_by": [], "filters": {}}
        return {"type": "rag"}


# ── 3. RAG — Knowledge Base ───────────────────────────────────
def ask_rag(question: str) -> dict:
    """
    Search the Bedrock Knowledge Base and generate an answer.
    Returns {"text": "...", "chart": None}
    """
    try:
        resp = bedrock_agent.retrieve_and_generate(
            input={"text": question},
            retrieveAndGenerateConfiguration={
                "type": "KNOWLEDGE_BASE",
                "knowledgeBaseConfiguration": {
                    "knowledgeBaseId": KNOWLEDGE_BASE_ID,
                    "modelArn": (
                        f"arn:aws:bedrock:{AWS_REGION}::"
                        f"foundation-model/{BEDROCK_MODEL_ID}"
                    ),
                    "retrievalConfiguration": {
                        "vectorSearchConfiguration": {"numberOfResults": 5}
                    }
                }
            }
        )

        answer = resp.get("output", {}).get("text", "")
        if not answer:
            answer = "I couldn't find an answer in the knowledge base."

        # Collect source file names
        sources = set()
        for ref in resp.get("citations", []):
            for loc in ref.get("retrievedReferences", []):
                uri = loc.get("location", {}).get("s3Location", {}).get("uri", "")
                if uri:
                    sources.add(uri.split("/")[-1])
        if sources:
            answer += f"\n\n📎 Sources: {', '.join(sources)}"

        return {"text": answer, "chart": None}

    except Exception as e:
        return {"text": f"⚠️ Knowledge base error: {e}", "chart": None}