"""
auth.py — Authentication Blueprint: login, logout, and login_required guard.
"""

import functools
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
)
from werkzeug.security import check_password_hash
from database import get_customer_by_username

auth_bp = Blueprint("auth", __name__)


# ---------------------------------------------------------------------------
# login_required decorator
# ---------------------------------------------------------------------------

def login_required(view):
    """Redirect unauthenticated requests to /login."""
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)
    return wrapped


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # If already logged in, send straight to dashboard
    if session.get("user_id"):
        return redirect(url_for("accounts.dashboard"))

    error = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # --- basic presence checks ---
        if not username or not password:
            error = "Invalid credentials."
        else:
            customer = get_customer_by_username(username)

            if customer is None or not check_password_hash(customer["password"], password):
                # Generic message — do NOT reveal which field was wrong
                error = "Invalid credentials."
            else:
                session.clear()
                session["user_id"] = customer["id"]
                flash("Welcome back, {}!".format(customer["username"]), "success")
                return redirect(url_for("accounts.dashboard"))

    return render_template("login.html", error=error)


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
