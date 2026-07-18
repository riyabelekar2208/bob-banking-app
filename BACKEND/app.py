"""
app.py — Flask application entry point.

Creates the Flask app, registers Blueprints, initialises the database,
and starts the development server when run directly.
"""

import os
import sys

# Make BACKEND importable when running from the BACKEND/ directory
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, redirect, url_for

# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def create_app(db_path: str = None):
    """
    Application factory.  Accepts an optional *db_path* so tests can inject
    an in-memory or temporary database without touching the real banking.db.
    """
    # Resolve paths relative to this file so the app works regardless of where
    # it is launched from.
    base_dir = os.path.dirname(__file__)
    frontend_dir = os.path.join(base_dir, "..", "FRONTEND")

    app = Flask(
        __name__,
        template_folder=os.path.join(frontend_dir, "templates"),
        static_folder=os.path.join(frontend_dir, "static"),
    )

    # Secret key — read from environment, fall back to dev default
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

    # Allow tests to override the database path
    if db_path is not None:
        app.config["DB_PATH"] = db_path

    # -----------------------------------------------------------------------
    # Register Blueprints
    # -----------------------------------------------------------------------
    from auth import auth_bp
    from accounts import accounts_bp
    from transactions import transactions_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(accounts_bp)
    app.register_blueprint(transactions_bp)

    # -----------------------------------------------------------------------
    # Root redirect → /login
    # -----------------------------------------------------------------------
    @app.route("/")
    def index():
        return redirect(url_for("auth.login"))

    # -----------------------------------------------------------------------
    # Initialise database inside application context
    # -----------------------------------------------------------------------
    with app.app_context():
        import database
        if db_path is not None:
            database.DB_PATH = db_path
        database.init_db()

    return app


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
