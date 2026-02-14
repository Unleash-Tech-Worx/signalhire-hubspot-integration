from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

HUBSPOT_TOKEN = os.getenv("HUBSPOT_TOKEN")
SIGNALHIRE_API_KEY = os.getenv("SIGNALHIRE_API_KEY")

HUBSPOT_SEARCH_URL = "https://api.hubapi.com/crm/v3/objects/contacts/search"
HUBSPOT_CONTACT_URL = "https://api.hubapi.com/crm/v3/objects/contacts"
SIGNALHIRE_SEARCH_URL = "https://www.signalhire.com/api/v1/candidate/search"

HUBSPOT_HEADERS = {
    "Authorization": f"Bearer {HUBSPOT_TOKEN}",
    "Content-Type": "application/json"
}


# ---------------- HUBSPOT HELPERS ---------------- #

def find_contact_by_email(email):
    payload = {
        "filterGroups": [{
            "filters": [{
                "propertyName": "email",
                "operator": "EQ",
                "value": email
            }]
        }]
    }

    response = requests.post(
        HUBSPOT_SEARCH_URL,
        headers=HUBSPOT_HEADERS,
        json=payload
    )

    response.raise_for_status()
    results = response.json().get("results")

    if results:
        return results[0]["id"]
    return None


def create_or_update_contact(contact_data):
    email = contact_data["email"]
    existing_contact_id = find_contact_by_email(email)

    properties = {
        "email": email,
        "firstname": contact_data.get("firstname"),
        "lastname": contact_data.get("lastname"),
        "phone": contact_data.get("phone"),
        "jobtitle": contact_data.get("jobtitle")
    }

    if existing_contact_id:
        print("Updating contact:", email)
        update_url = f"{HUBSPOT_CONTACT_URL}/{existing_contact_id}"
        response = requests.patch(
            update_url,
            headers=HUBSPOT_HEADERS,
            json={"properties": properties}
        )
    else:
        print("Creating contact:", email)
        response = requests.post(
            HUBSPOT_CONTACT_URL,
            headers=HUBSPOT_HEADERS,
            json={"properties": properties}
        )

    print("HubSpot response:", response.status_code, response.text)


# ---------------- ROOT ---------------- #

@app.route("/", methods=["GET"])
def home():
    return "SignalHire → HubSpot integration is running!"


# ---------------- ENRICH (Called by HubSpot Workflow) ---------------- #

@app.route("/enrich", methods=["POST"])
def enrich():
    data = request.json
    print("Received from HubSpot workflow:", data)

    linkedin_url = data.get("linkedin_url")
    email = data.get("email")

    if not linkedin_url or not email:
        return jsonify({"error": "LinkedIn URL and Email required"}), 400

    headers = {
        "apikey": SIGNALHIRE_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "items": [linkedin_url],
        "callbackUrl": "https://signalhire-hubspot-integration.onrender.com/callback"
    }

    response = requests.post(
        SIGNALHIRE_SEARCH_URL,
        headers=headers,
        json=payload
    )

    print("SignalHire request status:", response.status_code)
    print("SignalHire response:", response.text)

    return jsonify({"status": "Sent to SignalHire"}), 200


# ---------------- CALLBACK (Called by SignalHire) ---------------- #

@app.route("/callback", methods=["POST"])
def signalhire_callback():
    data = request.json
    print("Received from SignalHire:", data)

    if not data:
        return jsonify({"error": "No data received"}), 400

    for item in data:
        if item.get("status") == "success":
            candidate = item.get("candidate", {})

            contacts = candidate.get("contacts", [])

            email = None
            phone = None

            for c in contacts:
                if c.get("type") == "email":
                    email = c.get("value")
                if c.get("type") == "phone":
                    phone = c.get("value")

            full_name = candidate.get("fullName", "")
            first_name = full_name.split()[0] if full_name else ""
            last_name = full_name.split()[-1] if full_name else ""

            contact_data = {
                "email": email,
                "firstname": first_name,
                "lastname": last_name,
                "phone": phone,
                "jobtitle": candidate.get("headLine", "")
            }

            create_or_update_contact(contact_data)

    return jsonify({"status": "Callback processed"}), 200


# ---------------- RUN ---------------- #

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
