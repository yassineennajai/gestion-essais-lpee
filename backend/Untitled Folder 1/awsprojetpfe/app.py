from flask import Flask, render_template

app = Flask(__name__)

# Route الرئيسية
@app.route("/")
def home():
    return render_template("index.html")  # اسم الملف HTML

if __name__ == "__main__":
    app.run(debug=True)
