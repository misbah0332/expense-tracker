import importlib.util
import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import httpx
import pytest

_ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "expense_frontend_client", _ROOT / "frontend" / "app" / "client.py"
)
assert _SPEC is not None and _SPEC.loader is not None
_CLIENT = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_CLIENT)
ApiClient = _CLIENT.ApiClient
ApiError = _CLIENT.ApiError


class _Transport:
    def __init__(self, response: httpx.Response | None = None, error: Exception | None = None):
        self.response = response
        self.error = error
        self.calls: list[tuple[str, str, dict]] = []

    def __call__(self, method: str, url: str, **kwargs: object) -> httpx.Response:
        self.calls.append((method, url, kwargs))
        if self.error is not None:
            raise self.error
        assert self.response is not None
        return self.response


def _client(monkeypatch: pytest.MonkeyPatch, transport: _Transport, token: str | None = None) -> object:
    monkeypatch.setattr(_CLIENT.httpx, "request", transport)
    return ApiClient("http://api.test", token)


def test_login_returns_the_access_token(monkeypatch: pytest.MonkeyPatch) -> None:
    transport = _Transport(httpx.Response(200, json={"access_token": "abc", "token_type": "bearer"}))
    client = _client(monkeypatch, transport)
    assert client.login("owner", "secret") == "abc"
    method, url, kwargs = transport.calls[0]
    assert method == "POST"
    assert url == "http://api.test/auth/login"
    assert kwargs["json"] == {"username": "owner", "password": "secret"}


def test_list_expenses_sends_bearer_token_and_filters(monkeypatch: pytest.MonkeyPatch) -> None:
    transport = _Transport(httpx.Response(200, json=[]))
    client = _client(monkeypatch, transport, token="token-value")
    assert client.list_expenses(category_id=3, from_date=date(2026, 1, 1), to_date=date(2026, 1, 31)) == []
    method, url, kwargs = transport.calls[0]
    assert method == "GET"
    assert url == "http://api.test/expenses"
    assert kwargs["headers"]["Authorization"] == "Bearer token-value"
    assert kwargs["params"] == {
        "from_date": "2026-01-01",
        "to_date": "2026-01-31",
        "category_id": 3,
    }


def test_create_and_update_send_decimal_strings_and_iso_dates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created = {"id": 1, "amount": "12.50", "expense_date": "2026-01-15"}
    transport = _Transport(httpx.Response(201, json=created))
    client = _client(monkeypatch, transport, token="token-value")
    payload = {
        "amount": Decimal("12.5"),
        "expense_date": date(2026, 1, 15),
        "category_id": 4,
        "description": "  lunch  ",
    }
    assert client.create_expense(**payload)["id"] == 1
    assert client.update_expense(8, **payload)["id"] == 1
    assert transport.calls[0][0] == "POST"
    assert transport.calls[0][1] == "http://api.test/expenses"
    assert transport.calls[1][0] == "PUT"
    assert transport.calls[1][1] == "http://api.test/expenses/8"
    for _, _, kwargs in transport.calls:
        assert kwargs["json"] == {
            "amount": "12.50",
            "expense_date": "2026-01-15",
            "category_id": 4,
            "description": "lunch",
        }
        assert kwargs["headers"]["Authorization"] == "Bearer token-value"


def test_error_responses_keep_the_backend_message(monkeypatch: pytest.MonkeyPatch) -> None:
    cases = [
        (401, {"detail": "Not authenticated"}, "Not authenticated"),
        (409, {"detail": "Category name already exists"}, "Category name already exists"),
        (
            422,
            {"detail": [{"loc": ["body", "name"], "msg": "String should have at least 1 character"}]},
            "name: String should have at least 1 character",
        ),
    ]
    for status, body, expected in cases:
        transport = _Transport(httpx.Response(status, json=body))
        client = _client(monkeypatch, transport, token="token-value")
        try:
            client.list_categories()
        except ApiError as exc:
            assert exc.status_code == status
            assert exc.detail == expected
        else:
            raise AssertionError(f"status {status} did not raise")


def test_connection_failure_reports_that_the_backend_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transport = _Transport(error=httpx.ConnectError("connection refused"))
    client = _client(monkeypatch, transport)
    try:
        client.login("owner", "secret")
    except ApiError as exc:
        assert exc.status_code == 0
        assert exc.detail == "The backend is unavailable."
    else:
        raise AssertionError("connection error did not raise")


def test_recorded_json_is_serializable(monkeypatch: pytest.MonkeyPatch) -> None:
    transport = _Transport(httpx.Response(200, json={"access_token": "abc"}))
    _client(monkeypatch, transport).login("owner", "secret")
    json.dumps(transport.calls[0][2]["json"])
