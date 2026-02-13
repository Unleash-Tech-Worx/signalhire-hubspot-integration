from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

HUBSPOT_TOKEN = os.getenv("HUBSPOT_TOKEN")

hubspot_headers = {
    "Authorization": f"Bearer {HUBSPOT_TOKEN}",
    "Content-Type": "application/json"
}

HUBSPOT_CONTACT_URL = "https://api.hubapi.com/crm/v3/objects/contacts"


@app.route("/signalhire-callback", methods=["POST"])
def receive_signalhire_data():
    data = request.json
    print("Received from SignalHire:", data)

    # 🔥 Extract useful info (adjust based on real callback structure)
    person = data.get("profiles", [{}])[0]

    contact_data = {
        "email": person.get("email"),
        "firstname": person.get("firstName"),
        "lastname": person.get("lastName"),
        "phone": person.get("phone"),
        "jobtitle": person.get("position")
    }

    # Send to HubSpot
    response = requests.post(
        HUBSPOT_CONTACT_URL,
        headers=hubspot_headers,
        json={"properties": contact_data}
    )

    print("HubSpot Response:", response.status_code, response.text)

    return jsonify({"status": "received"}), 200


if __name__ == "__main__":
    app.run(port=5000)
