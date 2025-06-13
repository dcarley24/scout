import requests

# Replace with your private app token
api_key = os.getenv("HUBSPOT_API_KEY")
BASE_URL = "https://api.hubapi.com"

HEADERS = {
    "Authorization": f"Bearer {HUBSPOT_API_KEY}",
    "Content-Type": "application/json"
}

def find_company_by_name(name):
    url = f"{BASE_URL}/crm/v3/objects/companies/search"
    payload = {
        "filterGroups": [{
            "filters": [{
                "propertyName": "name",
                "operator": "EQ",
                "value": name
            }]
        }]
    }
    response = requests.post(url, headers=HEADERS, json=payload)
    if response.ok:
        results = response.json().get("results", [])
        return results[0]["id"] if results else None
    return None

def create_company(name):
    url = f"{BASE_URL}/crm/v3/objects/companies"
    payload = {
        "properties": {
            "name": name
        }
    }
    response = requests.post(url, headers=HEADERS, json=payload)
    if response.ok:
        return response.json()["id"]
    return None

def update_company_fields(company_id, summary, discovery):
    url = f"{BASE_URL}/crm/v3/objects/companies/{company_id}"
    payload = {
        "properties": {
            "centriq_snapshot_summary": summary,
            "centriq_discovery_insights": discovery
        }
    }
    response = requests.patch(url, headers=HEADERS, json=payload)
    return response.ok, response.text

def push_snapshot_to_hubspot(name, summary, discovery):
    company_id = find_company_by_name(name)
    if not company_id:
        company_id = create_company(name)
        if not company_id:
            return False, "Failed to create company"

    success, msg = update_company_fields(company_id, summary, discovery)
    return success, msg if success else f"Update failed: {msg}"
