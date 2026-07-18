# Step-by-Step Implementation Guide
## Banking Web Application

> **What this guide is:** Plain-English instructions explaining *how* to implement each
> part of the application and *why* each decision is made.
> This guide does **not** contain full source code — it explains the logic so you can
> write the code yourself, follow a code-generation tool, or implement it in any order.

---

## Table of Contents

1. [Environment Setup](#1-environment-setup)
2. [Backend Implementation](#2-backend-implementation)
3. [Frontend Implementation](#3-frontend-implementation)
4. [Integration Steps](#4-integration-steps)
5. [Validation Rules](#5-validation-rules)
6. [Testing](#6-testing)
7. [Deployment](#7-deployment)

---

## 1. Environment Setup

### 1.1 Prerequisites

Before writing any code, confirm you have the following installed on your machine:

- **Python 3.11 or later** — the runtime for Flask. Check by running `python --version`
  in your terminal.
- **pip** — Python's package installer. It ships with Python 3.11. Check with
  `pip --version`.
- A code editor of your choice (VS Code is recommended).

---

### 1.2 Create a Virtual Environment

A virtual environment is an isolated Python installation specific to this project. This
prevents package conflicts with other Python projects on your machine.

1. Open a terminal and navigate to the root of the project folder (`banking-workshop/`).
2. Create the virtual environment by telling Python to produce a hidden folder (commonly
   named `.venv`) that holds its own copy of Python and pip.
3. **Activate** the environment before installing anything. The activation command differs
   by operating system:
   - On **Windows**, you run the `activate` script inside `.venv\Scripts\`.
   - On **macOS/Linux**, you `source` the `.venv/bin/activate` file.
4. Once activated, your terminal prompt will show the environment name, confirming that
   any packages you install go into that isolated folder and not your system Python.

> **Rule of thumb:** Always activate the virtual environment before starting work on this
> project. Every terminal session needs to be activated separately.

---

### 1.3 Install Dependencies

All Python packages the app needs are declared in a single file: `BACKEND/requirements.txt`.

The file should list exactly two packages:
- **flask** — the web framework that handles routing, templates, and sessions.
- **werkzeug** — a toolkit that Flask depends on internally; you also use it directly
  for password hashing.

To install, run `pip install -r BACKEND/requirements.txt` while your virtual environment
is active. pip downloads both packages and their own sub-dependencies automatically.

---

### 1.4 Confirm Flask is Working

After installation, confirm Flask is accessible by asking Python to import it and print
its version. If you see a version number without errors, your environment is ready.

---

## 2. Backend Implementation

The backend is a Flask application split across multiple Python files. Each file owns
one concern, which keeps the codebase easy to navigate and extend.

### 2.1 Project Folder Skeleton

Create the following directory and file layout before writing any logic:

```
banking-workshop/
├── BACKEND/
│   ├── app.py
│   ├── auth.py
│   ├── accounts.py
│   ├── transactions.py
│   ├── database.py
│   └── requirements.txt
├── FRONTEND/
│   ├── templates/
│   │   ├── base.html
│   │   ├── login.html
│   │   ├── dashboard.html
│   │   ├── deposit.html
│   │   └── withdraw.html
│   └── static/
│       └── style.css
└── tests/
    └── test_app.py
```

Having empty files in place before you fill them lets you wire up imports and registrations
early, catching structural errors before logic gets complex.

---

### 2.2 Create the Flask App (`app.py`)

`app.py` is the entry point — the file you run to start the web server. Its job is:

1. **Instantiate Flask** — create the `app` object, which is the core of everything. When
   creating it, tell Flask where to find templates (point to `FRONTEND/templates/`) and
   where to find static files (point to `FRONTEND/static/`). Flask does not look in these
   locations by default since they are outside the standard folder structure.

2. **Set a secret key** — Flask's session system encrypts session data in a cookie and
   signs it using a secret key. Without a secret key, sessions will not work. For local
   development a hardcoded string is fine; for production this must be a long random value
   stored in an environment variable.

3. **Register Blueprints** — each module (`auth.py`, `accounts.py`, `transactions.py`)
   defines a Flask Blueprint (a mini-application with its own routes). In `app.py` you
   import those Blueprints and register them onto the main `app` object. This is how Flask
   knows about all the routes in the application without them all being written in one file.

4. **Add a root redirect** — the `/` route has no content of its own. Redirect it to
   `/login` so visiting the site's root URL always lands on the login page.

5. **Guard the entry point** — wrap the `app.run()` call inside an `if __name__ == '__main__'`
   block. This ensures the server only starts when you run the file directly; it does not
   accidentally start when the file is imported by tests.

---

### 2.3 Database Layer (`database.py`)

This file handles all direct communication with the SQLite database. No other file should
write SQL — they all call functions defined here.

**Database initialisation logic:**

- Define a function that creates the SQLite file (`banking.db`) if it does not exist and
  creates three tables: `customers`, `accounts`, and `transactions`.
- The `customers` table stores: a unique ID, a username, and a hashed password.
- The `accounts` table stores: an account ID, the customer ID it belongs to, and the
  current balance (stored as a number with decimal precision).
- The `transactions` table stores: a transaction ID, the account it applies to, the type
  (deposit or withdrawal as a string), the amount, and a timestamp.
- Call this initialisation function from `app.py` when the app starts, so the database is
  always ready before the first request arrives.

**Seeding logic:**

- After creating tables, check whether any customer rows already exist. If the table is
  empty, insert at least one test customer with a known username and a **hashed** password.
  Use Werkzeug's `generate_password_hash` to hash the password before inserting.
- Also create a corresponding account row for that customer with a starting balance (for
  example, £1000.00).
- The seed check prevents duplicate rows if the app is restarted.

**Data access functions to write:**

- `get_customer_by_username(username)` — returns the full customer row matching the given
  username, or nothing if not found. Used during login.
- `get_account_by_customer_id(customer_id)` — returns the account row for a given customer.
  Used on the dashboard and during transactions.
- `update_balance(account_id, new_balance)` — writes a new balance value to the account row.
- `log_transaction(account_id, type, amount)` — inserts a new row into the transactions
  table. Called after every successful deposit or withdrawal.

**Connection management:** Each call to these functions should open a SQLite connection,
perform its query, and close the connection. SQLite supports this simple per-call pattern
without connection pooling for a local single-user application.

---

### 2.4 Authentication Module (`auth.py`)

This file defines the routes and logic that let a customer log in and log out.

**Login — GET request:**
When the browser requests `/login` with GET, simply render the login HTML template. No
logic is needed; just display the form.

**Login — POST request:**
When the browser submits the login form, the following sequence must happen:
1. Read the `username` and `password` values from the submitted form data.
2. Look up the customer in the database by username using the data access function.
3. If no customer is found with that username, immediately re-render the login page with
   an error message. Do not reveal whether the username or the password was wrong — say
   "Invalid credentials" generically to prevent username enumeration.
4. If a customer is found, use Werkzeug's `check_password_hash` to compare the submitted
   password against the stored hash. If they do not match, re-render the login page with
   the same generic error message.
5. If the password matches, store the customer's unique ID in the Flask session dictionary
   using a key like `user_id`. The session is a secure cookie that Flask manages; writing
   to it establishes the authenticated state.
6. Redirect to `/dashboard`.

**Logout — POST request:**
Logout should use POST (not GET) to prevent logout from being triggered by a browser
prefetching a link. When called:
1. Clear the session entirely (Flask provides a `session.clear()` method).
2. Redirect to `/login`.

**Login-required guard:**
Write a helper function (or Python decorator) called something like `login_required`. It
checks whether `user_id` exists in the current session. If the key is absent, the user is
not logged in — redirect them to `/login` immediately. If the key is present, allow the
request to continue. Apply this guard to every route except `/login` and `/logout`.

---

### 2.5 Accounts Module (`accounts.py`)

This file handles the dashboard — the home page a customer sees after logging in.

**Dashboard — GET request:**
1. Apply the login-required guard. Unauthenticated requests never reach the logic below.
2. Read the `user_id` from the session.
3. Call `get_account_by_customer_id` to retrieve the account row (which contains the balance).
4. Also retrieve the customer's name to display a personalised welcome message.
5. Pass the name and balance to the dashboard template and render it.

The dashboard route does not accept POST requests — it is purely a display page.

---

### 2.6 Transactions Module (`transactions.py`)

This file handles deposit and withdrawal operations. Both follow the same structural
pattern (GET shows the form, POST processes it), so the logic is mirrored.

**Deposit — GET request:**
Render the deposit form template. No data needed from the database at this stage.

**Deposit — POST request:**
1. Apply the login-required guard.
2. Read the submitted `amount` value from the form.
3. Attempt to convert it to a floating-point number. If conversion fails (the user typed
   text, symbols, etc.), re-render the form with an error message.
4. Check that the amount is greater than zero. If it is zero or negative, re-render with
   an error.
5. Retrieve the current account from the database using the session `user_id`.
6. Calculate the new balance: current balance plus the deposit amount.
7. Call `update_balance` to write the new balance to the database.
8. Call `log_transaction` to record the deposit in the transactions table.
9. Use Flask's `flash()` to queue a success message (e.g. "Deposit of £X was successful").
10. Redirect to `/dashboard`. This follows the POST-Redirect-GET pattern, which prevents
    the form from being re-submitted if the user refreshes the page.

**Withdraw — GET request:**
Render the withdrawal form template.

**Withdraw — POST request:**
1–4. Same validation steps as deposit (numeric check, positive check).
5. Retrieve the current account and its balance.
6. Check whether the withdrawal amount exceeds the current balance. If it does, re-render
   the form with an error such as "Insufficient funds." Do not modify the database.
7. Calculate the new balance: current balance minus the withdrawal amount.
8. Call `update_balance` and `log_transaction`.
9. Flash a success message and redirect to `/dashboard`.

---

### 2.7 Session Management

Flask's session is a signed, encrypted cookie stored on the browser. Here is how it
behaves in this application:

- **Setting the session:** Writing `session['user_id'] = customer_id` after successful
  login stores the customer's ID. Flask serialises this to a cookie automatically.
- **Reading the session:** On any subsequent request, reading `session.get('user_id')`
  gives back the stored value. If the session is empty or the cookie is missing or tampered
  with, this returns `None`.
- **Clearing the session:** `session.clear()` on logout removes all keys, effectively
  logging the user out. The cookie becomes empty and future reads return `None`.
- **Secret key dependency:** The session only works correctly when `app.secret_key` is set.
  Without it, Flask raises an error or the session cannot be signed securely.

---

### 2.8 Error Handling

For this application, two categories of errors need handling:

**Input errors (user mistakes):** These are expected and should produce helpful feedback.
Rather than raising an exception, re-render the relevant form and pass an error message
string to the template. Display it prominently above the form.

**Unauthenticated access:** Handled by the login-required guard in every protected route.
Redirect silently to `/login`.

**Unexpected database errors:** For a local SQLite demo application, full error handling is
not required. However, wrapping database writes in try/except blocks allows you to catch
SQLite exceptions and flash a generic "An error occurred" message rather than crashing.

---

## 3. Frontend Implementation

All frontend pages are Jinja2 HTML templates — HTML files with special `{{ }}` and
`{% %}` syntax that Flask fills in with data before sending to the browser.

### 3.1 Shared Base Layout (`base.html`)

Create one base template that all other pages inherit from. This avoids repeating the
Bootstrap `<head>` block and navigation bar in every file. The base template defines:

1. **HTML skeleton** — the `<html>`, `<head>`, and `<body>` tags with the Bootstrap 5 CSS
   CDN link inside `<head>`.

2. **Navbar** — a Bootstrap navigation bar at the top showing the app name. If the user is
   logged in (check for `session.user_id` in the template), also show a Logout button that
   submits a small form via POST to `/logout`.

3. **Flash message block** — Flask's `flash()` function queues messages that should be
   shown once. In the base template, loop over `get_flashed_messages(with_categories=true)`
   and render each message as a Bootstrap alert (`alert-success` for success messages,
   `alert-danger` for errors). Because this block lives in `base.html`, all child pages
   automatically display flash messages without any extra code.

4. **Content block** — a Jinja2 `{% block content %}{% endblock %}` placeholder. Each
   child template fills this block with its unique page content.

---

### 3.2 Login Page (`login.html`)

This page extends `base.html` and fills the content block with:

- A centered card using Bootstrap's grid system (`container`, `row`, `col`) and a
  `card` component.
- Inside the card: a heading ("Sign In"), and a form with two input fields (`username`
  and `password`) and a Submit button.
- The form's `method` attribute must be `POST` and its `action` must point to `/login`.
- The `password` field's `type` must be `password` so the browser masks the input.
- If the backend passes an error message to the template context, display it as a
  Bootstrap `alert-danger` above the form.

---

### 3.3 Dashboard Page (`dashboard.html`)

This page extends `base.html` and shows the authenticated customer's home screen:

- A personalised welcome heading using the customer name passed from the backend
  (e.g. "Welcome, Alice").
- The current account balance displayed prominently, formatted as a currency value.
- Two Bootstrap buttons or styled links: one pointing to `/deposit` and one to `/withdraw`.

Keep this page simple. Its only purpose is to confirm the balance and provide navigation.

---

### 3.4 Deposit Form (`deposit.html`)

This page extends `base.html` and provides the deposit interface:

- A heading ("Deposit Funds").
- A single numeric input field for the deposit amount with a label ("Amount £").
- The `type` should be `number` and the `min` attribute should be `0.01` to enforce
  positive values at the browser level (the server still validates independently).
- A `step` of `0.01` allows decimal penny-level input.
- A Submit button ("Deposit").
- The form posts to `/deposit`.
- A link back to the dashboard for customers who change their mind.

---

### 3.5 Withdraw Form (`withdraw.html`)

Structurally identical to the deposit form, with:

- Heading changed to "Withdraw Funds".
- Form action pointing to `/withdraw`.
- Submit button labelled "Withdraw".

---

### 3.6 Bootstrap Layout Principles

Apply the following Bootstrap conventions consistently across all pages:

- Wrap page content in a `<div class="container mt-4">` to give consistent horizontal
  padding and top margin.
- Use `row` and `col-md-6 offset-md-3` (or similar) to horizontally centre narrow forms
  on wider screens.
- Use Bootstrap's `btn btn-primary` for primary actions (login, deposit, withdraw) and
  `btn btn-outline-secondary` for secondary actions (back links).
- Use `form-control` on every `<input>` and `form-label` on every `<label>` for consistent
  Bootstrap styling.

---

## 4. Integration Steps

### 4.1 Connect Flask to the Correct Template and Static Folders

Flask assumes templates live in a folder called `templates/` next to `app.py` and static
files in `static/`. Since this project places them under `FRONTEND/`, you must override
these defaults when creating the Flask app object. Pass the explicit paths as arguments
to the `Flask()` constructor — `template_folder` and `static_folder`. Flask will then
look in the right places automatically.

---

### 4.2 Connect Frontend Pages to Backend Routes

Every HTML form's `action` attribute must exactly match the URL path defined in the
corresponding Flask route. If a route is registered with a Blueprint that has a URL
prefix, that prefix must be included in the form action. For this application, routes
have no prefix, so form actions like `/login`, `/deposit`, and `/withdraw` map directly.

For links (anchor tags `<a href="...">`), use Flask's `url_for()` function inside Jinja2
templates rather than hardcoding paths. For example, `{{ url_for('auth.logout') }}` is
safer than `/logout` because it automatically updates if a route path changes.

---

### 4.3 Blueprint Registration

Each module (`auth.py`, `accounts.py`, `transactions.py`) should define a Flask Blueprint
object at the top. A Blueprint is simply a collection of routes that can be attached to
the main Flask app.

In `app.py`, import each Blueprint and call `app.register_blueprint()` to attach it. Until
this registration happens, the routes defined in those files are invisible to Flask.

---

### 4.4 Connect Flask to SQLite

Flask itself does not manage the SQLite file — that is handled entirely in `database.py`.
The connection between Flask and SQLite happens when route handlers call the data access
functions defined in `database.py`. There is no ORM or connection pool — just standard
Python `sqlite3` library calls.

Call the database initialisation function from `app.py` before the first request is
served. Flask provides an `app.app_context()` mechanism to safely run startup logic;
use it to call your `init_db()` function so the tables and seed data exist before any
user hits the app.

---

## 5. Validation Rules

Validation must happen on two levels: client-side (browser) for immediate feedback, and
server-side (Flask) for security. Never rely on client-side validation alone, because
any user can bypass it using browser developer tools or direct API calls.

### 5.1 Login Validation

| Rule | How to enforce it |
|---|---|
| Username field must not be empty | Check that the stripped username string is not blank after receiving the POST |
| Password field must not be empty | Check that the password string is not blank |
| Username must exist in the database | Query the customers table; if no row returned, reject |
| Password must match the stored hash | Use `check_password_hash`; if it returns False, reject |
| Rejection message must be generic | Say "Invalid credentials" — never say "Username not found" or "Wrong password" separately |

---

### 5.2 Balance Validation (Read)

The balance displayed on the dashboard is read directly from the database. No user input
is involved, so no validation is needed. However, ensure the balance is formatted to two
decimal places before passing to the template to avoid displaying raw floating-point
numbers like `1000.0000000003`.

---

### 5.3 Deposit Validation

| Rule | How to enforce it |
|---|---|
| Amount field must not be empty | Check that the field is present and not blank |
| Amount must be a valid number | Wrap the conversion to float in a try/except; catch ValueError |
| Amount must be greater than zero | Compare the parsed value; reject if `<= 0` |
| Enforce on the HTML input too | Use `type="number"`, `min="0.01"`, `step="0.01"` on the input element |

---

### 5.4 Withdrawal Validation

| Rule | How to enforce it |
|---|---|
| All deposit rules apply | Apply the same numeric checks first |
| Amount must not exceed current balance | After passing numeric checks, compare amount to the account's current balance |
| If amount > balance, reject without DB write | Return an error and re-render the form; do not call update_balance |

---

### 5.5 Session / Access Validation

| Rule | How to enforce it |
|---|---|
| Must be logged in to see dashboard | Apply login_required guard to `/dashboard` route |
| Must be logged in to deposit | Apply login_required guard to `/deposit` route |
| Must be logged in to withdraw | Apply login_required guard to `/withdraw` route |
| Accessing `/login` while already logged in | Optionally redirect to `/dashboard` to avoid confusion |

---

## 6. Testing

Testing verifies that the application behaves correctly for both happy-path and error
scenarios. Tests are written using **pytest** and run from the `tests/` folder.

### 6.1 Test Setup

Before writing test cases, create a **pytest fixture** that provides a configured test
client. A test client simulates a browser — it can send GET and POST requests to routes
and inspect responses, without actually starting a web server.

The fixture should:
1. Import the `app` object from `BACKEND/app.py`.
2. Override Flask's `TESTING` config flag to `True`. This disables certain behaviours
   (like error propagation) that would interfere with test assertions.
3. Use an in-memory SQLite database (`:memory:`) or a separate test database file so
   tests do not corrupt the development database.
4. Seed the test database with known customer credentials so tests can log in reliably.
5. Yield the test client, then tear down the database after each test.

---

### 6.2 Unit Tests

Unit tests check individual pieces of logic in isolation.

**Authentication tests:**

- **Login success:** POST to `/login` with the correct username and password. Assert the
  response redirects to `/dashboard` and that the session contains a `user_id`.
- **Login failure — wrong password:** POST to `/login` with the correct username but wrong
  password. Assert the response is 200 (re-renders the form, not a redirect) and that the
  response body contains an error message.
- **Login failure — unknown username:** POST to `/login` with a username that does not
  exist. Same assertions as wrong password.

**Transaction tests:**

- **Deposit valid amount:** POST to `/deposit` with a positive number while logged in.
  Assert the response redirects to `/dashboard`. Query the test database directly and
  confirm the balance increased by the deposited amount.
- **Deposit invalid amount — negative:** POST to `/deposit` with a negative value. Assert
  the form is re-rendered with an error and the balance is unchanged.
- **Deposit invalid amount — non-numeric:** POST to `/deposit` with text. Same assertions.
- **Withdrawal valid amount:** POST to `/withdraw` with an amount less than the balance.
  Assert redirect to dashboard and that the balance decreased correctly.
- **Withdrawal — insufficient funds:** POST to `/withdraw` with an amount greater than the
  balance. Assert the form is re-rendered with an error and the balance is unchanged.

---

### 6.3 Integration Tests

Integration tests verify that multiple components work correctly together end-to-end.

- **Full login + dashboard flow:** Log in successfully, then GET `/dashboard`. Assert the
  response contains the customer name and a formatted balance.
- **Full deposit flow:** Log in, POST to `/deposit`, follow the redirect to `/dashboard`,
  assert the new balance is shown.
- **Session isolation:** Log in as one user, confirm their balance. Log out. Confirm
  `/dashboard` now redirects to `/login`.
- **Unauthenticated redirect:** Without logging in, GET `/dashboard`. Assert the response
  redirects to `/login` (status code 302) rather than rendering any content.

---

### 6.4 Manual Testing Checklist

Run through this checklist in the browser after each significant change to verify
end-to-end behaviour:

**Login:**
- [ ] Visiting `/` redirects to the login page.
- [ ] Submitting the form with blank fields shows an error.
- [ ] Submitting with wrong credentials shows a generic error.
- [ ] Submitting with correct credentials lands on the dashboard.

**Dashboard:**
- [ ] The customer's name appears in the welcome message.
- [ ] The balance shown matches what was seeded in the database.
- [ ] Deposit and Withdraw buttons are visible and clickable.
- [ ] The Logout button is visible in the navbar.

**Deposit:**
- [ ] Entering a valid positive amount and submitting shows a success message on the dashboard.
- [ ] The balance on the dashboard increases by the deposited amount.
- [ ] Entering zero shows a validation error.
- [ ] Entering a negative number shows a validation error.
- [ ] Entering letters shows a validation error.

**Withdraw:**
- [ ] Entering an amount less than the balance succeeds and the new balance is reflected.
- [ ] Entering an amount equal to the balance succeeds (zero balance result is valid).
- [ ] Entering an amount greater than the balance shows an "Insufficient funds" error.
- [ ] The balance remains unchanged after a failed withdrawal.

**Logout:**
- [ ] Clicking Logout redirects to the login page.
- [ ] After logout, pressing the browser back button to `/dashboard` redirects to `/login`.

---

## 7. Deployment

### 7.1 Run Locally

To run the application on your own machine for development or demonstration:

1. Ensure your virtual environment is activated (see Section 1.2).
2. Navigate to the `BACKEND/` folder in your terminal.
3. Run `python app.py`. Flask will start a development web server, typically on
   `http://127.0.0.1:5000`.
4. Open that URL in your browser.
5. The database file (`banking.db`) will be created automatically in the `BACKEND/` folder
   if it does not already exist. The seed data (test customer) will also be inserted on
   first run.

To stop the server, press `Ctrl+C` in the terminal.

---

### 7.2 Environment Variables for Configuration

Even for local development, avoid hardcoding the Flask secret key directly in `app.py`.
A better pattern is to read it from an environment variable and fall back to a default
only in development mode:

- If the environment variable `SECRET_KEY` is set, use its value.
- If not, use a hardcoded development default (e.g. `"dev-secret-key"`).

This makes it trivial to configure a strong secret key in production without changing code.

---

### 7.3 Production Considerations

Flask's built-in development server (`app.run()`) is **not suitable for production**. It
is single-threaded, not secure, and not designed for real traffic. If you ever deploy this
beyond local use, consider the following:

**Use a production WSGI server:**
Replace `app.run()` with a proper WSGI server such as **Gunicorn** (Linux/macOS) or
**Waitress** (Windows-compatible). These servers handle multiple concurrent requests,
timeouts, and process management that Flask's dev server cannot.

**Upgrade the database:**
SQLite is sufficient for a single-user local demo. For multi-user or production use,
migrate to **PostgreSQL** or **MySQL**. The data access functions in `database.py` would
need to use a compatible library (e.g. `psycopg2` for PostgreSQL), but the logic would
remain the same.

**Set a strong secret key:**
The `SECRET_KEY` environment variable should be a long, randomly generated string in
production. Never commit it to source control.

**Use HTTPS:**
In any real-world deployment, serve the application over HTTPS to protect session cookies
and form data in transit. This is typically handled by a reverse proxy (e.g. Nginx or
a cloud load balancer) in front of the WSGI server.

**Disable debug mode:**
Ensure `app.run(debug=False)` or that the `FLASK_DEBUG` environment variable is `0` in
production. Debug mode exposes an interactive debugger in the browser that can execute
arbitrary Python code — a serious security risk.

---

## Summary: Implementation Order

Follow this sequence to avoid dependency issues:

```
Step 1  Set up virtual environment and install Flask + Werkzeug
Step 2  Create folder structure and empty files
Step 3  Write database.py — init, seed, and all data access functions
Step 4  Write app.py — Flask instance, secret key, blueprint registration, DB init call
Step 5  Write auth.py — login route (GET + POST), logout route, login_required guard
Step 6  Write accounts.py — dashboard route
Step 7  Write transactions.py — deposit and withdraw routes
Step 8  Write base.html — shared Bootstrap layout with navbar and flash block
Step 9  Write login.html, dashboard.html, deposit.html, withdraw.html
Step 10 Wire form actions and url_for links to match route definitions
Step 11 Manual test the full user journey in the browser
Step 12 Write pytest tests in tests/test_app.py
Step 13 Run pytest and confirm all tests pass
Step 14 Verify the CI pipeline configuration matches the project structure
```

Each step builds on the previous one. Completing the database layer first means every
route handler has something to call immediately, making it easier to test incrementally.
