from flask import Blueprint, render_template, session
from models import Settings
import os

main_bp = Blueprint("main_bp", __name__)
import json

def load_users():
    """Load users from users.json file"""
    users_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "users.json")
    try:
        with open(users_file, "r", encoding="utf-8") as f:
            users = json.load(f)
        return sorted(users)
    except FileNotFoundError:
        print("⚠️ users.json not found. Using default empty list.")
        return []
    except json.JSONDecodeError:
        print("⚠️ users.json is invalid JSON. Using default empty list.")
        return []

@main_bp.route("/")
def index():
    settings = Settings.query.first()
    
     # Load users from JSON file
    users = load_users()
    
    # Default values
    event_day = False
    event_name = "Match"
    event_start = "14:00"
    event_end = "20:00"
    extra_table = False
    second_event = False
    second_event_extra_table = False
    
    if settings:
        # Use new event fields or fall back to old match fields
        event_day = settings.event_day 
        event_name = settings.event_name 
        event_start = settings.event_start 
        event_end = settings.event_end 
        extra_table = settings.extra_table
        second_event = settings.second_event 
        second_event_extra_table = settings.second_event_extra_table 
    
    return render_template(
        "index.html",
        users=users,
        is_admin=session.get("is_admin", False),
        event_day=event_day,
        event_name=event_name,
        event_start=event_start,
        event_end=event_end,
        extra_table=extra_table,
        second_event=second_event,
        second_event_extra_table=second_event_extra_table,
        
    )