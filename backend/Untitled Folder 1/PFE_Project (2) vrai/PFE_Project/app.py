"""
app.py
──────
Flask entry point — only routing and HTTP logic here.
All intelligence lives in orchestrator.py.
"""
import uuid
from flask import Flask, request, jsonify, render_template, send_from_directory

from orchestrator import agent
from analytics import ALL_COLS, NUMERIC_COLS, CATEGORICAL_COLS, df, SAMPLE_ROWS
from config import BASE_DIR

# ── App setup ─────────────────────────────────────────────────
app = Flask(__name__,
            template_folder="templates",
            static_folder="static",
            static_url_path="/static")

# ── In-memory session store ───────────────────────────────────
# { session_id: [{"question": ..., "answer": ...}, ...] }
memory_store: dict = {}


# ── Routes ────────────────────────────────────────────────────

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/schema")
def schema():
    """Return dataset column metadata for the frontend schema panel."""
    return jsonify({
        "columns":     ALL_COLS,
        "numeric":     NUMERIC_COLS,
        "categorical": CATEGORICAL_COLS,
        "rows":        len(df),
        "sample":      SAMPLE_ROWS,
    })


@app.route("/ask", methods=["POST"])
def ask():
    """Main chat endpoint."""
    try:
        body       = request.get_json() or {}
        question   = (body.get("question") or "").strip()
        session_id = body.get("session_id") or str(uuid.uuid4())

        if not question:
            return jsonify({"error": "No question provided."}), 400

        # Retrieve session memory
        memory = memory_store.get(session_id, [])

        # Run the orchestrator
        result = agent.run(question=question, memory=memory)

        # Save to memory (keep last 10 turns)
        memory_store.setdefault(session_id, []).append({
            "question": question,
            "answer":   result.get("text", "")[:300]
        })
        memory_store[session_id] = memory_store[session_id][-10:]

        return jsonify({
            "session_id": session_id,
            "answer":     result.get("text", "No answer."),
            "chart":      result.get("chart"),
            "report_url": result.get("report_url"),
            "category":   result.get("category", "rag"),
            "intent":     result.get("intent", ""),
            "last_qa":    memory_store[session_id][-5:],
        })

    except Exception as e:
        print(f"[/ask ERROR] {e}")
        return jsonify({"error": str(e), "answer": f"⚠️ Server error: {e}"}), 500


@app.route("/report")
def download_report():
    """Trigger a new PDF report generation."""
    from report_generator import generate_report
    result = generate_report()
    return jsonify(result)


@app.route("/clear", methods=["POST"])
def clear_session():
    """Clear a session's memory."""
    sid = (request.get_json() or {}).get("session_id")
    memory_store.pop(sid, None)
    return jsonify({"status": "cleared"})


# ── Run ───────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)