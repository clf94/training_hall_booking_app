from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv
import os
import json
from datetime import date, datetime, time as dt_time, timedelta
from sqlalchemy import and_, or_
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, date, timedelta
from datetime import datetime, time, date
from zoneinfo import ZoneInfo

ZURICH_TZ = ZoneInfo("Europe/Zurich")


load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "supersecretkey")
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bookings.db'
db = SQLAlchemy(app)

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

def parse_hm_to_timeobj(hm: str):
    """Parse 'HH:MM' into a datetime.time object."""
    if not hm:
        return None
    try:
        h, m = map(int, hm.split(":"))
        return dt_time(h, m)
    except ValueError:
        return None


def time_in_range(start: dt_time, end: dt_time, now: dt_time):
    """Return True if now is between start and end (handles overnight ranges)."""
    if not start or not end:
        return False
    if start <= end:
        return start <= now < end
    return now >= start or now < end


def zurich_now():
    """Return current Zurich datetime (timezone aware)."""
    return datetime.now(ZURICH_TZ)


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player = db.Column(db.String(50))
    partner = db.Column(db.String(50), nullable=True)
    day = db.Column(db.String(10))
    start = db.Column(db.String(5))
    end = db.Column(db.String(5))
    status = db.Column(db.String(20), default="booked")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(ZURICH_TZ))
    checked_in_at = db.Column(db.DateTime, nullable=True) 


class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    match_day = db.Column(db.Boolean, default=False)
    extra_table = db.Column(db.Boolean, default=False)
    second_match = db.Column(db.Boolean, default=False)
    second_match_extra_table = db.Column(db.Boolean, default=False)
    match_start = db.Column(db.String(5), nullable=True)
    match_end = db.Column(db.String(5), nullable=True)

def load_users():
    users_file = os.path.join(os.path.dirname(__file__), "users.json")
    with open(users_file, "r", encoding="utf-8") as f:
        users = json.load(f)
    return sorted(users)  # returns alphabetically sorted list


@app.before_request
def load_settings():
    session['is_admin'] = session.get('is_admin', False)
    if Settings.query.first() is None:
        db.session.add(Settings())
        db.session.commit()

@app.route("/")
def index():
    users = load_users()
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
            "status": b.status,
            "created_at": b.created_at.isoformat() if b.created_at else None,
            "checked_in_at": b.checked_in_at.isoformat() if b.checked_in_at else None

        })
    return jsonify(data)

def parse_hm_to_timeobj(hm: str):
    if not hm: return None
    try:
        h,m = map(int, hm.split(":"))
        return dt_time(h,m)
    except: return None

def time_in_range(start: dt_time, end: dt_time, now: dt_time):
    if not start or not end: return False
    if start <= end: return start <= now < end
    return now >= start or now < end

@app.route("/occupancy")
def occupancy():
    today_iso = datetime.now(ZURICH_TZ).date().isoformat()
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

    now_time = datetime.now(ZURICH_TZ).time()
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

@app.route("/book", methods=["POST"])
def book():
    player = request.form["player"].strip()
    if player=="other":
        player = request.form.get("player_external","").strip()
        if not player: return jsonify({"ok": False,"error":"Please enter player name."})

    partner = request.form.get("partner")
    if partner=="other":
        partner = request.form.get("partner_external","").strip()
    if not partner: partner=None

    day = request.form["day"]
    start = request.form["start"]
    end = request.form["end"]
    now = datetime.now(ZURICH_TZ)
    try:
        booking_time = datetime(
    year=int(day[:4]),
    month=int(day[5:7]),
    day=int(day[8:]),
    hour=int(start[:2]),
    minute=int(start[3:]),
    tzinfo=ZURICH_TZ
)

    except:
        return jsonify({"ok": False, "error":"Invalid date/time."})
    if booking_time < now:
        return jsonify({"ok": False,"error":"Cannot book past slots."})

    s = Settings.query.first()
    if s and s.match_day and s.match_start and s.match_end:
        m_start = datetime.strptime(s.match_start,"%H:%M").time()
        m_end = datetime.strptime(s.match_end,"%H:%M").time()
        u_start = datetime.strptime(start,"%H:%M").time()
        u_end = datetime.strptime(end,"%H:%M").time()
        def intersects(a_start,a_end,b_start,b_end): return not(a_end<=b_start or a_start>=b_end)

        if intersects(u_start,u_end,m_start,m_end):
            full_match = s.match_day and s.extra_table and s.second_match and s.second_match_extra_table
            if (full_match and s.match_day == date.today().isoformat()):
                return jsonify({"ok": False, "error":"This slot is fully reserved for match. Choose another time."})

    # --- Conflict check ---
    conflict_query = Booking.query.filter(
    Booking.day == day,
    or_(
        # player or partner overlap
        and_(Booking.player == player if player else False),
        and_(Booking.partner == player if player else False),
        and_(Booking.player == partner if partner else False),
        and_(Booking.partner == partner if partner else False),
    ),
    # time overlap
    or_(
        and_(Booking.start <= start, Booking.end > start),
        and_(Booking.start < end, Booking.end >= end),
        and_(Booking.start >= start, Booking.end <= end)
    )
)
    if conflict_query.first():
       return jsonify({"ok": False, "error":"Player or partner already booked in this slot."})

    new_booking = Booking(player=player, partner=partner, day=day, start=start, end=end, created_at=datetime.now(ZURICH_TZ))
    db.session.add(new_booking)
    db.session.commit()
    return jsonify({"ok": True,"message":"Booking successful!"})

@app.route("/checkin", methods=["POST"])
def checkin():
    booking_id = request.json.get("booking_id")
    b = Booking.query.get(booking_id)
    if b:
        # Only allow check-in on the same day
        if b.day != datetime.now(ZURICH_TZ).date().isoformat():
            return jsonify({"ok": False, "error":"Check-in only allowed today."}), 400
        b.status="checked-in"
        db.session.commit()
        return jsonify({"ok": True})
    return jsonify({"ok": False,"error":"Booking not found"}),404

@app.route("/checkout", methods=["POST"])
def checkout():
    booking_id = request.json.get("booking_id")
    b = Booking.query.get(booking_id)
    if b:
        b.status="booked"
        db.session.commit()
        return jsonify({"ok": True})
    return jsonify({"ok": False,"error":"Booking not found"}),404

@app.route("/delete", methods=["POST"])
def delete_booking():
    booking_id = request.json.get("booking_id")
    b = Booking.query.get(booking_id)
    if b and session.get('is_admin'):
        db.session.delete(b)
        db.session.commit()
        return jsonify({"ok": True})
    return jsonify({"ok": False,"error":"Not authorized or booking missing"}),401

@app.route("/update-settings", methods=["POST"])
def update_settings():
    if not session.get('is_admin'): return "Unauthorized", 401
    payload = request.json
    s = Settings.query.first()
    s.match_day = payload.get("match_day", False)
    s.extra_table = payload.get("extra_table", False)
    s.second_match = payload.get("second_match", False)
    s.second_match_extra_table = payload.get("second_match_extra_table", False)
    s.match_start = payload.get("match_start","")
    s.match_end = payload.get("match_end","")
    db.session.commit()
    return jsonify({"ok": True})
    
def cleanup_old_bookings():
    with app.app_context():
        today = date.today().isoformat()
        deleted = Booking.query.filter(Booking.day < today).delete()
        db.session.commit()
        if deleted:
            print(f"[{datetime.now()}] Cleaned up {deleted} old bookings.")
        else:
            print(f"[{datetime.now()}] No old bookings to clean.")

scheduler = BackgroundScheduler()
# Run cleanup daily at 00:05
scheduler.add_job(cleanup_old_bookings, 'cron', hour=0, minute=5)
scheduler.start()    

if __name__=="__main__":
   with app.app_context(): db.create_all()
   app.run(host="0.0.0.0", port=5009, debug=True)