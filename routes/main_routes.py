from flask import Blueprint, render_template, session
from models import Settings
import os

main_bp = Blueprint("main_bp", __name__)

USERS = os.getenv("USERS", "").split(",")

@main_bp.route("/")
def index():
    settings = Settings.query.first()
    
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
        users=USERS,
        is_admin=session.get("is_admin", False),
        event_day=event_day,
        event_name=event_name,
        event_start=event_start,
        event_end=event_end,
        extra_table=extra_table,
        second_event=second_event,
        second_event_extra_table=second_event_extra_table,
        
    )