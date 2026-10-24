# Architecture: Expense Tracker

## 1. Architecture Overview
The application will use a three-layer architecture:

- **Frontend:** Streamlit for the user interface.
- **Backend:** FastAPI for API endpoints, validation and business logic.
- **Database:** PostgreSQL for persistent data storage.

## 2. Component Communication
Streamlit sends HTTP requests to FastAPI. FastAPI processes requests and communicates with PostgreSQL. Streamlit does not connect directly to the database.

## 3. Code Organization
The frontend and backend will be maintained in separate folders within one repository.

The backend will separate:
- API routes
- Business logic
- Database operations
- Configuration

## 4. Security
- Protect authenticated API endpoints.
- Validate input on the backend.
- Store secrets securely and restrict database access.
