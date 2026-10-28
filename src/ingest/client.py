"""GET-only Pancake POS API client with secret-safe error handling."""

from __future__ import annotations

import logging
import re
import time
from collections.abc import Mapping, Sequence
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import requests

from .settings import Settings

LOGGER = logging.getLogger(__name__)
_SENSITIVE_QUERY_KEYS = {
    "api_key",
    "access_token",
    "token",
    "secret",
    "password",
    "authorization",
    "x-api-key",
}
_TRANSIENT_STATUSES = {429, 500, 502, 503, 504}
_ALLOWED_SHOPS_PATHS = (
    re.compile(r"/shops/(?P<shop_id>\d+)/orders\Z"),
    re.compile(r"/shops/(?P<shop_id>\d+)/products/variations\Z"),
    re.compile(r"/shops/(?P<shop_id>\d+)/customers\Z"),
    re.compile(r"/shops/(?P<shop_id>\d+)/shopee/evaluate\Z"),
    re.compile(r"/shops/(?P<shop_id>\d+)/ads_manager/ad_accounts\Z"),
    re.compile(r"/shops/(?P<shop_id>\d+)/ads_manager/campaigns_v2\Z"),
)


class PancakeAPIError(RuntimeError):
    """Sanitized API error that never includes request or response contents."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class ReadOnlyViolationError(PermissionError):
    """Raised before any attempt to send a non-GET request."""


def redact_url(url: str) -> str:
    """Mask credentials in sensitive query parameters and URL userinfo."""
    parsed = urlsplit(url)
    safe_query: list[tuple[str, str]] = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        normalized = key.strip().lower()
        if normalized in _SENSITIVE_QUERY_KEYS or any(
            marker in normalized for marker in ("token", "secret", "password", "api_key")
        ):
            value = "[REDACTED]"
        safe_query.append((key, value))

    host = parsed.hostname or ""
    if parsed.port:
        host = f"{host}:{parsed.port}"
    if parsed.username or parsed.password:
        netloc = f"[REDACTED]@{host}"
    else:
        netloc = host
    encoded_query = urlencode(safe_query).replace("%5BREDACTED%5D", "[REDACTED]")
    return urlunsplit((parsed.scheme, netloc, parsed.path, encoded_query, ""))


class PancakeClient:
    """Small read-only client restricted to explicitly allowlisted endpoints."""

    def __init__(
        self,
        settings: Settings,
        *,
        timeout: tuple[float, float] = (5.0, 30.0),
        max_attempts: int = 4,
        backoff_seconds: float = 0.5,
        session: requests.Session | None = None,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1.")
        self._settings = settings
        self._timeout = timeout
        self._max_attempts = max_attempts
        self._backoff_seconds = backoff_seconds
        self._session = session or requests.Session()
        self._session.headers.update({"Accept": "application/json"})

    def list_shops(self) -> list[dict[str, Any]]:
        """Call the documented GET /shops endpoint."""
        payload = self.request("GET", "/shops")
        shops = payload.get("shops") if isinstance(payload, dict) else None
        if not isinstance(shops, list):
            raise PancakeAPIError("GET /shops returned an unexpected response shape.")
        return shops

    def list_orders(
        self,
        shop_id: str,
        *,
        filter_status: Sequence[int] | None = None,
        page_number: int | None = None,
        page_size: int | None = None,
    ) -> dict[str, Any]:
        """Call the order-list endpoint with pagination args verified on live pages."""
        if not re.fullmatch(r"\d+", str(shop_id)):
            raise ValueError("shop_id must contain digits only.")
        params: dict[str, Any] = {}
        if filter_status:
            if any(not isinstance(status, int) for status in filter_status):
                raise ValueError("filter_status values must be integers.")
            params["filter_status[]"] = list(filter_status)
        for name, value in (("page_number", page_number), ("page_size", page_size)):
            if value is not None:
                if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                    raise ValueError(f"{name} must be a positive integer.")
                params[name] = value
        if shop_id != self._settings.shop_id:
            raise ValueError("shop_id must match the configured shop.")
        return self.request("GET", f"/shops/{shop_id}/orders", params=params)

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        """Perform an allowlisted GET and return its JSON payload."""
        payload, _ = self.request_with_status(method, path, params=params)
        return payload

    def request_with_status(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
    ) -> tuple[Any, int]:
        """Perform an allowlisted GET; reject all other methods before sending."""
        if not isinstance(method, str) or method.upper() != "GET":
            raise ReadOnlyViolationError("Only GET requests are allowed.")
        if path != "/shops":
            match = None
            if isinstance(path, str):
                for candidate in _ALLOWED_SHOPS_PATHS:
                    match = candidate.fullmatch(path)
                    if match is not None:
                        break
            if match is None or match.group("shop_id") != self._settings.shop_id:
                raise ValueError("Endpoint is not in the Pancake read allowlist.")

        url = f"{self._settings.api_base_url}{path}"
        query = dict(params or {})
        query["api_key"] = self._settings.api_key
        safe_path = redact_url(url)

        for attempt in range(self._max_attempts):
            try:
                response = self._session.get(
                    url,
                    params=query,
                    timeout=self._timeout,
                    allow_redirects=False,
                )
            except requests.RequestException as exc:
                retryable = isinstance(
                    exc,
                    (requests.Timeout, requests.ConnectionError),
                )
                if retryable and attempt + 1 < self._max_attempts:
                    time.sleep(self._backoff_seconds * (2**attempt))
                    continue
                LOGGER.error("Pancake GET failed (%s).", type(exc).__name__)
                raise PancakeAPIError(
                    f"GET {safe_path} failed ({type(exc).__name__})."
                ) from None

            status = response.status_code
            if status in _TRANSIENT_STATUSES and attempt + 1 < self._max_attempts:
                time.sleep(self._backoff_seconds * (2**attempt))
                continue
            if status < 200 or status >= 300:
                LOGGER.error("Pancake GET returned HTTP %s.", status)
                raise PancakeAPIError(
                    f"GET {safe_path} returned HTTP {status}.",
                    status_code=status,
                )

            try:
                payload = response.json()
            except (ValueError, requests.exceptions.JSONDecodeError):
                raise PancakeAPIError(
                    f"GET {safe_path} returned invalid JSON.",
                    status_code=status,
                ) from None

            if isinstance(payload, dict) and payload.get("success") is False:
                raise PancakeAPIError(
                    f"GET {safe_path} returned success=false.",
                    status_code=status,
                )
            return payload, status

        raise PancakeAPIError(f"GET {safe_path} exhausted retry attempts.")
