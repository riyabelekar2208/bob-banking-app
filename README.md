# Banking Web Application

A full-stack banking demo built with **Flask** (Python), **SQLite**, **Bootstrap 5**, and **Jinja2** templates.

---

## Features

| Feature | Details |
|---|---|
| User authentication | Login / logout with hashed passwords (Werkzeug) |
| Session management | Secure Flask signed-cookie sessions |
| Dashboard | Displays customer name and current balance |
| Deposit | Add funds with full server-side validation |
| Withdraw | Remove funds with insufficient-funds guard |
| Transaction log | Every deposit/withdrawal is persisted to the DB |
| Flash messages | Success/error feedback on every action |

---

## Project Structure

```
banking-workshop/
├── BACKEND/
│   ├── app.py             # Flask factory + entry-point
│   ├── auth.py            # Login, logout, login_required
│   ├── accounts.py        # Dashboard route
│   ├── transactions.py    # Deposit & withdraw routes
│   ├── database.py        # SQLite schema, seed data, data-access functions
│   └── requirements.txt   # Python dependencies
├── FRONTEND/
│   ├── templates/
│   │   ├── base.html      # Shared Bootstrap layout + navbar + flash block
│   │   ├── login.html
│   │   ├── dashboard.html
│   │   ├── deposit.html
│   │   └── withdraw.html
│   └── static/
│       └── style.css
├── tests/
│   └── test_app.py        # pytest: unit + integration tests (26 tests)
└── .venv/                 # Virtual environment (not committed)
```

---

## Quickstart

### 1. Prerequisites

- Python 3.11 or later
- `pip` (bundled with Python 3.11+)

### 2. Create & activate a virtual environment

```powershell
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r BACKEND/requirements.txt
```

### 4. Run the application

```bash
cd BACKEND
python app.py
```

Flask starts on **http://127.0.0.1:5000**.

The SQLite database file (`BACKEND/banking.db`) is created automatically on first run and seeded with:

| Username | Password |
|---|---|
| alice | password123 |

### 5. Open the app

Navigate to `http://127.0.0.1:5000` in your browser.  
You will be redirected to `/login` automatically.

---

## Running the Tests

From the project root (with the virtual environment active):

```bash
python -m pytest tests/test_app.py -v
```

Expected output: **26 passed**.

---

## Environment Variables

| Variable | Purpose | Default |
|---|---|---|
| `SECRET_KEY` | Flask session signing key | `dev-secret-key-change-in-production` |

Set this to a long random string before deploying anywhere beyond `localhost`.

---

## Validation Summary

- **Login** — blank fields and invalid credentials show "Invalid credentials" (generic, no enumeration)
- **Deposit** — must be a positive numeric value
- **Withdrawal** — must be a positive numeric value and must not exceed current balance
- **All protected routes** — unauthenticated requests redirect to `/login`

---

## Production Notes

- Replace `app.run(debug=True)` with **Gunicorn** (Linux/macOS) or **Waitress** (Windows)
- Set `SECRET_KEY` via environment variable
- Migrate from SQLite to **PostgreSQL** or **MySQL** for multi-user workloads
- Serve over **HTTPS** via a reverse proxy (Nginx / cloud load-balancer)
