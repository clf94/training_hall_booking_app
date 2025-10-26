import json
import os
from datetime import datetime, time as dt_time
from config import ZURICH_TZ
import requests

WEB_HOOK_N8N_URL = os.getenv("WEB_HOOK_N8N_URL")

def load_users():
    users_file = os.path.join(os.path.dirname(__file__), "users.json")
    with open(users_file, "r", encoding="utf-8") as f:
        users = json.load(f)
    return sorted(users)

def notify_n8n(booking):
    webhook_url = WEB_HOOK_N8N_URL
    try:
        safe_booking = {
            "player": booking.player,
            "partner": booking.partner,
            "day": str(booking.day),
            "start": str(booking.start),
            "end": str(booking.end),
        }
        response = requests.post(webhook_url, json=safe_booking)
        print("Webhook sent:", response.status_code, response.text)
    except Exception as e:
        print("Webhook failed:", e)

def parse_hm_to_timeobj(hm: str):
    if not hm:
        return None
    try:
        h, m = map(int, hm.split(":"))
        return dt_time(h, m)
    except ValueError:
        return None

def time_in_range(start: dt_time, end: dt_time, now: dt_time):
    if not start or not end:
        return False
    if start <= end:
        return start <= now < end
    return now >= start or now < end

def zurich_now():
    return datetime.now(ZURICH_TZ)
