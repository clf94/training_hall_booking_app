from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv
import os
from datetime import date, datetime, time as dt_time

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "supersecretkey")
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bookings.db'
db = SQLAlchemy(app)

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player = db.Column(db.String(50))
    partner = db.Column(db.String(50), nullable=True)
    day = db.Column(db.String(10))
    start = db.Column(db.String(5))
    end = db.Column(db.String(5))
    status = db.Column(db.String(20), default="booked")

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    match_day = db.Column(db.Boolean, default=False)
    extra_table = db.Column(db.Boolean, default=False)
    second_match = db.Column(db.Boolean, default=False)
    second_match_extra_table = db.Column(db.Boolean, default=False)
    match_start = db.Column(db.String(5), nullable=True)
    match_end = db.Column(db.String(5), nullable=True)

users = [
    "Albus, Lennart","Angelini, Giacomo","Bamil, Aradhya","Basu, Soumya","Batinic, Danijel",
    "Beranek, Peter","Bhardwaj, Akshat Kumar","Bosshard, Nicolas","Bradac, Domagoj","Braun, Jacob Martin",
    "Bulmak, Munzur","Caldesi, Luca Francesco","Cassanelli, Carlo","Chen, Manyu","Chernik, Vitaly",
    "Couto, Yago","Dai, Xi","De Belder, Audrey","Di Michino, Giorgio","Distler, Jacob","Frey, Rolf",
    "Foerster, Eva","Fuchs, Laurin","Geiger, Margit","Grunder, Michael","Hala, Michael","Hanzawa, Michiru",
    "Hillmann, Matthias","Hou, Jyun Yu","Huang, Yixin","Koop, Olga","König, Markus","Kull, Eric",
    "Lai, Xiaotong","Lemke, Meinolf","Li, Yuchen","Loo, Christopher T","Loo, Natascha","Loosli, Dominik",
    "Maier, Florin","Main, Maximilian","Matuschek, Nicolai","Mazloumian, Amin Seyed","Müsing, Andreas",
    "Nemes, Olga","Norden, Jens","Ondis, Jozef Jun","Paliwal, Saurabh","Parkitny, Lisa","Pereira, Cesar",
    "Potoplyak, Grygoriy","Protsch, Florian","Queudot, Florent","Reichle, Indira","Rouger, Robin",
    "Rupp, Samuel","Salleras Hanzawa, Kei","Scalari, Giorgio","Schaffler, Alois","Schinz, Hanspeter",
    "Schlenger, Jonas","Schwarz, Peter","Sergueev, Pyotr","Sertcan Gökmen, Belize","Sieber, Nick",
    "Sitt, Axel","Sladek, Samuel","Steiger, Marion","Stroh-Desler, Jens","Tomcak, Ladislav","Trtik, Lukas",
    "Waschkies, Jannes","Wei, Lin Yun","Wei, Ruoqi","Zech, Damian","Zhang, Yong","Zhu, Qifeng","Zurfluh, Ursula"
]

@app.before_request
def load_settings():
    session['is_admin'] = session.get('is_admin', False)
    if Settings.query.first() is None:
        db.session.add(Settings())
        db.session.commit()

@app.route("/")
def index():
    settings = Settings.query.first()
    return render_template(
        "index.html",
        users=users,
        date=date.today(),
        is_admin=session.get('is_admin', False),
        match_day=settings.match_day if settings else False,
        extra_table=settings.extra_table if settings else False,
        second_match=settings.second_match if settings else False,
        second_match_extra_table=settings.second_match_extra_table if settings else False,
        match_start=settings.match_start if settings else "",
        match_end=settings.match_end if settings else ""
    )

@app.route("/admin-login", methods=["GET","POST"])
def admin_login():
    if request.method=="POST":
        if request.form.get("password")==ADMIN_PASSWORD:
            session['is_admin']=True
            return redirect(url_for("index"))
        return render_template("admin_login.html", error="Wrong password")
    return render_template("admin_login.html", error=None)

@app.route("/admin-logout")
def admin_logout():
    session['is_admin']=False
    return redirect(url_for("index"))

@app.route("/bookings")
def bookings():
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
            "status": b.status
        })
    return jsonify(data)

def parse_hm_to_timeobj(hm: str):
    """Return a datetime.time object for HH:MM or None if invalid/empty."""
    if not hm:
        return None
    try:
        parts = hm.split(":")
        return dt_time(int(parts[0]), int(parts[1]))
    except Exception:
        return None

def time_in_range(start: dt_time, end: dt_time, now: dt_time):
    """Return True if now is in [start, end) when start < end.
       If start == end treat as full-day. This assumes times on same day."""
    if not start or not end:
        return False
    if start <= end:
        return start <= now < end
    # unlikely case (overnight), treat wrap-around
    return now >= start or now < end

@app.route("/occupancy")
def occupancy():
    today_iso = date.today().isoformat()
    # count only checked-in bookings for today
    bookings = Booking.query.filter_by(day=today_iso, status="checked-in").all()
    occupied = 0
    for b in bookings:
        if b.partner and not b.partner.startswith("None-"):
            occupied += 2
        else:
            occupied += 1

    settings = Settings.query.first()
    match_day_flag = False
    match_start = ""
    match_end = ""
    extra_table = False
    second_match_flag = False
    second_match_extra_table = False

    # current local time as time object
    now_time = datetime.now().time()

    if settings:
        # parse configured match start/end into time objects
        m_start = parse_hm_to_timeobj(settings.match_start)
        m_end = parse_hm_to_timeobj(settings.match_end)

        # Apply match extras only if match_day enabled AND current time is within the match window
        if settings.match_day and m_start and m_end and time_in_range(m_start, m_end, now_time):
            occupied += 4
            match_day_flag = True
            match_start = settings.match_start
            match_end = settings.match_end
        else:
            # still expose match_start/end so client knows the configured window
            if settings.match_start:
                match_start = settings.match_start
            if settings.match_end:
                match_end = settings.match_end

        # Extra table for first match is also applied only during the match window
        if settings.extra_table and m_start and m_end and time_in_range(m_start, m_end, now_time):
            occupied += 2
            extra_table = True

        # Second match handling: parse separate flags the same way.
        # For simplicity we assume second_match uses the same match_start/match_end fields.
        if settings.second_match and m_start and m_end and time_in_range(m_start, m_end, now_time):
            occupied += 4
            second_match_flag = True
        if settings.second_match_extra_table and m_start and m_end and time_in_range(m_start, m_end, now_time):
            occupied += 2
            second_match_extra_table = True

    return jsonify({
        "occupied": occupied,
        "capacity": 12,
        # inform client whether extras are currently active (based on now)
        "match_day": match_day_flag,
        "match_start": match_start,
        "match_end": match_end,
        "extra_table": extra_table,
        "second_match": second_match_flag,
        "second_match_extra_table": second_match_extra_table
    })

@app.route("/book", methods=["POST"])
def book():
    player = request.form["player"].strip()
    if player == "other":
        player = request.form.get("player_external", "").strip()
        if not player:
            return jsonify({"ok": False, "error": "Please enter a player name."})

    partner = request.form.get("partner")
    if partner == "other":
        partner = request.form.get("partner_external", "").strip()
    if not partner:
        partner = None

    day = request.form["day"]
    start = request.form["start"]
    end = request.form["end"]

    now = datetime.now()
    try:
        booking_time = datetime.combine(date.fromisoformat(day), datetime.strptime(start, "%H:%M").time())
    except Exception:
        return jsonify({"ok": False, "error": "Invalid date/time."})

    if booking_time < now:
        return jsonify({"ok": False, "error": "You cannot book slots in the past."})

    warning = None
    s = Settings.query.first()
    if s and s.match_day and s.match_start and s.match_end:
        match_start_dt = datetime.strptime(s.match_start, "%H:%M").time()
        match_end_dt = datetime.strptime(s.match_end, "%H:%M").time()
        user_start = datetime.strptime(start, "%H:%M").time()
        user_end = datetime.strptime(end, "%H:%M").time()

        def intersects(a_start, a_end, b_start, b_end):
            return not (a_end <= b_start or a_start >= b_end)

        if intersects(user_start, user_end, match_start_dt, match_end_dt):
            # Check if the match is fully configured (all 4 checkboxes)
            full_match = s.match_day and s.extra_table and s.second_match and s.second_match_extra_table
            if full_match:
                return jsonify({"ok": False, "error": "This slot is reserved for a full match. Please select another time."})
            else:
                # Warn user but still allow booking
                # Optionally, show current occupancy in that window
                existing = Booking.query.filter_by(day=day).all()
                occupied = 0
                for b in existing:
                    b_start = datetime.strptime(b.start, "%H:%M").time()
                    b_end = datetime.strptime(b.end, "%H:%M").time()
                    if intersects(b_start, b_end, match_start_dt, match_end_dt):
                        if b.partner and not b.partner.startswith("None-"):
                            occupied += 2
                        else:
                            occupied += 1
                MAX_CAPACITY = 12
                warning = f"This slot overlaps the match window. Current occupancy: {occupied}/{MAX_CAPACITY}."

    # Conflict check
    conflict_query = Booking.query.filter(
        Booking.day == day,
        Booking.start == start,
        Booking.end == end
    )
    conflict_filters = []
    if player:
        conflict_filters.append((Booking.player == player) | (Booking.partner == player))
    if partner:
        conflict_filters.append((Booking.player == partner) | (Booking.partner == partner))
    if conflict_filters:
        for f in conflict_filters:
            conflict_query = conflict_query.filter(f)

    conflict = conflict_query.first()
    if conflict:
        return jsonify({"ok": False, "error": "Player or partner already booked in this slot."})

    new_booking = Booking(player=player, partner=partner, day=day, start=start, end=end)
    db.session.add(new_booking)
    db.session.commit()

    response = {
        "ok": True,
        "message": "Booking successful! If you want to cancel your booking, please get in touch with an admin."
    }
    if warning:
        response["warning"] = warning

    return jsonify(response)

@app.route("/checkin", methods=["POST"])
def checkin():
    booking_id = request.json.get("booking_id")
    b = Booking.query.get(booking_id)
    if b:
        b.status = "checked-in"
        db.session.commit()
        return jsonify({"ok": True}), 200
    return jsonify({"ok": False, "error": "Booking not found"}), 404

@app.route("/checkout", methods=["POST"])
def checkout():
    booking_id = request.json.get("booking_id")
    b = Booking.query.get(booking_id)
    if b:
        b.status = "booked"
        db.session.commit()
        return jsonify({"ok": True}), 200
    return jsonify({"ok": False, "error": "Booking not found"}), 404

@app.route("/delete", methods=["POST"])
def delete_booking():
    booking_id = request.json.get("booking_id")
    b = Booking.query.get(booking_id)
    if b and session.get('is_admin'):
        db.session.delete(b)
        db.session.commit()
        return jsonify({"ok": True}), 200
    return jsonify({"ok": False, "error": "Not authorized or booking missing"}), 401

@app.route("/update-settings", methods=["POST"])
def update_settings():
    if not session.get('is_admin'):
        return "Unauthorized", 401
    match_day = request.json.get("match_day", False)
    extra_table = request.json.get("extra_table", False)
    second_match = request.json.get("second_match", False)
    second_match_extra_table = request.json.get("second_match_extra_table", False)
    match_start = request.json.get("match_start", "")
    match_end = request.json.get("match_end", "")
    settings = Settings.query.first()
    settings.match_day = match_day
    settings.extra_table = extra_table
    settings.second_match = second_match
    settings.second_match_extra_table = second_match_extra_table
    settings.match_start = match_start
    settings.match_end = match_end
    db.session.commit()
    return jsonify({"ok": True}), 200

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5009, debug=True)