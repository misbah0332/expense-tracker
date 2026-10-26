from fastapi.testclient import TestClient

from tests.conftest import PREDEFINED_CATEGORIES, authorize


def test_lists_predefined_categories(client: TestClient, token: str) -> None:
    response = client.get("/categories", headers=authorize(token))
    assert response.status_code == 200
    predefined = {
        item["name"]: item["is_predefined"]
        for item in response.json()
        if item["is_predefined"]
    }
    assert set(predefined) == set(PREDEFINED_CATEGORIES)
    assert all(predefined.values())


def test_creates_a_custom_category(client: TestClient, token: str) -> None:
    response = client.post(
        "/categories",
        headers=authorize(token),
        json={"name": "  School  "},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "School"
    assert body["is_predefined"] is False

    listed = client.get("/categories", headers=authorize(token))
    assert any(item["id"] == body["id"] for item in listed.json())


def test_duplicate_category_name_conflicts(client: TestClient, token: str) -> None:
    headers = authorize(token)
    created = client.post("/categories", headers=headers, json={"name": "School"})
    assert created.status_code == 201
    duplicate = client.post("/categories", headers=headers, json={"name": "school"})
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "Category name already exists"


def test_blank_category_name_is_rejected(client: TestClient, token: str) -> None:
    response = client.post(
        "/categories", headers=authorize(token), json={"name": "   "}
    )
    assert response.status_code == 422


def test_long_category_name_is_rejected(client: TestClient, token: str) -> None:
    response = client.post(
        "/categories", headers=authorize(token), json={"name": "x" * 51}
    )
    assert response.status_code == 422
