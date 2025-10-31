from flask import Flask, session
from flask_cors import CORS
from dotenv import load_dotenv
import os
from extensions import db
from models import Settings
from routes.main_routes import main_bp
from routes.admin_routes import admin_bp
from routes.booking_routes import booking_bp
from routes.settings_routes import settings_bp
from routes.occupancy_routes import occupancy_bp
from scheduler import start_scheduler

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "supersecretkey")
CORS(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///bookings.db"
db.init_app(app)

# Register blueprints
app.register_blueprint(main_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(booking_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(occupancy_bp)

@app.before_request
def load_settings():
    session['is_admin'] = session.get('is_admin', False)
    if Settings.query.first() is None:
        db.session.add(Settings())
        db.session.commit()

if __name__ == "__main__":
    with app.app_context():
        db.drop_all()
        db.create_all()
        start_scheduler(app)
    app.run(host="0.0.0.0", port=5009, debug=True)
