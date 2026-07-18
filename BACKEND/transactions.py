"""
transactions.py — Transactions Blueprint: deposit and withdrawal routes.
"""

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
)
from database import get_account_by_customer_id, update_balance, log_transaction
from auth import login_required

transactions_bp = Blueprint("transactions", __name__)


# ---------------------------------------------------------------------------
# Deposit
# ---------------------------------------------------------------------------

@transactions_bp.route("/deposit", methods=["GET", "POST"])
@login_required
def deposit():
    error = None

    if request.method == "POST":
        raw = request.form.get("amount", "").strip()

        # --- numeric validation ---
        try:
            amount = float(raw)
        except ValueError:
            error = "Please enter a valid numeric amount."
            return render_template("deposit.html", error=error)

        if amount <= 0:
            error = "Deposit amount must be greater than zero."
            return render_template("deposit.html", error=error)

        # --- apply deposit ---
        customer_id = session["user_id"]
        account = get_account_by_customer_id(customer_id)

        new_balance = round(account["balance"] + amount, 2)
        update_balance(account["id"], new_balance)
        log_transaction(account["id"], "deposit", amount)

        flash("Deposit of £{:.2f} was successful.".format(amount), "success")
        return redirect(url_for("accounts.dashboard"))

    return render_template("deposit.html", error=error)


# ---------------------------------------------------------------------------
# Withdraw
# ---------------------------------------------------------------------------

@transactions_bp.route("/withdraw", methods=["GET", "POST"])
@login_required
def withdraw():
    error = None

    if request.method == "POST":
        raw = request.form.get("amount", "").strip()

        if not raw:
            error = "Amount is required"
            return render_template("withdraw.html", error=error)

        try:
            amount = float(raw)
        except ValueError:
            error = "Amount must be greater than zero"
            return render_template("withdraw.html", error=error)

        if amount <= 0:
            error = "Amount must be greater than zero"
            return render_template("withdraw.html", error=error)

        # --- funds check ---
        customer_id = session["user_id"]
        account = get_account_by_customer_id(customer_id)

        if amount > account["balance"]:
            error = "Insufficient funds"
            return render_template("withdraw.html", error=error)

        new_balance = round(account["balance"] - amount, 2)
        update_balance(account["id"], new_balance)
        log_transaction(account["id"], "withdrawal", amount)

        flash("Withdrawal of £{:.2f} was successful.".format(amount), "success")
        return redirect(url_for("accounts.dashboard"))

    return render_template("withdraw.html", error=error)
