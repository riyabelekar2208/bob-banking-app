"""
database.py — All SQLite data-access logic for the banking application.

No other module writes SQL directly; they call the functions defined here.
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash

# Path to the SQLite file, stored alongside this module inside BACKEND/
DB_PATH = os.path.join(os.path.dirname(__file__), "banking.db")


def _get_connection():
    """Open and return a new SQLite connection with row_factory set."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   # Rows accessible as dicts / by column name
    return conn


# ---------------------------------------------------------------------------
# Schema creation + seed data
# ---------------------------------------------------------------------------

def init_db():
    """Create tables if they do not exist, then seed with a default test user."""
    conn = _get_connection()
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS customers (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT    NOT NULL UNIQUE,
            password TEXT    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS accounts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL REFERENCES customers(id),
            balance     REAL    NOT NULL DEFAULT 0.0
        );

        CREATE TABLE IF NOT EXISTS transactions (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL REFERENCES accounts(id),
            type       TEXT    NOT NULL,
            amount     REAL    NOT NULL,
            timestamp  DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()

    # Seed only when no customers exist yet (prevents duplicates on restart)
    cur.execute("SELECT COUNT(*) AS cnt FROM customers")
    if cur.fetchone()["cnt"] == 0:
        hashed = generate_password_hash("password123")
        cur.execute(
            "INSERT INTO customers (username, password) VALUES (?, ?)",
            ("alice", hashed),
        )
        customer_id = cur.lastrowid
        cur.execute(
            "INSERT INTO accounts (customer_id, balance) VALUES (?, ?)",
            (customer_id, 1000.00),
        )
        conn.commit()

    conn.close()


# ---------------------------------------------------------------------------
# Data-access functions
# ---------------------------------------------------------------------------

def get_customer_by_username(username: str):
    """Return the customer row matching *username*, or None."""
    conn = _get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM customers WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    return row


def get_account_by_customer_id(customer_id: int):
    """Return the account row for *customer_id*, or None."""
    conn = _get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM accounts WHERE customer_id = ?", (customer_id,))
    row = cur.fetchone()
    conn.close()
    return row


def update_balance(account_id: int, new_balance: float):
    """Overwrite the balance for *account_id*."""
    conn = _get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE accounts SET balance = ? WHERE id = ?",
        (new_balance, account_id),
    )
    conn.commit()
    conn.close()


def log_transaction(account_id: int, transaction_type: str, amount: float):
    """Insert a new row into the transactions table."""
    conn = _get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO transactions (account_id, type, amount) VALUES (?, ?, ?)",
        (account_id, transaction_type, amount),
    )
    conn.commit()
    conn.close()
