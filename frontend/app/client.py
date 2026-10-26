import os
from datetime import date
from decimal import Decimal
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


class ApiError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def get_base_url() -> str:
    return os.environ.get("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")


def _detail(response: httpx.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        return "Request failed."
    detail = body.get("detail", "Request failed.")
    if isinstance(detail, list):
        messages = []
        for item in detail:
            if isinstance(item, dict):
                location = item.get("loc") or []
                field = location[-1] if location else "input"
                messages.append(f"{field}: {item.get('msg', 'Invalid value')}")
            else:
                messages.append(str(item))
        return " ".join(messages) or "Invalid input."
    return str(detail)


class ApiClient:
    def __init__(self, base_url: str, token: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token

    def _headers(self) -> dict[str, str]:
        if not self.token:
            return {}
        return {"Authorization": f"Bearer {self.token}"}

    def _request(self, method: str, path: str, **kwargs: object) -> httpx.Response:
        try:
            response = httpx.request(
                method,
                f"{self.base_url}{path}",
                headers=self._headers(),
                timeout=10.0,
                **kwargs,
            )
        except httpx.RequestError as exc:
            raise ApiError(0, "The backend is unavailable.") from exc
        if response.status_code >= 400:
            raise ApiError(response.status_code, _detail(response))
        return response

    def login(self, username: str, password: str) -> str:
        response = self._request(
            "POST",
            "/auth/login",
            json={"username": username, "password": password},
        )
        return str(response.json()["access_token"])

    def list_categories(self) -> list[dict]:
        return list(self._request("GET", "/categories").json())

    def create_category(self, name: str) -> dict:
        return dict(self._request("POST", "/categories", json={"name": name}).json())

    def list_expenses(
        self,
        *,
        category_id: int | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[dict]:
        params = _date_params(from_date, to_date)
        if category_id is not None:
            params["category_id"] = category_id
        return list(self._request("GET", "/expenses", params=params).json())

    def create_expense(
        self,
        *,
        amount: Decimal,
        expense_date: date,
        category_id: int,
        description: str | None,
    ) -> dict:
        return dict(
            self._request(
                "POST",
                "/expenses",
                json=_expense_body(amount, expense_date, category_id, description),
            ).json()
        )

    def update_expense(
        self,
        expense_id: int,
        *,
        amount: Decimal,
        expense_date: date,
        category_id: int,
        description: str | None,
    ) -> dict:
        return dict(
            self._request(
                "PUT",
                f"/expenses/{expense_id}",
                json=_expense_body(amount, expense_date, category_id, description),
            ).json()
        )

    def delete_expense(self, expense_id: int) -> None:
        self._request("DELETE", f"/expenses/{expense_id}")

    def summarize(
        self, *, from_date: date | None = None, to_date: date | None = None
    ) -> dict:
        return dict(
            self._request(
                "GET", "/expenses/summary", params=_date_params(from_date, to_date)
            ).json()
        )


def _date_params(from_date: date | None, to_date: date | None) -> dict[str, str]:
    params: dict[str, str] = {}
    if from_date is not None:
        params["from_date"] = from_date.isoformat()
    if to_date is not None:
        params["to_date"] = to_date.isoformat()
    return params


def _expense_body(
    amount: Decimal, expense_date: date, category_id: int, description: str | None
) -> dict[str, object]:
    cleaned = description.strip() if description else ""
    return {
        "amount": f"{amount.quantize(Decimal('0.01')):.2f}",
        "expense_date": expense_date.isoformat(),
        "category_id": category_id,
        "description": cleaned or None,
    }
