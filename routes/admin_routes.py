from flask import Blueprint, render_template, request, session, redirect, url_for
import os

admin_bp = Blueprint("admin", __name__)
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

@admin_bp.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["is_admin"] = True
            return redirect(url_for("main_bp.index"))  # ✅ updated
        return render_template("admin_login.html", error="Wrong password")
    return render_template("admin_login.html", error=None)

@admin_bp.route("/admin-logout")
def admin_logout():
    session["is_admin"] = False
    return redirect(url_for("main_bp.index"))
