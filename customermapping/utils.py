# customermapping/utils.py
import requests
from django.conf import settings
from base64 import b64encode

def fetch_user_by_phone(phone_number):
    api_base = getattr(settings, "API_BASE_URL", None)
    username = getattr(settings, "API_AUTH_USERNAME", None)
    password = getattr(settings, "API_AUTH_PASSWORD", None)

    if not api_base or not username or not password:
        print("⚠️ API credentials not set")
        return None

    api_url = f"{api_base.rstrip('/')}/get_user_by_phone/{phone_number}"
    auth_value = f"{username}:{password}"
    encoded_auth_value = b64encode(auth_value.encode('utf-8')).decode('utf-8')

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {encoded_auth_value}"
    }

    try:
        resp = requests.get(api_url, headers=headers, timeout=10, verify=False)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        print("API request failed:", e)
        return None


def get_customer_by_phone(phone):
    """Fetch and return a list of users for a given phone number."""
    data = fetch_user_by_phone(phone)

    if not data or not isinstance(data, list):
        return None

    users = []
    for record in data:
        user_info = {}
        billing_info = {}

        for item in record:
            if "User" in item:
                user_info = item["User"]
            elif "currentBillingCycleUsage" in item:
                billing_info = item["currentBillingCycleUsage"]

        if user_info and user_info.get("status") == "active":
            users.append({
                "id": user_info.get("id", ""),
                "name": user_info.get("name", ""),
                "username": user_info.get("username", ""),
                "phone": user_info.get("phone", ""),
                "email": user_info.get("email", ""),
                "status": user_info.get("status", ""),
                "city": user_info.get("address_city", ""),
                "plan": billing_info.get("bandwidthTemplateName", ""),
                "billing_type": billing_info.get("billingResetType", "")
            })

    return users
