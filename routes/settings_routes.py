from flask import Blueprint, jsonify, request, session
from models import Settings
from extensions import db

settings_bp = Blueprint("settings_bp", __name__)

@settings_bp.route("/update-settings", methods=["POST"])
def update_settings_route():
    if not session.get("is_admin"):
        return jsonify({"ok": False, "error": "Unauthorized"}), 401
    
    payload = request.json
    s = Settings.query.first()
    
    if not s:
        return jsonify({"ok": False, "error": "Settings not found"}), 404
    
    # Validate time range
    event_start = payload.get("event_start", "")
    event_end = payload.get("event_end", "")
    
    if event_start and event_end:
        try:
            start_parts = event_start.split(':')
            end_parts = event_end.split(':')
            start_minutes = int(start_parts[0]) * 60 + int(start_parts[1])
            end_minutes = int(end_parts[0]) * 60 + int(end_parts[1])
            
            if end_minutes <= start_minutes:
                return jsonify({
                    "ok": False, 
                    "error": "End time must be after start time"
                }), 400
        except (ValueError, IndexError):
            return jsonify({
                "ok": False, 
                "error": "Invalid time format"
            }), 400
    
    # Update event settings
    s.event_day = payload.get("event_day", False)
    s.event_name = payload.get("event_name", "Match").strip() or "Match"
    s.event_start = event_start
    s.event_end = event_end
    s.extra_table = payload.get("extra_table", False)
    s.second_event = payload.get("second_event", False)
    s.second_event_extra_table = payload.get("second_event_extra_table", False)
    
    # Backward compatibility - sync old fields with new ones
    s.match_day = s.event_day
    s.match_start = s.event_start
    s.match_end = s.event_end
    s.second_match = s.second_event
    s.second_match_extra_table = s.second_event_extra_table
    
    try:
        db.session.commit()
        return jsonify({"ok": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500