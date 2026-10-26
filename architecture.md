# Architecture: Expense Tracker

## 1. Architecture Overview
The application uses a three-layer architecture:

- **Frontend:** Streamlit for the user interface.
- **Backend:** FastAPI for API endpoints, validation and business logic.
- **Database:** PostgreSQL for persistent data storage.

## 2. Component Communication
Streamlit sends HTTP requests to FastAPI. FastAPI processes requests and communicates with PostgreSQL through SQLAlchemy. Streamlit does not connect directly to the database.

## 3. Code Organization
The frontend and backend are maintained in separate folders within one repository.

`frontend/app` contains the Streamlit pages and the HTTP client.

The backend separates:

- `backend/app/api` for API routes
- `backend/app/services` for business logic
- `backend/app/db` for models, queries, and database sessions
- `backend/app/schemas` for request and response models
- `backend/app/core` for configuration and security

Alembic migrations live in `backend/alembic`.

## 4. Security
- One application user signs in with a password checked against an Argon2 hash.
- Category and expense endpoints require a bearer token.
- Input is validated on the backend.
- Secrets stay in the gitignored environment file.
- The database role is limited to the application database.
