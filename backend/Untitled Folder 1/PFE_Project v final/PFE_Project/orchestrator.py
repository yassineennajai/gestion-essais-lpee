"""
orchestrator.py
───────────────
Classe AgentWorkflow — le cerveau de l'application.

Il reçoit une question de l'utilisateur, décide quoi faire,
appelle l'outil approprié et renvoie un résultat unifié.

Routes possibles :
  analytics → analytics.py  (questions sur les données + graphiques)
  rag       → bedrock_client.py (FAQ, politiques, documents KB)
  report    → report_generator.py (rapport PDF complet)
"""
import uuid

from bedrock_client import parse_question, ask_rag, detect_language
from analytics import (
    handle_analytics, best_num_col, best_cat_col,
    NUMERIC_COLS, CATEGORICAL_COLS, DATE_COLS, ALL_COLS, SAMPLE_ROWS
)
from report_generator import generate_report

# ── Mots-clés pour détecter si l'utilisateur veut un graphique ──
_CHART_KW = {
    # Anglais
    "show", "visualize", "chart", "graph", "plot", "display", "draw",
    "bar", "line", "trend", "top", "compare", "distribution",
    "breakdown", "evolution", "monthly", "yearly", "over time",
    "pie", "histogram", "visual",
    # Français
    "montre", "affiche", "graphique", "histogramme", "camembert",
    "tendance", "evolution", "mensuel", "annuel", "comparer",
    "visualise", "courbe", "diagramme", "classement"
}

# ── Mots-clés pour détecter une salutation ──
_GREET_KW = {
    "hi", "hello", "hey",
    "bonjour", "salut", "bonsoir", "bonne journée",
    "good morning", "good afternoon"
}

# ── Mots-clés pour détecter si l'utilisateur veut un rapport ──
_REPORT_KW = {
    "report", "summary", "export", "pdf", "document",
    "generate report", "make a report",
    "rapport", "résumé", "genere", "génère", "générer", "faire un rapport"
}

# ── Messages de bienvenue selon la langue ──
_GREETING_FR = (
    "👋 Bonjour ! Je suis NexusAI, votre agent d'intelligence commerciale.\n\n"
    "Je peux vous aider avec :\n"
    "  📊 Analytique — tendances, classements, totaux, graphiques\n"
    "  📚 Base de connaissances — politiques, FAQ de l'entreprise\n"
    "  📄 Rapports — rapports PDF complets\n\n"
    "Que souhaitez-vous savoir ?"
)

_GREETING_EN = (
    "👋 Hello! I'm NexusAI, your Sales Intelligence Agent.\n\n"
    "I can help you with:\n"
    "  📊 Analytics — trends, rankings, totals, charts\n"
    "  📚 Knowledge Base — company policies, FAQs\n"
    "  📄 Reports — full PDF sales reports\n\n"
    "What would you like to know?"
)

# ── Fonctions internes de détection ──
def _wants_chart(q: str) -> bool:
    """Retourne True si la question contient un mot-clé de graphique"""
    return any(kw in q.lower() for kw in _CHART_KW)

def _is_greeting(q: str) -> bool:
    """Retourne True si la question est une salutation"""
    q_lower = q.lower().strip()
    return any(q_lower.startswith(kw) for kw in _GREET_KW)

def _wants_report(q: str) -> bool:
    """Retourne True si la question demande un rapport"""
    return any(kw in q.lower() for kw in _REPORT_KW)

# ── Métadonnées DataFrame envoyées à Bedrock pour classification ──
_DF_META = {
    "all_cols":        ALL_COLS,
    "numeric_cols":    NUMERIC_COLS,
    "categorical_cols": CATEGORICAL_COLS,
    "date_cols":       DATE_COLS,
    "sample_rows":     SAMPLE_ROWS,
}

# ── Classe principale : orchestrateur stateless ──
class AgentWorkflow:
    """
    Stateless orchestrator — toute la mémoire de session
    est gérée dans memory_store (app.py).
    """

    def run(self, question: str, memory: list) -> dict:
        """
        Traite une question et retourne un résultat unifié.
        
        Parameters
        ----------
        question : str — question de l'utilisateur
        memory   : list — historique des N dernières Q/A

        Returns
        -------
        dict avec clés :
          text       — réponse textuelle
          chart      — URL du graphique ou None
          report_url — URL PDF ou None
          category   — "analytics" | "rag" | "report" | "greeting"
          intent     — description courte de l'intention
          lang       — "fr" ou "en"
        """

        # ── 0. Détecter la langue ──
        lang = detect_language(question)
        print(f"[orchestrator] lang={lang}")

        # ── 1. Salutations ──
        if _is_greeting(question):
            return {
                "text": _GREETING_FR if lang == "fr" else _GREETING_EN,
                "chart": None,
                "report_url": None,
                "category": "greeting",
                "intent": "greeting",
                "lang": lang
            }

        # ── 2. Shortcut rapport ──
        if _wants_report(question):
            print("[orchestrator] route=report")
            result = generate_report(question=question, lang=lang)
            intent = "Générer un rapport PDF complet des ventes" if lang=="fr" else "Generate full PDF sales report"
            return {**result, "category": "report", "intent": intent, "lang": lang}

        # ── 3. Classification via Bedrock ──
        parsed = parse_question(question, _DF_META, memory, lang=lang)
        q_type = parsed.get("type", "rag")  # type par défaut = rag
        intent = parsed.get("intent", "")

        # Validation des colonnes
        cols = parsed.get("columns") or []
        parsed["columns"] = [c for c in cols if c in NUMERIC_COLS] or [best_num_col()]

        grps = parsed.get("group_by") or []
        parsed["group_by"] = [g for g in grps if g in ALL_COLS] or []

        if parsed.get("metric") == "top_n" and not parsed["group_by"]:
            parsed["group_by"] = [best_cat_col()]

        # Choix automatique de type de graphique si besoin
        if (parsed.get("metric") in ("sum", "average", "count", "max", "min")
                and parsed["group_by"] and not parsed.get("chart_type")):
            parsed["chart_type"] = "bar"

        # Si utilisateur veut un graphique mais type = rag
        if _wants_chart(question) and q_type == "rag":
            q_type               = "analytics"
            parsed["type"]       = "analytics"
            parsed["metric"]     = parsed.get("metric") or "top_n"
            parsed["chart_type"] = parsed.get("chart_type") or "bar"

        # Si type = report (après classification Bedrock)
        if q_type == "report":
            result = generate_report(question=question, lang=lang)
            return {**result, "category": "report", "intent": intent, "lang": lang}

        print(f"[orchestrator] route={q_type} | metric={parsed.get('metric')} "
              f"| col={parsed.get('columns')} | grp={parsed.get('group_by')}")

        # ── 4. Exécution ──
        if q_type == "analytics":
            result = handle_analytics(parsed, lang=lang)
        else:
            result = ask_rag(question, lang=lang)

        return {**result, "category": q_type, "intent": intent,
                "report_url": None, "lang": lang}

# ── Singleton — utilisé par app.py ou lambda_function.py ──
agent = AgentWorkflow()
