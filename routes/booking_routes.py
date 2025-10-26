from flask import Blueprint, jsonify, request, session
from sqlalchemy import and_, or_
from datetime import datetime, date
from config import ZURICH_TZ
from extensions import db
from models import Booking, Settings
from utils import notify_n8n, parse_hm_to_timeobj, time_in_range, zurich_now

booking_bp = Blueprint("booking_bp", __name__)

@booking_bp.route("/bookings")
def bookings_route():
    day = request.args.get("day")
    bookings = Booking.query.filter_by(day=day).all() if day else Booking.query.all()
    data = []
    for b in bookings:
        partner_val = b.partner
        if partner_val and partner_val.startswith("None-"):
            partner_val = None
        data.append({
            "booking_id": b.id,
            "player": b.player,
            "partner": partner_val,
            "day": b.day,
            "start": b.start,
            "end": b.end,
            "status": b.status,
            "created_at": b.created_at.isoformat() if b.created_at else None,
            "checked_in_at": b.checked_in_at.isoformat() if b.checked_in_at else None
        })
    return jsonify(data)

@booking_bp.route("/occupancy")
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

@booking_bp.route("/book", methods=["POST"])
def book_route():
    try:
        player = request.form.get("player", "").strip()
        if not player:
            return jsonify({"ok": False, "error": "Player missing."})
        if player == "other":
            player = request.form.get("player_external", "").strip()
            if not player:
                return jsonify({"ok": False, "error": "Please enter player name."})

        partner = request.form.get("partner")
        if partner == "other":
            partner = request.form.get("partner_external", "").strip()
        if not partner:
            partner = None

        day = request.form.get("day")
        start = request.form.get("start")
        end = request.form.get("end")
        if not day or not start or not end:
            return jsonify({"ok": False, "error": "Missing date/time."})

        booking_time_naive = datetime.strptime(f"{day} {start}", "%Y-%m-%d %H:%M")
        booking_time = booking_time_naive.replace(tzinfo=ZURICH_TZ)
        now = zurich_now()
        if booking_time < now:
            return jsonify({"ok": False, "error": "Cannot book past slots."})

        conflict_query = Booking.query.filter(
            Booking.day == day,
            or_(
                Booking.player == player,
                Booking.partner == player,
                Booking.player == partner,
                Booking.partner == partner,
            ),
            or_(
                and_(Booking.start <= start, Booking.end > start),
                and_(Booking.start < end, Booking.end >= end),
                and_(Booking.start >= start, Booking.end <= end)
            )
        )
        if conflict_query.first():
            return jsonify({"ok": False, "error": "Player or partner already booked in this slot."})

        new_booking = Booking(player=player, partner=partner, day=day, start=start, end=end)
        db.session.add(new_booking)
        db.session.commit()
        notify_n8n(new_booking)
        return jsonify({"ok": True, "message": "Booking successful!"})

    except Exception as e:
        print("Booking error:", e)
        return jsonify({"ok": False, "error": "Server error. Check input."})

@booking_bp.route("/checkin", methods=["POST"])
def checkin_route():
    booking_id = request.json.get("booking_id")
    b = Booking.query.get(booking_id)
    if b:
        if b.day != zurich_now().date().isoformat():
            return jsonify({"ok": False, "error": "Check-in only allowed today."}), 400
        b.status = "checked-in"
        db.session.commit()
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "Booking not found"}), 404

@booking_bp.route("/checkout", methods=["POST"])
def checkout_route():
    booking_id = request.json.get("booking_id")
    b = Booking.query.get(booking_id)
    if b:
        b.status = "booked"
        db.session.commit()
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "Booking not found"}), 404

@booking_bp.route("/delete", methods=["POST"])
def delete_booking_route():
    booking_id = request.json.get("booking_id")
    b = Booking.query.get(booking_id)
    if b and session.get("is_admin"):
        db.session.delete(b)
        db.session.commit()
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "Not authorized or booking missing"}), 401

@booking_bp.route("/update-settings", methods=["POST"])
def update_settings_route():
    if not session.get("is_admin"):
        return "Unauthorized", 401
    payload = request.json
    s = Settings.query.first()
    s.match_day = payload.get("match_day", False)
    s.extra_table = payload.get("extra_table", False)
    s.second_match = payload.get("second_match", False)
    s.second_match_extra_table = payload.get("second_match_extra_table", False)
    s.match_start = payload.get("match_start", "")
    s.match_end = payload.get("match_end", "")
    db.session.commit()
    return jsonify({"ok": True})
