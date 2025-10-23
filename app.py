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

users = [
    "Zech, Damian","Beranek, Peter","Basu, Soumya","Ondis, Jozef Jun","Zhu, Qifeng","Matuschek, Nicolai",
    "Norden, Jens","Tomcak, Ladislav","Potoplyak, Grygoriy","Protsch, Florian","Sladek, Samuel 723214",
    "Braun, Jacob Martin","Main, Maximilian","Cassanelli, Carlo","Hillmann, Matthias",
    "Mazloumian, Amin Seyed","Schlenger, Jonas","Dai, Xi","Di Michino, Giorgio","Zhang, Yong",
    "Li, Yuchen","Müsing, Andreas","Rouger, Robin","Bhardwaj, Akshat Kumar","Bradac, Domagoj",
    "Chernik, Vitaly","Grunder, Michael","Lemke, Meinolf","Loo, Christopher T","Stroh-Desler, Jens",
    "Paliwal, Saurabh","Schaffler, Alois","Waschkies, Jannes","Hala, Michael","Lai, Xiaotong",
    "Loosli, Dominik","Sitt, Axel","Angelini, Giacomo","Batinic, Danijel","Caldesi, Luca Francesco",
    "Frey, Rolf","König, Markus","Bosshard, Nicolas","Distler, Jacob","Queudot, Florent",
    "Rupp, Samuel","Trtik, Lukas","Albus, Lennart","Bamil, Aradhya","Bulmak, Munzur","Couto, Yago",
    "De Belder, Audrey","Fuchs, Laurin","Hou, Jyun Yu","Kull, Eric","Maier, Florin","Pereira, Cesar",
    "Salleras Hanzawa, Kei","Scalari, Giorgio","Schinz, Hanspeter","Schwarz, Peter","Sergueev, Pyotr",
    "Sieber, Nick","Nemes, Olga","Wei, Ruoqi","Koop, Olga","Loo, Natascha","Wei, Lin Yun",
    "Hanzawa, Michiru","Geiger, Margit","Sertcan Gökmen, Belize","Steiger, Marion","Chen, Manyu",
    "Reichle, Indira","Foerster, Eva","Huang, Yixin","Parkitny, Lisa","Zurfluh, Ursula"
]

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
    bookings = Booking.query.filter_by(day=today, status="checked-in").all()
    occupied = sum(2 if b.partner else 1 for b in bookings)
    return jsonify({"occupied": occupied, "capacity": 12})

@app.route("/book", methods=["POST"])
def book():
    player = request.form["player"]
    partner = request.form.get("partner")
    external_partner = request.form.get("partner_external")
    if partner == "other" and external_partner:
        partner = external_partner.strip()
    day = request.form["day"]
    start = request.form["start"]
    end = request.form["end"]

    if partner == player:
        return jsonify({"ok": False, "error": "Player cannot be their own partner"})

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
