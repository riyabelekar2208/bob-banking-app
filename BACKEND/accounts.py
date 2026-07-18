"""
accounts.py — Accounts Blueprint: customer dashboard view.
"""

from flask import Blueprint, render_template, session
from database import get_account_by_customer_id, get_customer_by_username
from auth import login_required

accounts_bp = Blueprint("accounts", __name__)


@accounts_bp.route("/dashboard")
@login_required
def dashboard():
    customer_id = session["user_id"]

    # Retrieve account for the logged-in customer
    account = get_account_by_customer_id(customer_id)

    # Retrieve customer row to get the username for the welcome message
    # (We stored user_id, so we need to fetch the customer row)
    from database import _get_connection
    conn = _get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
    customer = cur.fetchone()
    conn.close()

    balance = round(account["balance"], 2) if account else 0.0

    return render_template(
        "dashboard.html",
        username=customer["username"] if customer else "User",
        balance="{:.2f}".format(balance),
    )
