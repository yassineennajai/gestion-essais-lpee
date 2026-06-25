from flask import Flask, request, jsonify, render_template
from agents.orchestrator import  SuperOrchestrator
from services.s3_loader import load_data
import logging

# =====================================================
# CONFIG LOGGING
# =====================================================
logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

logger = logging.getLogger(__name__)

# =====================================================
# INIT APP
# =====================================================
app = Flask(__name__)

logger.info("Application starting...")

try:
    logger.info("Loading dataset from S3...")
    DATA_DF = load_data()
    logger.info("Dataset loaded successfully.")
except Exception as e:
    logger.error(f"Error loading dataset: {e}")
    DATA_DF = {}

orchestrator = SuperOrchestrator(DATA_DF)

# =====================================================
# ROUTES
# =====================================================
@app.route("/")
def home():
    logger.info("Home page accessed.")
    return render_template("index.html")

@app.route("/agent", methods=["POST"])
def run_agent():
    try:
        user_msg = request.json.get("message")
        logger.info(f"User message received: {user_msg}")

        if not user_msg:
            logger.warning("Empty message received.")
            return jsonify({"reply": "Message vide."})

        response = orchestrator.route(user_msg)
        logger.info("Response generated successfully.")

        return jsonify({"reply": response})

    except Exception as e:
        logger.error(f"Error in /agent route: {e}")
        return jsonify({"reply": "Une erreur interne est survenue."})

# =====================================================
if __name__ == "__main__":
    logger.info("Starting Flask server...")
    app.run(debug=False)