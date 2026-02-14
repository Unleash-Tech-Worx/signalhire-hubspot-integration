import requests
import os
from dotenv import load_dotenv

load_dotenv()

HUBSPOT_TOKEN = os.getenv("HUBSPOT_TOKEN")
SIGNALHIRE_API_KEY = os.getenv("SIGNALHIRE_API_KEY")

HUBSPOT_SEARCH_URL = "https://api.hubapi.com/crm/v3/objects/contacts/search"
HUBSPOT_CONTACT_URL = "https://api.hubapi.com/crm/v3/objects/contacts"

HUBSPOT_HEADERS = {
    "Authorization": f"Bearer {HUBSPOT_TOKEN}",
    "Content-Type": "application/json"
}

SIGNALHIRE_URL = "https://www.signalhire.com/api/v1/candidate/search"


# ---------------- HUBSPOT FUNCTIONS ---------------- #

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
        print("Contact exists. Updating...")
        update_url = f"{HUBSPOT_CONTACT_URL}/{existing_contact_id}"
        response = requests.patch(
            update_url,
            headers=HUBSPOT_HEADERS,
            json={"properties": properties}
        )
    else:
        print("Contact not found. Creating...")
        response = requests.post(
            HUBSPOT_CONTACT_URL,
            headers=HUBSPOT_HEADERS,
            json={"properties": properties}
        )

    print("HubSpot Status Code:", response.status_code)
    print(response.json())


# ---------------- SIGNALHIRE FUNCTION ---------------- #

def send_linkedin_to_signalhire(linkedin_url):
    url = "https://www.signalhire.com/api/v1/candidate/search"

    headers = {
        "apikey": SIGNALHIRE_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "items": [linkedin_url],
        "callbackUrl": "https://signalhire-hubspot-integration.onrender.com/signalhire-callback"
    }

    response = requests.post(url, headers=headers, json=payload)

    print("SignalHire Status:", response.status_code)
    print("SignalHire Response:", response.text)


# -------------------------------
# MAIN EXECUTION
# -------------------------------

if __name__ == "__main__":

    # 1️⃣ Test HubSpot directly
    sample_contact = {
        "email": "smartintegration@example.com",
        "firstname": "Smart",
        "lastname": "Integration",
        "phone": "9999999999",
        "jobtitle": "API Automation"
    }

    create_or_update_contact(sample_contact)

    # 2️⃣ Send LinkedIn profile to SignalHire
    linkedin_profile = "https://www.linkedin.com/in/sample-profile/"
    send_linkedin_to_signalhire(linkedin_profile)
