from flask import Flask, request, jsonify
from bedrock_client import ask_general, ask_company_data

app = Flask(__name__)

# ================= GENERAL TOOL =================
@app.route('/general', methods=['POST'])
def general():
    data = request.json
    message = data.get("message", "")
    result = ask_general(message)
    return jsonify({"result": result})


# ================= COMPANY DATA TOOL =================
@app.route('/company-data', methods=['POST'])
def company_data():
    data = request.json
    message = data.get("message", "")
    result = ask_company_data(message)
    return jsonify({"result": result})


# ================= REPORT TOOL =================
@app.route('/report', methods=['POST'])
def report():
    data = request.json
    message = data.get("message", "")
    prompt = f"Generate a professional enterprise report:\n{message}"
    result = ask_general(prompt)
    return jsonify({"result": result})


# ================= HEALTH =================
@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "running"})


if __name__ == '__main__':
    print("🚀 AI Tools API Running on http://localhost:5000")
    app.run(debug=True, port=5000)