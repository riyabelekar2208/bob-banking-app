# Banking Web Application — Implementation Plan

> **Planning Level Document**
> This document describes *what* to build and *why*. It does not contain database schemas,
> SQL scripts, API contracts, or detailed code-level implementation steps.

---

## 1. Solution Overview

### Objective

Build a lightweight, browser-based banking web application that allows customers to securely
log in, view their account balance, and perform basic deposit and withdrawal transactions.

### Scope

| In Scope | Out of Scope |
|---|---|
| Customer login / logout | Account registration / self-service sign-up |
| View account balance | Multi-account management per customer |
| Deposit funds | External bank transfers or payment gateways |
| Withdraw funds | Admin or teller role management |
| Session-based security | Two-factor authentication |
| Local SQLite persistence | Production database (PostgreSQL, MySQL) |

### Users

| User Type | Description |
|---|---|
| **Customer** | Authenticated bank customer who can view balances and perform transactions |

### Functional Requirements

1. A customer can log in using a username and password.
2. A customer is redirected to a personal dashboard after successful login.
3. The dashboard displays the customer's current account balance.
4. A customer can deposit a positive monetary amount into their account.
5. A customer can withdraw a positive monetary amount, provided sufficient funds exist.
6. A customer can log out, terminating their session.
7. Unauthenticated requests to protected pages are redirected to the login page.

### Non-Functional Requirements

| Category | Requirement |
|---|---|
| **Security** | Passwords must be stored hashed (never plain text); sessions must be invalidated on logout |
| **Usability** | UI must be responsive and usable on desktop browsers using Bootstrap |
| **Portability** | Application must run locally with minimal setup (Python 3.11, no external DB server) |
| **Testability** | Backend logic must be structured to support pytest-based unit tests |
| **Maintainability** | Code separated by concern: frontend, backend, and data layers are distinct |

### Assumptions

- A small set of customer accounts will be pre-seeded; there is no self-registration flow.
- SQLite is sufficient for local/demo use; no concurrency or scaling requirements apply.
- The CI pipeline defined in [`banking-app-ci.yml`](docs/demo-setup/banking-app-ci.yml) is the
  target CI environment (Python 3.11, Flask, Werkzeug, pytest).
- Bootstrap is loaded via CDN; no build toolchain (Webpack, npm) is required.
- A single browser session per customer is assumed; no concurrent session handling is needed.

---

## 2. High-Level Architecture

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                        BROWSER                          │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │              FRONTEND  (HTML + Bootstrap)        │   │
│  │  login.html │ dashboard.html │ deposit/withdraw  │   │
│  └──────────────────┬───────────────────────────────┘   │
└─────────────────────┼───────────────────────────────────┘
                      │  HTTP Requests (form POST / GET)
                      ▼
┌─────────────────────────────────────────────────────────┐
│                   BACKEND  (Python Flask)               │
│                                                         │
│   ┌────────────┐  ┌──────────────┐  ┌───────────────┐  │
│   │ Auth Routes│  │ Account      │  │ Transaction   │  │
│   │ /login     │  │ Routes       │  │ Routes        │  │
│   │ /logout    │  │ /dashboard   │  │ /deposit      │  │
│   └────────────┘  │ /balance     │  │ /withdraw     │  │
│                   └──────────────┘  └───────────────┘  │
│                                                         │
│   ┌─────────────────────────────────────────────────┐   │
│   │            Session Management (Flask session)   │   │
│   └─────────────────────────────────────────────────┘   │
│                                                         │
│   ┌─────────────────────────────────────────────────┐   │
│   │           Data Access Layer                     │   │
│   └───────────────────────┬─────────────────────────┘   │
└───────────────────────────┼─────────────────────────────┘
                            │  SQLite queries
                            ▼
┌─────────────────────────────────────────────────────────┐
│              DATABASE  (SQLite)                         │
│                                                         │
│   customers table │ accounts table │ transactions table │
└─────────────────────────────────────────────────────────┘
```

### Frontend → Backend → Database Interaction

```
Browser Form Submit
       │
       ▼
Flask Route Handler
       │
       ├── Validates session / input
       │
       ├── Calls Data Access Layer
       │         │
       │         └── Reads / writes SQLite
       │
       └── Renders HTML template (Jinja2) or redirects
```

### Request Lifecycle

| Step | Actor | Action |
|---|---|---|
| 1 | Browser | User submits a form (login, deposit, withdraw) |
| 2 | Flask | Route handler receives and validates the request |
| 3 | Flask | Checks session authentication; rejects if not logged in |
| 4 | Flask | Calls data access functions to read or mutate the database |
| 5 | SQLite | Returns query results or confirms write success |
| 6 | Flask | Renders the appropriate Jinja2 HTML template with data |
| 7 | Browser | Displays the rendered page to the customer |

---

## 3. Component Design

### Frontend Responsibilities

- Render all customer-facing pages using HTML + Bootstrap 5 (via CDN).
- Provide forms for: login, deposit amount entry, withdrawal amount entry.
- Display feedback messages: success confirmations, error messages (invalid credentials,
  insufficient funds, invalid input).
- Enforce basic client-side input constraints (e.g. positive numbers only) where appropriate.
- Use Jinja2 template inheritance to share a common layout (navbar, header, footer).
- Handle logout via a link/button that calls the logout route.

### Backend Responsibilities

- Define Flask routes for all application actions (login, logout, dashboard, deposit, withdraw).
- Manage user sessions: create on login, destroy on logout, verify on every protected route.
- Hash passwords using Werkzeug's security utilities; never store or compare plain text passwords.
- Validate all incoming form data server-side before touching the database.
- Return appropriate HTTP redirects after state-changing operations (POST-Redirect-GET pattern).
- Pass structured data (balance, customer name, messages) to templates via the render context.

### Database Responsibilities

- Persist customer credentials (username + hashed password).
- Persist account balance associated with each customer.
- Record a transaction log for every deposit and withdrawal (amount, type, timestamp).
- Provide simple query interfaces consumed by the backend data access layer.

---

## 4. Folder Structure

```
banking-workshop/
├── BACKEND/
│   ├── app.py                  # Flask application entry point; registers routes
│   ├── auth.py                 # Login / logout route handlers and session logic
│   ├── accounts.py             # Dashboard and balance route handlers
│   ├── transactions.py         # Deposit and withdrawal route handlers
│   ├── database.py             # SQLite connection setup and data access functions
│   ├── requirements.txt        # Python dependencies (flask, werkzeug)
│   └── banking.db              # SQLite database file (generated at runtime)
│
├── FRONTEND/
│   ├── templates/
│   │   ├── base.html           # Shared layout: Bootstrap CDN, navbar, flash messages
│   │   ├── login.html          # Login form page
│   │   ├── dashboard.html      # Balance display + navigation to deposit/withdraw
│   │   ├── deposit.html        # Deposit amount form
│   │   └── withdraw.html       # Withdrawal amount form
│   └── static/
│       └── style.css           # Optional custom styles layered on Bootstrap
│
├── tests/
│   └── test_app.py             # pytest unit tests for backend route and logic behaviour
│
└── docs/
    └── demo-setup/
        ├── banking-app-ci.yml  # GitHub Actions CI pipeline (existing)
        ├── GITHUB-MCP-SETUP.md # MCP demo setup guide (existing)
        └── mcp-github-template.json  # MCP config template (existing)
```

### Responsibility of Each Folder

| Folder | Responsibility |
|---|---|
| `BACKEND/` | All Python/Flask source code: routing, business logic, data access, database file |
| `FRONTEND/templates/` | Jinja2 HTML pages rendered and served by Flask |
| `FRONTEND/static/` | Static assets (CSS) served directly by Flask |
| `tests/` | pytest test files for backend behaviour; required by the CI pipeline |
| `docs/demo-setup/` | Workshop documentation and CI/CD configuration |

---

## 5. Module Breakdown

### Authentication Module

**Purpose:** Control who can access the application.

| Concern | Description |
|---|---|
| Login | Accept username + password; verify against hashed credential in DB; create session on success |
| Session guard | Decorator or inline check on every protected route; redirect to login if no active session |
| Logout | Clear the Flask session; redirect to login page |
| Password security | Use `werkzeug.security.generate_password_hash` / `check_password_hash` |

**Pages involved:** `login.html`
**Routes involved:** `GET /login`, `POST /login`, `POST /logout`

---

### Dashboard Module

**Purpose:** Give the authenticated customer a home screen that summarises their account.

| Concern | Description |
|---|---|
| Balance display | Query the account balance for the logged-in customer and pass to template |
| Navigation | Provide clear links/buttons to deposit and withdraw actions |
| Welcome message | Display the customer's name for personalisation |

**Pages involved:** `dashboard.html`
**Routes involved:** `GET /dashboard`

---

### Account Management Module

**Purpose:** Expose account balance information to the customer.

| Concern | Description |
|---|---|
| Balance retrieval | Read current balance from the database for the authenticated customer |
| Customer identity | Resolve customer name and account details from the session user ID |

**Pages involved:** `dashboard.html` (balance is displayed here)
**Routes involved:** Served as part of `GET /dashboard`

---

### Transactions Module

**Purpose:** Allow the customer to change their account balance through deposits and withdrawals.

| Concern | Description |
|---|---|
| Deposit | Validate positive amount; add to balance; write transaction record; redirect to dashboard |
| Withdrawal | Validate positive amount; check sufficient funds; deduct from balance; write transaction record; redirect to dashboard |
| Input validation | Reject non-numeric, zero, or negative amounts with a user-visible error message |
| Insufficient funds | Detect when withdrawal amount exceeds balance; surface error without modifying the DB |
| Transaction log | Record every completed deposit/withdrawal with amount, type, and timestamp |

**Pages involved:** `deposit.html`, `withdraw.html`
**Routes involved:** `GET /deposit`, `POST /deposit`, `GET /withdraw`, `POST /withdraw`

---

## 6. Implementation Roadmap

### Development Phases

```
Phase 1 — Project Scaffolding
  └── Create BACKEND/ and FRONTEND/ folders
  └── Set up Flask app entry point
  └── Wire up template folder to Flask (point to FRONTEND/templates)
  └── Create requirements.txt
  └── Create and seed the SQLite database with at least one test customer

Phase 2 — Authentication
  └── Build login route (GET + POST)
  └── Implement password hashing and session creation
  └── Build logout route
  └── Add session guard to protect all non-login routes
  └── Create login.html template

Phase 3 — Dashboard & Account View
  └── Build dashboard route
  └── Query and display customer name and current balance
  └── Create dashboard.html template with navigation

Phase 4 — Transactions
  └── Build deposit route (GET + POST) with validation
  └── Build withdraw route (GET + POST) with validation and funds check
  └── Write transaction log records on success
  └── Create deposit.html and withdraw.html templates
  └── Surface success and error flash messages

Phase 5 — Polish & Testing
  └── Refine Bootstrap layout and shared base.html
  └── Add optional custom styles in static/style.css
  └── Write pytest tests covering: login success/failure, deposit, withdrawal,
      insufficient funds, unauthenticated access
  └── Verify CI pipeline passes (banking-app-ci.yml)
```

### Estimated Effort

| Phase | Relative Effort |
|---|---|
| Phase 1 — Scaffolding | Low |
| Phase 2 — Authentication | Medium |
| Phase 3 — Dashboard & Balance | Low |
| Phase 4 — Transactions | Medium |
| Phase 5 — Polish & Testing | Medium |

### Dependencies

```
Phase 1 must complete before any other phase begins.
Phase 2 (Auth) must complete before Phase 3 or Phase 4.
Phase 3 (Dashboard) must complete before Phase 4 (Transactions link back to dashboard).
Phase 5 (Testing) depends on Phase 2, 3, and 4 being functionally complete.
```

| Phase | Depends On |
|---|---|
| Phase 2 | Phase 1 |
| Phase 3 | Phase 2 |
| Phase 4 | Phase 3 |
| Phase 5 | Phase 2, 3, 4 |

---

## Sub-Tasks for Implementation

> Each sub-task below maps to one development phase and is designed to be implemented
> and reviewed independently.

---

### Sub-Task 1 — Project Scaffolding

**Intent:** Establish the complete folder skeleton and wired-up Flask entry point so all
subsequent phases have a functioning base to build on.

**Expected Outcomes:**
- `BACKEND/` and `FRONTEND/templates/` and `FRONTEND/static/` directories exist.
- Flask app starts without errors and serves a placeholder route.
- `requirements.txt` is present with `flask` and `werkzeug`.
- SQLite database file is created and seeded with at least one test customer account.

**Todo List:**
1. Create `BACKEND/`, `FRONTEND/templates/`, `FRONTEND/static/` directories.
2. Create `BACKEND/app.py` as Flask entry point; configure template and static folder paths.
3. Create `BACKEND/database.py` with database initialisation and seeding logic.
4. Create `BACKEND/requirements.txt` listing `flask` and `werkzeug`.
5. Create `FRONTEND/templates/base.html` with Bootstrap 5 CDN and flash message block.

**Status:** `[ ] pending`

---

### Sub-Task 2 — Authentication

**Intent:** Enable customers to log in and log out securely, and prevent unauthenticated
access to all protected pages.

**Expected Outcomes:**
- `GET /login` renders the login form.
- `POST /login` with valid credentials creates a session and redirects to `/dashboard`.
- `POST /login` with invalid credentials re-renders login with an error message.
- `POST /logout` clears the session and redirects to `/login`.
- Visiting any protected route without a session redirects to `/login`.

**Todo List:**
1. Create `BACKEND/auth.py` with login and logout route handlers.
2. Implement password verification using `werkzeug.security.check_password_hash`.
3. Implement session creation (`session['user_id']`) on successful login.
4. Add a `login_required` guard (function or decorator) reusable across all protected routes.
5. Register auth blueprint/routes in `app.py`.
6. Create `FRONTEND/templates/login.html` with a username/password form.

**Status:** `[ ] pending`

---

### Sub-Task 3 — Dashboard & Balance View

**Intent:** Give the logged-in customer a personalised home page that displays their
current account balance and navigation options.

**Expected Outcomes:**
- `GET /dashboard` (authenticated) renders the customer's name and current balance.
- Unauthenticated `GET /dashboard` redirects to `/login`.
- Dashboard page includes clearly labelled links to Deposit and Withdraw.

**Todo List:**
1. Create `BACKEND/accounts.py` with the dashboard route handler.
2. Query customer name and balance from the database using the session user ID.
3. Pass name and balance to the template render context.
4. Register accounts blueprint/routes in `app.py`.
5. Create `FRONTEND/templates/dashboard.html` displaying balance and action links.

**Status:** `[ ] pending`

---

### Sub-Task 4 — Transactions (Deposit & Withdraw)

**Intent:** Allow customers to increase or decrease their balance, with validation and
an audit trail for every operation.

**Expected Outcomes:**
- `GET /deposit` renders the deposit form.
- `POST /deposit` with a valid positive amount updates the balance, logs the transaction, and redirects to dashboard with a success message.
- `POST /deposit` with an invalid amount re-renders the form with an error.
- `GET /withdraw` renders the withdrawal form.
- `POST /withdraw` with a valid amount and sufficient funds updates the balance, logs the transaction, and redirects to dashboard with a success message.
- `POST /withdraw` with insufficient funds shows an error without modifying the balance.

**Todo List:**
1. Create `BACKEND/transactions.py` with deposit and withdraw route handlers.
2. Add server-side input validation (numeric, positive, non-zero).
3. Implement balance update and transaction log write in `database.py`.
4. Implement insufficient-funds check before any withdrawal write.
5. Use Flask's `flash()` for success and error user feedback.
6. Register transactions blueprint/routes in `app.py`.
7. Create `FRONTEND/templates/deposit.html` and `FRONTEND/templates/withdraw.html`.

**Status:** `[ ] pending`

---

### Sub-Task 5 — Polish & Testing

**Intent:** Ensure consistent UI presentation and verify all critical backend behaviours
through automated tests compatible with the existing CI pipeline.

**Expected Outcomes:**
- All pages share a consistent Bootstrap layout via `base.html`.
- `tests/test_app.py` contains pytest tests covering: login success, login failure,
  deposit, withdrawal, insufficient-funds rejection, and unauthenticated redirect.
- Running `pytest tests/ -v` locally passes all tests.
- The GitHub Actions workflow in `banking-app-ci.yml` passes.

**Todo List:**
1. Finalise `FRONTEND/templates/base.html` (navbar with logout, flash message display).
2. Add optional custom styles to `FRONTEND/static/style.css`.
3. Create `tests/test_app.py` with a pytest fixture that creates a test Flask client.
4. Write test cases for each critical behaviour listed in expected outcomes.
5. Ensure `BACKEND/app.py` exposes the Flask `app` object for test import.
6. Validate that the CI pipeline configuration aligns with the final project structure.

**Status:** `[ ] pending`
