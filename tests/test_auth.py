import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from tests.conftest import TEST_PASSWORD, TEST_USERNAME, authorize


def test_login_success(client: TestClient) -> None:
    response = client.post(
        "/auth/login",
        json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_wrong_password_and_username_use_the_same_error(client: TestClient) -> None:
    wrong_password = client.post(
        "/auth/login",
        json={"username": TEST_USERNAME, "password": "incorrect-password"},
    )
    wrong_username = client.post(
        "/auth/login",
        json={"username": "someone-else", "password": TEST_PASSWORD},
    )
    assert wrong_password.status_code == 401
    assert wrong_username.status_code == 401
    assert wrong_password.json()["detail"] == "Invalid username or password"
    assert wrong_username.json()["detail"] == wrong_password.json()["detail"]


def test_login_missing_password_is_rejected(client: TestClient) -> None:
    response = client.post("/auth/login", json={"username": TEST_USERNAME})
    assert response.status_code == 422


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/categories"),
        ("post", "/categories"),
        ("get", "/expenses"),
        ("get", "/expenses/summary"),
        ("post", "/expenses"),
        ("delete", "/expenses/1"),
    ],
)
def test_protected_routes_require_a_token(
    client: TestClient, method: str, path: str
) -> None:
    response = getattr(client, method)(path)
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_invalid_token_is_rejected(client: TestClient) -> None:
    response = client.get("/categories", headers=authorize("not-a-token"))
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"


def test_expired_token_is_rejected(client: TestClient) -> None:
    expired = create_access_token(TEST_USERNAME, expires_minutes=-1)
    response = client.get("/categories", headers=authorize(expired))
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"


def test_valid_token_can_list_categories(client: TestClient, token: str) -> None:
    response = client.get("/categories", headers=authorize(token))
    assert response.status_code == 200
    assert response.json()
