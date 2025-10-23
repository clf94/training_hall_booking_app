from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv
import os
from datetime import date, datetime

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
    status = db.Column(db.String(20), default="booked")  # booked or checked-in

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    match_day = db.Column(db.Boolean, default=False)
    extra_table = db.Column(db.Boolean, default=False)

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
        extra_table=settings.extra_table if settings else False
    )

@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        pwd = request.form.get("password")
        if pwd == ADMIN_PASSWORD:
            session['is_admin'] = True
            return redirect(url_for("index"))
        else:
            return render_template("admin_login.html", error="Wrong password")
    return render_template("admin_login.html", error=None)

@app.route("/admin-logout")
def admin_logout():
    session['is_admin'] = False
    return redirect(url_for("index"))

@app.route("/bookings")
def bookings():
    day = request.args.get("day")
    bookings = Booking.query.filter_by(day=day).all() if day else Booking.query.all()
    data = [{
        "booking_id": b.id,
        "player": b.player,
        "partner": b.partner,
        "day": b.day,
        "start": b.start,
        "end": b.end,
        "status": b.status
    } for b in bookings]
    return jsonify(data)

@app.route("/occupancy")
def occupancy():
    today = date.today().isoformat()
    bookings = Booking.query.filter_by(day=today, status="checked-in").all()
    occupied = sum(2 if b.partner else 1 for b in bookings)
    settings = Settings.query.first()
    match_day = False
    if settings:
        if settings.match_day:
            occupied += 4
            match_day = True
        if settings.extra_table:
            occupied += 2
    return jsonify({"occupied": occupied, "capacity": 12, "match_day": match_day})

@app.route("/book", methods=["POST"])
def book():
    player = request.form["player"]
    partner = request.form.get("partner")
    partner_external = request.form.get("partner_external")
    if partner == "other":
        partner = partner_external.strip() or None
    day = request.form["day"]
    start = request.form["start"]
    end = request.form["end"]

    now = datetime.now()
    booking_time = datetime.combine(date.fromisoformat(day), datetime.strptime(start, "%H:%M").time())
    if booking_time < now:
        return jsonify({"ok": False, "error": "You cannot book slots in the past."})

    conflict = Booking.query.filter(
        Booking.day == day,
        Booking.start == start,
        Booking.end == end,
        ((Booking.player == player) | (Booking.partner == player) |
         (Booking.player == partner) | (Booking.partner == partner))
    ).first()

    if conflict:
        return jsonify({"ok": False, "error": "Player or partner already booked in this slot."})

    new_booking = Booking(player=player, partner=partner, day=day, start=start, end=end)
    db.session.add(new_booking)
    db.session.commit()
    return jsonify({
        "ok": True,
        "message": "Booking successful! If you want to cancel your booking, please get in touch with an admin."
    })

@app.route("/checkin", methods=["POST"])
def checkin():
    booking_id = request.json["booking_id"]
    b = Booking.query.get(booking_id)
    if b:
        b.status = "checked-in"
        db.session.commit()
    return "", 204

@app.route("/checkout", methods=["POST"])
def checkout():
    booking_id = request.json["booking_id"]
    b = Booking.query.get(booking_id)
    if b:
        b.status = "booked"
        db.session.commit()
    return "", 204

@app.route("/delete", methods=["POST"])
def delete_booking():
    booking_id = request.json["booking_id"]
    b = Booking.query.get(booking_id)
    if b and session.get('is_admin'):
        db.session.delete(b)
        db.session.commit()
    return "", 204

@app.route("/update-settings", methods=["POST"])
def update_settings():
    if not session.get('is_admin'):
        return "Unauthorized", 401
    match_day = request.json.get("match_day", False)
    extra_table = request.json.get("extra_table", False)
    settings = Settings.query.first()
    settings.match_day = match_day
    settings.extra_table = extra_table
    db.session.commit()
    return "", 204

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5009, debug=True)
