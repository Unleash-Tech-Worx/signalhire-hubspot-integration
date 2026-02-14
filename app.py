from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv
import logging

load_dotenv()

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

HUBSPOT_TOKEN = os.getenv("HUBSPOT_TOKEN")
SIGNALHIRE_API_KEY = os.getenv("SIGNALHIRE_API_KEY")

HUBSPOT_SEARCH_URL = "https://api.hubapi.com/crm/v3/objects/contacts/search"
HUBSPOT_CONTACT_URL = "https://api.hubapi.com/crm/v3/objects/contacts"

HEADERS = {
    "Authorization": f"Bearer {HUBSPOT_TOKEN}",
    "Content-Type": "application/json"
}

def find_contact_by_email(email):
    if not email:
        return None
    payload = {
        "filterGroups": [{
            "filters": [{
                "propertyName": "email",
                "operator": "EQ",
                "value": email
            }]
        }]
    }
    try:
        response = requests.post(HUBSPOT_SEARCH_URL, headers=HEADERS, json=payload)
        response.raise_for_status()
        results = response.json().get("results")
        if results:
            return results[0]["id"]
    except Exception as e:
        logging.error(f"Error searching contact: {e}")
    return None

def create_or_update_contact(contact_data):
    email = contact_data.get("email")
    if not email:
        logging.warning("No email provided, skipping contact creation.")
        return

    existing_contact_id = find_contact_by_email(email)

    properties = {
        "email": email,
        "firstname": contact_data.get("firstname", ""),
        "lastname": contact_data.get("lastname", ""),
        "phone": contact_data.get("phone", ""),
        "jobtitle": contact_data.get("jobtitle", "")
    }

    try:
        if existing_contact_id:
            update_url = f"{HUBSPOT_CONTACT_URL}/{existing_contact_id}"
            response = requests.patch(update_url, headers=HEADERS, json={"properties": properties})
        else:
            response = requests.post(HUBSPOT_CONTACT_URL, headers=HEADERS, json={"properties": properties})

        logging.info(f"HubSpot response: {response.status_code} {response.text}")
    except Exception as e:
        logging.error(f"Error creating/updating contact: {e}")

@app.route("/callback", methods=["POST"])
def signalhire_callback():
    data = request.get_json(force=True)  # ensure JSON is parsed even if Content-Type header is missing
    logging.info(f"Received callback data: {data}")

    if not isinstance(data, list):
        return jsonify({"status": "invalid data"}), 400

    for item in data:
        if item.get("status") == "success":
            candidate = item.get("candidate", {})
            email = None
            phone = None

            for c in candidate.get("contacts", []):
                if c.get("type") == "email" and not email:
                    email = c.get("value")
                elif c.get("type") == "phone" and not phone:
                    phone = c.get("value")

            full_name = candidate.get("fullName", "Unknown Unknown")
            firstname = full_name.split()[0] if full_name else ""
            lastname = full_name.split()[-1] if full_name else ""

            contact_data = {
                "email": email,
                "firstname": firstname,
                "lastname": lastname,
                "phone": phone,
                "jobtitle": candidate.get("headLine", "")
            }

            create_or_update_contact(contact_data)

    return jsonify({"status": "received"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

