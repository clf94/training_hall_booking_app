from apscheduler.schedulers.background import BackgroundScheduler
from datetime import date, datetime
from models import Booking
from extensions import db


def cleanup_old_bookings(app):
    """Delete old bookings from the database."""
    with app.app_context():
        today = date.today().isoformat()
        deleted = Booking.query.filter(Booking.day < today).delete()
        db.session.commit()
        if deleted:
            print(f"[{datetime.now()}] Cleaned up {deleted} old bookings.")
        else:
            print(f"[{datetime.now()}] No old bookings.")


def start_scheduler(app):
    """Start APScheduler background job."""
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: cleanup_old_bookings(app), 'cron', hour=0, minute=5)
    scheduler.start()
    print("🕒 Scheduler started (daily cleanup at 00:05).")
