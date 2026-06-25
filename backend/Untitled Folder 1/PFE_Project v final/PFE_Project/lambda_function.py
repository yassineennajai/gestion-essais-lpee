import json
import uuid
from orchestrator import agent
from analytics import ALL_COLS, NUMERIC_COLS, CATEGORICAL_COLS, df, SAMPLE_ROWS

# ── In-memory session store ────────────────────────────────────
# Note: Lambda instances can be recycled, so memory resets between
# cold starts. For persistence, swap this with DynamoDB or ElastiCache.
memory_store: dict = {}


# ── Response helper ───────────────────────────────────────────
def _response(status: int, body: dict) -> dict:
    """Format a response for AWS API Gateway."""
    return {
        "statusCode": status,
        "headers": {
            "Content-Type":                "application/json",
            "Access-Control-Allow-Origin": "*",       # CORS
        },
        "body": json.dumps(body),
    }


# ── Main handler ──────────────────────────────────────────────
def lambda_handler(event: dict, context) -> dict:
    """
    Entry point called by AWS Lambda.

    event keys used:
      path            → route (e.g. "/ask")
      httpMethod      → GET | POST
      body            → JSON string (for POST requests)
      queryStringParameters → URL params (not used yet)
    """
    path   = event.get("path", "/ask")
    method = event.get("httpMethod", "POST").upper()

    # Parse body for POST requests
    body = {}
    if method == "POST" and event.get("body"):
        try:
            body = json.loads(event["body"])
        except Exception:
            return _response(400, {"error": "Invalid JSON body"})

    # ── POST /ask ─────────────────────────────────────────────
    if path == "/ask" and method == "POST":
        try:
            question   = (body.get("question") or "").strip()
            session_id = body.get("session_id") or str(uuid.uuid4())

            if not question:
                return _response(400, {"error": "No question provided."})

            memory = memory_store.get(session_id, [])
            result = agent.run(question=question, memory=memory)

            memory_store.setdefault(session_id, []).append({
                "question": question,
                "answer":   result.get("text", "")[:300]
            })
            memory_store[session_id] = memory_store[session_id][-10:]

            return _response(200, {
                "session_id": session_id,
                "answer":     result.get("text", "No answer."),
                "chart":      result.get("chart"),
                "report_url": result.get("report_url"),
                "category":   result.get("category", "rag"),
                "intent":     result.get("intent", ""),
                "last_qa":    memory_store[session_id][-5:],
            })

        except Exception as e:
            print(f"[lambda /ask ERROR] {e}")
            return _response(500, {"error": str(e), "answer": f"⚠️ Error: {e}"})

    # ── GET /schema ───────────────────────────────────────────
    if path == "/schema" and method == "GET":
        return _response(200, {
            "columns":     ALL_COLS,
            "numeric":     NUMERIC_COLS,
            "categorical": CATEGORICAL_COLS,
            "rows":        len(df),
            "sample":      SAMPLE_ROWS,
        })

    # ── GET /report ───────────────────────────────────────────
    if path == "/report" and method == "GET":
        try:
            from report_generator import generate_report
            result = generate_report()
            return _response(200, result)
        except Exception as e:
            return _response(500, {"error": str(e)})

    # ── POST /clear ───────────────────────────────────────────
    if path == "/clear" and method == "POST":
        sid = body.get("session_id")
        memory_store.pop(sid, None)
        return _response(200, {"status": "cleared"})

    # ── 404 fallback ──────────────────────────────────────────
    return _response(404, {"error": f"Route '{path}' not found."})