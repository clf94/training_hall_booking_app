from flask import Blueprint, jsonify
from datetime import date
from models import Booking, Settings
from utils import zurich_now, parse_hm_to_timeobj, time_in_range

occupancy_bp = Blueprint("occupancy_bp", __name__)

@occupancy_bp.route("/occupancy")
def occupancy_route():
    today_iso = date.today().isoformat()
    bookings = Booking.query.filter_by(day=today_iso, status="checked-in").all()
    occupied = 0

    for b in bookings:
        occupied += 2 if b.partner and not b.partner.startswith("None-") else 1

    settings = Settings.query.first()

    if not settings:
        return jsonify({
            "occupied": 0,
            "capacity": 12,
            "event_day": False,
            "event_start": None,
            "event_end": None,
            "event_name": None
        })

    # Default values
    event_day_flag = False
    event_name = "Match"
    event_start = ""
    event_end = ""
    extra_table_flag = False
    second_event_flag = False
    second_event_extra_table_flag = False

    now_time = zurich_now().time()

    if settings:
        event_day_flag = getattr(settings, "event_day", False)
        event_start = getattr(settings, "event_start", "")
        event_end = getattr(settings, "event_end", "")
        event_name = getattr(settings, "event_name", "Match")
        extra_table_flag = getattr(settings, "extra_table", False)
        second_event_flag = getattr(settings, "second_event", False)
        second_event_extra_table_flag = getattr(settings, "second_event_extra_table", False)

        # ✅ Only if event_day and valid times exist
        if event_day_flag and event_start and event_end:
            event_start_time = parse_hm_to_timeobj(event_start)
            event_end_time = parse_hm_to_timeobj(event_end)

            # If event currently ongoing, add occupied tables
            if time_in_range(event_start_time, event_end_time, now_time):
                if event_day_flag:
                    occupied += 4
                if extra_table_flag:
                    occupied += 2
                if second_event_flag:
                    occupied += 4
                if second_event_extra_table_flag:
                    occupied += 2

    return jsonify({
        "occupied": occupied,
        "capacity": 12,
        "event_day": event_day_flag,
        "event_name": event_name,
        "event_start": event_start,
        "event_end": event_end,
        "extra_table": extra_table_flag,
        "second_event": second_event_flag,
        "second_event_extra_table": second_event_extra_table_flag
    })
