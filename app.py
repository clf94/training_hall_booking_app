from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import date

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bookings.db'
db = SQLAlchemy(app)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player = db.Column(db.String(50))
    partner = db.Column(db.String(50), nullable=True)
    day = db.Column(db.String(10))
    start = db.Column(db.String(5))
    end = db.Column(db.String(5))
    status = db.Column(db.String(20), default="booked")  # booked or checked-in

users = ["Alice", "Bob", "Charlie", "Diana"]

@app.route("/")
def index():
    return render_template("index.html", users=users, date=date.today())

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
    # Only count checked-in bookings for live occupancy
    bookings = Booking.query.filter_by(day=today, status="checked-in").all()
    occupied = sum(2 if b.partner else 1 for b in bookings)
    return jsonify({"occupied": occupied, "capacity": 12})

@app.route("/book", methods=["POST"])
def book():
    player = request.form["player"]
    partner = request.form.get("partner")
    day = request.form["day"]
    start = request.form["start"]
    end = request.form["end"]

    # Prevent double booking for player or partner in the same slot
    conflict = Booking.query.filter(
        Booking.day==day,
        Booking.start==start,
        Booking.end==end,
        ((Booking.player==player) | (Booking.partner==player) |
         (Booking.player==partner) | (Booking.partner==partner))
    ).first()

    if conflict:
        return jsonify({"ok": False, "error": "Player or partner already booked in this slot"})

    new_booking = Booking(
        player=player, partner=partner,
        day=day, start=start, end=end,
        status="booked"
    )
    db.session.add(new_booking)
    db.session.commit()
    return jsonify({"ok": True})

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
    if b:
        db.session.delete(b)
        db.session.commit()
    return "", 204

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5009, debug=True)
