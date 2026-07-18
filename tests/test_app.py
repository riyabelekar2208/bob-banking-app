"""
tests/test_app.py — pytest test suite for the banking application.

Covers:
  - Unit tests: authentication (login success/failure), transaction validation
  - Integration tests: full login→dashboard flow, deposit/withdraw flow,
    session isolation, unauthenticated redirect
"""

import sys
import os
import tempfile
import pytest

# ---------------------------------------------------------------------------
# Ensure BACKEND is on the Python path so we can import the app
# ---------------------------------------------------------------------------
BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..", "BACKEND")
sys.path.insert(0, os.path.abspath(BACKEND_DIR))


@pytest.fixture
def app():
    """
    Create the Flask application wired to a temporary SQLite file so tests
    never touch the development banking.db.
    """
    # Use a temp file (not :memory:) so the same DB is shared across connections
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)

    from app import create_app
    flask_app = create_app(db_path=db_path)
    flask_app.config["TESTING"] = True
    flask_app.config["WTF_CSRF_ENABLED"] = False

    yield flask_app

    # Teardown — remove the temp database
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Test client backed by the test-isolated Flask app."""
    return app.test_client()


@pytest.fixture
def auth_client(client):
    """A test client that is already logged in as the seed user (alice)."""
    client.post("/login", data={"username": "alice", "password": "password123"})
    return client


# ===========================================================================
# Helper
# ===========================================================================

def login(client, username="alice", password="password123"):
    return client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=False,
    )


# ===========================================================================
# 1. Authentication — Unit Tests
# ===========================================================================

class TestLogin:

    def test_login_page_get(self, client):
        """GET /login returns 200 with the sign-in form."""
        response = client.get("/login")
        assert response.status_code == 200
        assert b"Sign In" in response.data

    def test_login_success_redirects_to_dashboard(self, client):
        """Valid credentials redirect to /dashboard."""
        response = login(client)
        assert response.status_code == 302
        assert "/dashboard" in response.headers["Location"]

    def test_login_success_sets_session(self, app, client):
        """Session contains user_id after successful login."""
        with client.session_transaction() as sess:
            assert "user_id" not in sess

        login(client)

        with client.session_transaction() as sess:
            assert "user_id" in sess

    def test_login_wrong_password(self, client):
        """Wrong password re-renders the form (200) with a generic error."""
        response = client.post(
            "/login",
            data={"username": "alice", "password": "wrongpassword"},
            follow_redirects=False,
        )
        assert response.status_code == 200
        assert b"Invalid credentials" in response.data

    def test_login_unknown_username(self, client):
        """Unknown username re-renders the form with a generic error."""
        response = client.post(
            "/login",
            data={"username": "nobody", "password": "anything"},
            follow_redirects=False,
        )
        assert response.status_code == 200
        assert b"Invalid credentials" in response.data

    def test_login_blank_fields(self, client):
        """Blank submission should show an error, not crash."""
        response = client.post(
            "/login",
            data={"username": "", "password": ""},
            follow_redirects=False,
        )
        assert response.status_code == 200
        assert b"Invalid credentials" in response.data

    def test_logout_clears_session(self, auth_client):
        """POST /logout clears the session and redirects to /login."""
        with auth_client.session_transaction() as sess:
            assert "user_id" in sess

        response = auth_client.post("/logout", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

        with auth_client.session_transaction() as sess:
            assert "user_id" not in sess


# ===========================================================================
# 2. Transactions — Unit Tests
# ===========================================================================

class TestDeposit:

    def test_deposit_get(self, auth_client):
        """GET /deposit returns the deposit form (200)."""
        response = auth_client.get("/deposit")
        assert response.status_code == 200
        assert b"Deposit" in response.data

    def test_deposit_valid_increases_balance(self, app, auth_client):
        """A valid deposit amount increases the account balance."""
        response = auth_client.post(
            "/deposit",
            data={"amount": "250.00"},
            follow_redirects=False,
        )
        assert response.status_code == 302  # redirects to dashboard

        # Verify balance in the database directly
        import database
        with auth_client.application.app_context():
            from database import get_account_by_customer_id, _get_connection
            conn = _get_connection()
            cur = conn.cursor()
            cur.execute("SELECT id FROM customers WHERE username = 'alice'")
            cid = cur.fetchone()["id"]
            conn.close()
            account = get_account_by_customer_id(cid)
            assert round(account["balance"], 2) == 1250.00

    def test_deposit_zero_rejected(self, auth_client):
        """A deposit of zero is rejected with an error message."""
        response = auth_client.post(
            "/deposit",
            data={"amount": "0"},
            follow_redirects=False,
        )
        assert response.status_code == 200
        assert b"greater than zero" in response.data

    def test_deposit_negative_rejected(self, auth_client):
        """A negative deposit amount is rejected."""
        response = auth_client.post(
            "/deposit",
            data={"amount": "-50"},
            follow_redirects=False,
        )
        assert response.status_code == 200
        assert b"greater than zero" in response.data

    def test_deposit_non_numeric_rejected(self, auth_client):
        """Non-numeric input is rejected."""
        response = auth_client.post(
            "/deposit",
            data={"amount": "abc"},
            follow_redirects=False,
        )
        assert response.status_code == 200
        assert b"valid numeric amount" in response.data


class TestWithdraw:

    def test_withdraw_get(self, auth_client):
        """GET /withdraw returns the withdrawal form (200)."""
        response = auth_client.get("/withdraw")
        assert response.status_code == 200
        assert b"Withdraw" in response.data

    def test_withdraw_valid_decreases_balance(self, app, auth_client):
        """A valid withdrawal decreases the account balance."""
        auth_client.post("/withdraw", data={"amount": "100.00"}, follow_redirects=False)

        import database
        with auth_client.application.app_context():
            from database import get_account_by_customer_id, _get_connection
            conn = _get_connection()
            cur = conn.cursor()
            cur.execute("SELECT id FROM customers WHERE username = 'alice'")
            cid = cur.fetchone()["id"]
            conn.close()
            account = get_account_by_customer_id(cid)
            assert round(account["balance"], 2) == 900.00

    def test_withdraw_insufficient_funds(self, auth_client):
        """Withdrawing more than the balance is rejected."""
        response = auth_client.post(
            "/withdraw",
            data={"amount": "5000.00"},
            follow_redirects=False,
        )
        assert response.status_code == 200
        assert b"Insufficient funds" in response.data

    def test_withdraw_exact_balance_succeeds(self, app, auth_client):
        """Withdrawing exactly the current balance succeeds (zero result)."""
        response = auth_client.post(
            "/withdraw",
            data={"amount": "1000.00"},
            follow_redirects=False,
        )
        assert response.status_code == 302

        import database
        with auth_client.application.app_context():
            from database import get_account_by_customer_id, _get_connection
            conn = _get_connection()
            cur = conn.cursor()
            cur.execute("SELECT id FROM customers WHERE username = 'alice'")
            cid = cur.fetchone()["id"]
            conn.close()
            account = get_account_by_customer_id(cid)
            assert round(account["balance"], 2) == 0.00

    def test_withdraw_zero_rejected(self, auth_client):
        response = auth_client.post(
            "/withdraw",
            data={"amount": "0"},
            follow_redirects=False,
        )
        assert response.status_code == 200
        assert b"greater than zero" in response.data

    def test_withdraw_non_numeric_rejected(self, auth_client):
        response = auth_client.post(
            "/withdraw",
            data={"amount": "xyz"},
            follow_redirects=False,
        )
        assert response.status_code == 200
        assert b"valid numeric amount" in response.data


# ===========================================================================
# 3. Integration Tests
# ===========================================================================

class TestIntegration:

    def test_root_redirects_to_login(self, client):
        """/ redirects to /login."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_unauthenticated_dashboard_redirects(self, client):
        """Unauthenticated GET /dashboard redirects to /login (302)."""
        response = client.get("/dashboard", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_unauthenticated_deposit_redirects(self, client):
        """Unauthenticated GET /deposit redirects to /login."""
        response = client.get("/deposit", follow_redirects=False)
        assert response.status_code == 302

    def test_unauthenticated_withdraw_redirects(self, client):
        """Unauthenticated GET /withdraw redirects to /login."""
        response = client.get("/withdraw", follow_redirects=False)
        assert response.status_code == 302

    def test_full_login_dashboard_flow(self, client):
        """Log in successfully, then view dashboard with name and balance."""
        login(client)  # sets session
        response = client.get("/dashboard", follow_redirects=True)
        assert response.status_code == 200
        assert b"alice" in response.data.lower()
        assert b"1000.00" in response.data

    def test_full_deposit_flow(self, client):
        """Login → deposit → dashboard shows updated balance."""
        login(client)
        client.post("/deposit", data={"amount": "500"}, follow_redirects=True)
        response = client.get("/dashboard", follow_redirects=True)
        assert b"1500.00" in response.data

    def test_session_isolation_after_logout(self, client):
        """After logout, /dashboard redirects back to /login."""
        login(client)
        client.post("/logout")
        response = client.get("/dashboard", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_already_logged_in_redirects_from_login(self, auth_client):
        """Visiting /login while authenticated redirects to /dashboard."""
        response = auth_client.get("/login", follow_redirects=False)
        assert response.status_code == 302
        assert "/dashboard" in response.headers["Location"]
