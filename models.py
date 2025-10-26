from extensions import db
from datetime import datetime
from config import ZURICH_TZ

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
