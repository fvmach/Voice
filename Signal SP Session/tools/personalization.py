# personalization.py

import os
import requests
import urllib.parse

def get_customer_identifier(setup_event: dict) -> str:
    direction = setup_event.get("direction", "inbound")
    if direction == "inbound":
        return setup_event.get("from")
    else:
        return setup_event.get("to")

def fetch_segment_profile(phone_number: str) -> dict:
    # Load credentials
    SEGMENT_SPACE_ID = os.environ['SEGMENT_SPACE_ID']
    SEGMENT_ACCESS_SECRET = os.environ['SEGMENT_ACCESS_SECRET']

    # Properly escape the + symbol and any unsafe characters
    encoded_phone = urllib.parse.quote_plus(phone_number)

    url = f"https://profiles.segment.com/v1/spaces/{SEGMENT_SPACE_ID}/collections/users/profiles/phone:{encoded_phone}/traits"

    # Basic Auth with token as username, blank password
    response = requests.get(url, auth=(SEGMENT_ACCESS_SECRET, ''))

    if response.status_code == 404:
        return {"error": "Profile not found"}
    response.raise_for_status()
    return response.json()

def get_personalization_context(setup_event: dict) -> dict:
    phone = get_customer_identifier(setup_event)
    if not phone:
        return {"error": "Missing phone number in setup event"}
    return fetch_segment_profile(phone)
