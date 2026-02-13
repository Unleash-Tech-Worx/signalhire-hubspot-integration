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

headers = {
    "Authorization": f"Bearer {HUBSPOT_TOKEN}",
    "Content-Type": "application/json"
}

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

    response = requests.post(HUBSPOT_SEARCH_URL, headers=headers, json=payload)
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
        update_url = f"{HUBSPOT_CONTACT_URL}/{existing_contact_id}"
        response = requests.patch(update_url, headers=headers, json={"properties": properties})
    else:
        response = requests.post(HUBSPOT_CONTACT_URL, headers=headers, json={"properties": properties})

@app.route("/callback", methods=["POST"])
def signalhire_callback():
    data = request.json
    for item in data:
        if item.get("status") == "success":
            candidate = item.get("candidate")
            contact_data = {
                "email": candidate["contacts"][1]["value"],  # example: pick work email
                "firstname": candidate["fullName"].split()[0],
                "lastname": candidate["fullName"].split()[-1],
                "phone": candidate["contacts"][0]["value"],  # example: pick work phone
                "jobtitle": candidate.get("headLine", "")
            }
            create_or_update_contact(contact_data)
    return jsonify({"status": "received"}), 200

if __name__ == "__main__":
    app.run(debug=True)
