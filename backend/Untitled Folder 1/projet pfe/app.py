from flask import Flask, render_template, request, jsonify
from bedrock_client import ask_claude
from s3_loader import load_dataset

app = Flask(__name__)

# تحميل الداتا مرة وحدة ملي كيبدأ السيرفر
DATA_CONTEXT = load_dataset()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():

    user_msg = request.json["message"]

    prompt = f"""
    انت مساعد شركة.
    جاوب غير باستعمال المعلومات التالية:

    {DATA_CONTEXT}

    السؤال:
    {user_msg}
    """

    answer = ask_claude(prompt)

    return jsonify({"reply": answer})


if __name__ == "__main__":
    app.run(debug=True)
