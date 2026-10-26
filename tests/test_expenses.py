from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from tests.conftest import authorize


def _category_id(client: TestClient, token: str, name: str) -> int:
    response = client.get("/categories", headers=authorize(token))
    assert response.status_code == 200
    return next(item["id"] for item in response.json() if item["name"] == name)


def _expense(
    amount: str = "12.50",
    expense_date: str = "2026-01-15",
    category_id: int = 1,
    description: str | None = "lunch",
) -> dict:
    return {
        "amount": amount,
        "expense_date": expense_date,
        "category_id": category_id,
        "description": description,
    }


def test_expense_crud_filters_and_summary(client: TestClient, token: str) -> None:
    headers = authorize(token)
    food_id = _category_id(client, token, "Food")
    transport_id = _category_id(client, token, "Transport")

    created = client.post(
        "/expenses",
        headers=headers,
        json=_expense(category_id=food_id, description="  lunch  "),
    )
    assert created.status_code == 201
    body = created.json()
    assert body["description"] == "lunch"
    assert body["category_name"] == "Food"
    assert Decimal(body["amount"]) == Decimal("12.50")

    fetched = client.get(f"/expenses/{body['id']}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["id"] == body["id"]

    updated = client.put(
        f"/expenses/{body['id']}",
        headers=headers,
        json=_expense(
            amount="15.00",
            expense_date="2026-01-20",
            category_id=transport_id,
            description="taxi",
        ),
    )
    assert updated.status_code == 200
    assert updated.json()["category_name"] == "Transport"
    assert Decimal(updated.json()["amount"]) == Decimal("15.00")

    second = client.post(
        "/expenses",
        headers=headers,
        json=_expense(
            amount="3.25",
            expense_date="2026-02-02",
            category_id=transport_id,
            description=None,
        ),
    )
    assert second.status_code == 201

    filtered = client.get(
        "/expenses",
        headers=headers,
        params={"from_date": "2026-02-01", "category_id": transport_id},
    )
    filtered_ids = [item["id"] for item in filtered.json()]
    assert second.json()["id"] in filtered_ids
    assert body["id"] not in filtered_ids

    summary = client.get(
        "/expenses/summary",
        headers=headers,
        params={"from_date": "2026-01-01", "to_date": "2026-02-28"},
    )
    assert summary.status_code == 200
    assert Decimal(summary.json()["total"]) == Decimal("18.25")
    transport_total = next(
        item["total"]
        for item in summary.json()["categories"]
        if item["category_name"] == "Transport"
    )
    assert Decimal(transport_total) == Decimal("18.25")

    deleted = client.delete(f"/expenses/{body['id']}", headers=headers)
    assert deleted.status_code == 204
    missing = client.get(f"/expenses/{body['id']}", headers=headers)
    assert missing.status_code == 404
    assert missing.json()["detail"] == "Expense not found"


def test_missing_expense_update_and_delete(client: TestClient, token: str) -> None:
    headers = authorize(token)
    food_id = _category_id(client, token, "Food")
    update = client.put(
        "/expenses/999999",
        headers=headers,
        json=_expense(category_id=food_id),
    )
    delete = client.delete("/expenses/999999", headers=headers)
    assert update.status_code == 404
    assert delete.status_code == 404


def test_reversed_date_range_is_rejected(client: TestClient, token: str) -> None:
    response = client.get(
        "/expenses",
        headers=authorize(token),
        params={"from_date": "2026-03-01", "to_date": "2026-01-01"},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "from_date must be on or before to_date"


@pytest.mark.parametrize("amount", ["-1.00", "0.00", "1.999"])
def test_invalid_amounts_are_rejected(
    client: TestClient, token: str, amount: str
) -> None:
    food_id = _category_id(client, token, "Food")
    response = client.post(
        "/expenses",
        headers=authorize(token),
        json=_expense(amount=amount, category_id=food_id),
    )
    assert response.status_code == 422


def test_unknown_category_is_rejected(client: TestClient, token: str) -> None:
    response = client.post(
        "/expenses",
        headers=authorize(token),
        json=_expense(category_id=999999),
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "Category not found"
