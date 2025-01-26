from flask import Flask, render_template, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/message")
def get_message():
    return jsonify(message="Hello, World!")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
