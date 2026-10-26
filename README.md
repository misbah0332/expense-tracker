# Expense Tracker

A single-user app for recording expenses, organizing them into categories, and reviewing totals. Streamlit provides the interface, FastAPI provides the API, and PostgreSQL stores the data. The interface talks to the API over HTTP and does not connect to the database.

```
backend/app/     API routes, business rules, database access, and configuration
frontend/app/    Streamlit pages and the HTTP client
backend/alembic Alembic migrations
tests/           Automated API and client tests
```

## Prerequisites

- Python 3.14
- PostgreSQL 18. Its `psql` program is not on the system path; the database section uses the installed program directly.
- A PostgreSQL superuser for the one-time database setup

## Setup

From the project root:

```powershell
py -3.14 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

`requirements-dev.txt` installs the application dependencies and pytest.

## Environment configuration

Edit the gitignored `.env` in the project root. Both apps load it from there.

`DATABASE_URL` uses the application role and the password chosen during database setup:

```
postgresql+psycopg://expense_tracker_app:PASSWORD@127.0.0.1:5432/expense_tracker
```

URL-encode any reserved characters in the password.

Create the login password hash and a JWT signing secret locally:

```powershell
python -c "import getpass; from pwdlib import PasswordHash; print(PasswordHash.recommended().hash(getpass.getpass('Password: ')))"
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Put the results in `.env`:

| Variable | Purpose |
| --- | --- |
| `APP_USERNAME` | The single login name |
| `APP_PASSWORD_HASH` | Argon2 hash from the command above. It must start with `$argon2` |
| `JWT_SECRET` | Signing secret, at least 32 characters |
| `JWT_EXPIRE_MINUTES` | Token lifetime. The example uses 60 |
| `API_BASE_URL` | Streamlit’s API address. Defaults to `http://127.0.0.1:8000` |

Restart the backend after changing these values.

## Database

Create the database and the least-privilege role once, as the PostgreSQL superuser. `psql` prompts for the superuser password and then for the new role password. The script makes no changes if the role or database already exists.

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -h 127.0.0.1 -f backend/app/db/create_database.sql
```

Apply the schema from the `backend` directory. Alembic reads `DATABASE_URL` from `.env`. The URL in `backend/alembic.ini` is only a placeholder.

```powershell
cd backend
python -m alembic upgrade head
```

The migration creates the category and expense tables and seeds Food, Transport, Housing, Utilities, Healthcare, Entertainment, and Other.

## Running both apps

Use two terminals from the project root, with the virtual environment active.

```powershell
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
python -m streamlit run frontend/app/app.py --server.address 127.0.0.1 --server.port 8501
```

Open `http://127.0.0.1:8501`. The API is at `http://127.0.0.1:8000`.

## Authentication

The app has one user, taken from `APP_USERNAME` and `APP_PASSWORD_HASH`. There is no user table. `POST /auth/login` checks the password against the Argon2 hash and returns a bearer token. Category and expense routes require `Authorization: Bearer <token>`. Streamlit keeps that token in the browser session and returns to the login form when it expires.

## Automated tests

From the project root, after the migration has been applied:

```powershell
python -m pytest
```

The suite needs `DATABASE_URL`. It signs in as an in-memory test user and rolls back every database change when each test finishes.
