from flask import Blueprint, jsonify, request, session
from models import Settings
from extensions import db

settings_bp = Blueprint("settings_bp", __name__)

@settings_bp.route("/update-settings", methods=["POST"])
def update_settings_route():
    if not session.get("is_admin"):
        return "Unauthorized", 401

    payload = request.json
    s = Settings.query.first()
    if not s:
        return jsonify({"ok": False, "error": "Settings not found"}), 404

    s.match_day = payload.get("match_day", False)
    s.extra_table = payload.get("extra_table", False)
    s.second_match = payload.get("second_match", False)
    s.second_match_extra_table = payload.get("second_match_extra_table", False)
    s.match_start = payload.get("match_start", "")
    s.match_end = payload.get("match_end", "")
    db.session.commit()

    return jsonify({"ok": True})
