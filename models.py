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
    
    # Event/Match settings (renamed for generalization)
    event_day = db.Column(db.Boolean, default=False)
    event_name = db.Column(db.String(50), default="Match")
    event_start = db.Column(db.String(5), nullable=True)
    event_end = db.Column(db.String(5), nullable=True)
    
    # Table configuration
    extra_table = db.Column(db.Boolean, default=False)
    second_event = db.Column(db.Boolean, default=False)
    second_event_extra_table = db.Column(db.Boolean, default=False)
    
 