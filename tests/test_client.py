from __future__ import annotations

import logging
from typing import Any

import pytest
import requests

from ingest.client import PancakeAPIError, PancakeClient, ReadOnlyViolationError, redact_url
from ingest.settings import Settings

SECRET = "top-secret-api-key"


class FakeResponse:
    def __init__(self, status_code: int = 200, payload: Any = None) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(self) -> Any:
        return self._payload


class FakeSession:
    def __init__(self, response: FakeResponse | None = None, error: Exception | None = None):
        self.headers: dict[str, str] = {}
        self.response = response
        self.error = error
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def get(self, url: str, **kwargs: Any) -> FakeResponse:
        self.calls.append((url, kwargs))
        if self.error:
            raise self.error
        assert self.response is not None
        return self.response


def settings() -> Settings:
    return Settings(api_key=SECRET, shop_id="12345")


def test_redact_url_masks_keys_and_tokens() -> None:
    safe = redact_url(
        "https://pos.pages.fm/api/v1/shops?api_key=abc&token=xyz&page=2"
    )
    assert "abc" not in safe
    assert "xyz" not in safe
    assert "page=2" in safe
    assert "[REDACTED]" in safe


def test_list_shops_uses_get_and_returns_payload() -> None:
    session = FakeSession(response=FakeResponse(payload={"success": True, "shops": [{"id": 12345}]}))
    client = PancakeClient(settings(), session=session)  # type: ignore[arg-type]

    result = client.list_shops()

    assert result == [{"id": 12345}]
    url, kwargs = session.calls[0]
    assert url.endswith("/shops")
    assert kwargs["params"]["api_key"] == SECRET
    assert kwargs["allow_redirects"] is False
    assert kwargs["timeout"] == (5.0, 30.0)


def test_orders_only_uses_documented_status_filter() -> None:
    session = FakeSession(response=FakeResponse(payload={"success": True, "orders": []}))
    client = PancakeClient(settings(), session=session)  # type: ignore[arg-type]

    client.list_orders("12345", filter_status=[3, 16])

    params = session.calls[0][1]["params"]
    assert params["filter_status[]"] == [3, 16]
    assert params["api_key"] == SECRET


def test_request_exception_does_not_leak_secret(caplog: pytest.LogCaptureFixture) -> None:
    session = FakeSession(error=requests.ConnectionError(f"failed at ?api_key={SECRET}"))
    client = PancakeClient(settings(), session=session, max_attempts=1)  # type: ignore[arg-type]

    with caplog.at_level(logging.ERROR):
        with pytest.raises(PancakeAPIError) as error:
            client.list_shops()

    assert SECRET not in str(error.value)
    assert SECRET not in caplog.text


def test_redirect_is_rejected_without_following() -> None:
    session = FakeSession(response=FakeResponse(status_code=302, payload={}))
    client = PancakeClient(settings(), session=session, max_attempts=1)  # type: ignore[arg-type]

    with pytest.raises(PancakeAPIError, match="HTTP 302"):
        client.list_shops()

    assert session.calls[0][1]["allow_redirects"] is False


def test_invalid_shop_id_is_rejected_before_request() -> None:
    session = FakeSession(response=FakeResponse(payload={"success": True, "orders": []}))
    client = PancakeClient(settings(), session=session)  # type: ignore[arg-type]

    with pytest.raises(ValueError):
        client.list_orders("12345/../../other")

    assert session.calls == []


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE", "TRACE", "CONNECT"])
def test_non_get_method_is_rejected_before_request(method: str) -> None:
    session = FakeSession(response=FakeResponse(payload={"success": True}))
    client = PancakeClient(settings(), session=session)  # type: ignore[arg-type]

    with pytest.raises(ReadOnlyViolationError):
        client.request(method, "/shops")

    assert session.calls == []


@pytest.mark.parametrize(
    "path",
    [
        "/shops/99999/orders",
        "/shops/12345/products",
        "/shops/12345/orders?limit=1",
        "https://pos.pages.fm/api/v1/shops",
        "/shops/12345/orders/../products",
    ],
)
def test_non_allowlisted_endpoint_is_rejected_before_request(path: str) -> None:
    session = FakeSession(response=FakeResponse(payload={"success": True}))
    client = PancakeClient(settings(), session=session)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="allowlist"):
        client.request("GET", path)

    assert session.calls == []


def test_list_orders_rejects_a_different_shop_before_request() -> None:
    session = FakeSession(response=FakeResponse(payload={"success": True, "data": []}))
    client = PancakeClient(settings(), session=session)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="configured shop"):
        client.list_orders("99999")

    assert session.calls == []
