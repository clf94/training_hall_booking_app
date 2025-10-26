from flask import Blueprint, render_template, session
from datetime import date
from models import Settings
from utils import load_users

main_bp = Blueprint("main_bp", __name__)

@main_bp.route("/")
def index():
    users = load_users()
    settings = Settings.query.first()
    return render_template(
        "index.html",
        users=users,
        date=date.today(),
        is_admin=session.get("is_admin", False),
        match_day=settings.match_day if settings else False,
        extra_table=settings.extra_table if settings else False,
        second_match=settings.second_match if settings else False,
        second_match_extra_table=settings.second_match_extra_table if settings else False,
        match_start=settings.match_start if settings else "",
        match_end=settings.match_end if settings else ""
    )
