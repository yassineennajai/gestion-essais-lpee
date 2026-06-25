"""
orchestrator.py
───────────────
The AgentWorkflow class — the brain of the application.

It receives a user question, decides what to do, calls the right
tool, and returns a unified result dict.

Routes:
  analytics → analytics.py  (data questions + charts)
  rag       → bedrock_client.py (FAQ, policies, KB docs)
  report    → report_generator.py (full PDF report)
"""
import uuid

from bedrock_client import parse_question, ask_rag
from analytics import (
    handle_analytics, best_num_col, best_cat_col,
    NUMERIC_COLS, CATEGORICAL_COLS, DATE_COLS, ALL_COLS, SAMPLE_ROWS
)
from report_generator import generate_report

# Keywords that indicate the user explicitly wants a chart
_CHART_KW = {
    "show", "visualize", "chart", "graph", "plot", "display", "draw",
    "bar", "line", "trend", "top", "compare", "distribution",
    "breakdown", "evolution", "monthly", "yearly", "over time",
    "pie", "histogram", "visual"
}

# Keywords that indicate the user wants a greetings response
_GREET_KW = {"hi", "hello", "hey", "bonjour", "salut", "bonsoir", "good morning", "good afternoon"}

# Keywords that indicate the user wants a report
_REPORT_KW = {"report", "summary", "export", "pdf", "document", "generate report", "make a report"}


def _wants_chart(q: str) -> bool:
    return any(kw in q.lower() for kw in _CHART_KW)

def _is_greeting(q: str) -> bool:
    q_lower = q.lower().strip()
    return any(q_lower.startswith(kw) for kw in _GREET_KW)

def _wants_report(q: str) -> bool:
    return any(kw in q.lower() for kw in _REPORT_KW)


# ── DataFrame metadata passed to Bedrock for classification ──
_DF_META = {
    "all_cols":        ALL_COLS,
    "numeric_cols":    NUMERIC_COLS,
    "categorical_cols": CATEGORICAL_COLS,
    "date_cols":       DATE_COLS,
    "sample_rows":     SAMPLE_ROWS,
}


class AgentWorkflow:
    """
    Stateless orchestrator — all session state lives in memory_store (app.py).
    Call .run(question, memory) to get a result.
    """

    def run(self, question: str, memory: list) -> dict:
        """
        Parameters
        ----------
        question : str   — the user's raw question
        memory   : list  — last N {"question", "answer"} dicts for context

        Returns
        -------
        dict with keys:
          text        — string answer
          chart       — chart URL or None
          report_url  — PDF URL or None (only for report type)
          category    — "analytics" | "rag" | "report" | "greeting"
          intent      — short description of what was understood
        """

        # ── 1. Greetings: handle locally, no LLM needed ───────
        if _is_greeting(question):
            return {
                "text": (
                    "👋 Hello! I'm NexusAI, your Sales Intelligence Agent.\n\n"
                    "I can help you with:\n"
                    "  📊 Analytics — trends, rankings, totals, charts\n"
                    "  📚 Knowledge Base — company policies, FAQs\n"
                    "  📄 Reports — full PDF sales reports\n\n"
                    "What would you like to know?"
                ),
                "chart": None, "report_url": None,
                "category": "greeting", "intent": "greeting"
            }

        # ── 2. Report shortcut: detect before calling LLM ─────
        if _wants_report(question):
            print("[orchestrator] route=report")
            result = generate_report()
            return {**result, "category": "report",
                    "intent": "Generate full PDF sales report"}

        # ── 3. Classify via Bedrock ───────────────────────────
        parsed = parse_question(question, _DF_META, memory)
        q_type = parsed.get("type", "rag")
        intent = parsed.get("intent", "")

        # Safety: validate columns returned by LLM
        cols = parsed.get("columns") or []
        parsed["columns"] = [c for c in cols if c in NUMERIC_COLS] or [best_num_col()]

        grps = parsed.get("group_by") or []
        parsed["group_by"] = [g for g in grps if g in ALL_COLS] or []

        # Safety: top_n without group_by → assign best cat column
        if parsed.get("metric") == "top_n" and not parsed["group_by"]:
            parsed["group_by"] = [best_cat_col()]

        # Safety: grouped aggregations should get a chart
        if (parsed.get("metric") in ("sum", "average", "count", "max", "min")
                and parsed["group_by"] and not parsed.get("chart_type")):
            parsed["chart_type"] = "bar"

        # Safety: override to analytics if chart keyword detected but LLM said rag
        if _wants_chart(question) and q_type == "rag":
            q_type             = "analytics"
            parsed["type"]     = "analytics"
            parsed["metric"]   = parsed.get("metric") or "top_n"
            parsed["chart_type"] = parsed.get("chart_type") or "bar"

        # Safety: if LLM returned "report" type, honour it
        if q_type == "report":
            result = generate_report()
            return {**result, "category": "report", "intent": intent}

        print(f"[orchestrator] route={q_type} | metric={parsed.get('metric')} "
              f"| col={parsed.get('columns')} | grp={parsed.get('group_by')}")

        # ── 4. Execute ────────────────────────────────────────
        if q_type == "analytics":
            result = handle_analytics(parsed)
        else:
            result = ask_rag(question)

        return {**result, "category": q_type, "intent": intent, "report_url": None}


# Singleton — imported by app.py and lambda_function.py
agent = AgentWorkflow()