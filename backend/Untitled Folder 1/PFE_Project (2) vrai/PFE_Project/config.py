"""
config.py
─────────
Single source of truth for all settings.
Loads everything from .env so no credentials are hardcoded.
"""
import os
from dotenv import load_dotenv

# Load .env file from the project root
load_dotenv()

# ── AWS ───────────────────────────────────────────────────────
AWS_REGION        = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY    = os.getenv("AWS_SECRET_ACCESS_KEY")

# ── Bedrock ───────────────────────────────────────────────────
BEDROCK_MODEL_ID  = "anthropic.claude-3-haiku-20240307-v1:0"
KNOWLEDGE_BASE_ID = os.getenv("KNOWLEDGE_BASE_ID")

# ── Paths ─────────────────────────────────────────────────────
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
KB_DIR       = os.path.join(BASE_DIR, "KnowledgeBase")
CHART_DIR    = os.path.join(BASE_DIR, "static", "charts")
REPORTS_DIR  = os.path.join(BASE_DIR, "static", "reports")
CSV_PATH     = os.path.join(KB_DIR, "Sales_Data.csv")

# Create folders if they don't exist
os.makedirs(CHART_DIR,   exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

# ── Chart style palette ───────────────────────────────────────
PALETTE = [
    "#4F8EF7", "#F76C5E", "#43C59E", "#F9A825",
    "#AB47BC", "#26C6DA", "#EF5350", "#66BB6A",
    "#FFA726", "#5C6BC0"
]