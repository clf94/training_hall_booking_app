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
    match_day_flag = False
    match_start = settings.match_start if settings else ""
    match_end = settings.match_end if settings else ""
    extra_table_flag = False
    second_match_flag = False
    second_match_extra_table_flag = False

    now_time = zurich_now().time()
    if settings and settings.match_day and settings.match_start and settings.match_end:
        m_start = parse_hm_to_timeobj(settings.match_start)
        m_end = parse_hm_to_timeobj(settings.match_end)
        if time_in_range(m_start, m_end, now_time):
            match_day_flag = settings.match_day
            extra_table_flag = settings.extra_table
            second_match_flag = settings.second_match
            second_match_extra_table_flag = settings.second_match_extra_table

            if settings.match_day: occupied += 4
            if settings.extra_table: occupied += 2
            if settings.second_match: occupied += 4
            if settings.second_match_extra_table: occupied += 2

    return jsonify({
        "occupied": occupied,
        "capacity": 12,
        "match_day": match_day_flag,
        "match_start": match_start,
        "match_end": match_end,
        "extra_table": extra_table_flag,
        "second_match": second_match_flag,
        "second_match_extra_table": second_match_extra_table_flag
    })
