from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from app.core.config import AuthSettings
from app.db.session import engine, get_db
from app.main import app

TEST_USERNAME = "test-user"
TEST_PASSWORD = "test-password"
TEST_JWT_SECRET = "test-jwt-secret-that-is-at-least-32-characters"
PREDEFINED_CATEGORIES = (
    "Entertainment",
    "Food",
    "Healthcare",
    "Housing",
    "Other",
    "Transport",
    "Utilities",
)


@pytest.fixture(scope="session")
def auth_settings() -> AuthSettings:
    return AuthSettings(
        username=TEST_USERNAME,
        password_hash=PasswordHash.recommended().hash(TEST_PASSWORD),
        jwt_secret=TEST_JWT_SECRET,
        jwt_expire_minutes=60,
    )


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(
        bind=connection,
        autoflush=False,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(
    db_session: Session, auth_settings: AuthSettings, monkeypatch: pytest.MonkeyPatch
) -> Generator[TestClient, None, None]:
    monkeypatch.setattr("app.services.auth.get_auth_settings", lambda: auth_settings)
    monkeypatch.setattr("app.core.security.get_auth_settings", lambda: auth_settings)

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def token(client: TestClient) -> str:
    response = client.post(
        "/auth/login",
        json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def authorize(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
