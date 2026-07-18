"""
transactions.py — Transactions Blueprint: deposit and withdrawal routes.
"""

from decimal import Decimal, InvalidOperation
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
)
from database import get_account_by_customer_id, update_balance, log_transaction, withdraw_atomic
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

        flash("Deposit of \u00a3{:.2f} was successful.".format(amount), "success")
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

        # Issue 1 fix: empty check
        if not raw:
            error = "Amount is required"
            return render_template("withdraw.html", error=error)

        # Issue 2 & 3 fix: use Decimal for money; give accurate error for non-numeric input
        try:
            amount = Decimal(raw)
        except InvalidOperation:
            error = "Please enter a valid numeric amount"
            return render_template("withdraw.html", error=error)

        # Issue 2 check: must be positive
        if amount <= 0:
            error = "Amount must be greater than zero"
            return render_template("withdraw.html", error=error)

        # Issue 4 fix: minimum withdrawal floor
        if amount < Decimal("0.01"):
            error = "Minimum withdrawal amount is \u00a30.01"
            return render_template("withdraw.html", error=error)

        # Issue 1 fix: pre-flight balance check (fast fail before acquiring lock)
        customer_id = session["user_id"]
        account = get_account_by_customer_id(customer_id)

        if amount > Decimal(str(account["balance"])):
            error = "Insufficient funds"
            return render_template("withdraw.html", error=error)

        # Issue 1 fix: atomic read-lock-deduct-log in one SQLite transaction
        success = withdraw_atomic(account["id"], amount)
        if not success:
            # Another concurrent request won the race — balance now insufficient
            error = "Insufficient funds"
            return render_template("withdraw.html", error=error)

        flash("Withdrawal of \u00a3{:.2f} was successful.".format(amount), "success")
        return redirect(url_for("accounts.dashboard"))

    return render_template("withdraw.html", error=error)
