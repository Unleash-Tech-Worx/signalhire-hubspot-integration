from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return "Hello, your integration is live!"

@app.route("/signalhire-callback", methods=["POST"])
def signalhire_callback():
    data = request.json
    print("Received callback from SignalHire:", data)
    return jsonify({"status": "received"}), 200
