from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import probe_endpoints
from ingest.client import PancakeAPIError
from ingest.identifiers import pseudonymize_id

SECRET = "probe-api-key-never-output"
HMAC_KEY = b"x" * 32


class FakeClient:
    def __init__(self, payload: Any = None, error: Exception | None = None) -> None:
        self.payload = payload
        self.error = error
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    def request(self, method: str, path: str, *, params: dict[str, Any]) -> Any:
        self.calls.append((method, path, params))
        if self.error:
            raise self.error
        return self.payload

    def request_with_status(
        self, method: str, path: str, *, params: dict[str, Any]
    ) -> tuple[Any, int]:
        return self.request(method, path, params=params), 200


def test_aggregate_contains_only_metadata_and_hmac_match_counts(caplog: pytest.LogCaptureFixture) -> None:
    synthetic_name = "SYNTHETIC_TEST_NAME_DO_NOT_OUTPUT"
    synthetic_phone = "SYNTHETIC_TEST_PHONE_DO_NOT_OUTPUT"
    record = {
        "customer_id": "customer-1",
        "name": synthetic_name,
        "phone_numbers": [synthetic_phone],
        "inserted_at": "2025-02-01T10:00:00Z",
    }
    client = FakeClient({"data": [record], "total_entries": 1})
    endpoint = next(item for item in probe_endpoints.ENDPOINTS if item["name"] == "customers")
    key = pseudonymize_id("customer-1", key=HMAC_KEY, namespace="xoaif/customer/v1")
    dev_keys = {"customer_id": {key}, "order_id": set(), "product_id": set()}

    with caplog.at_level(logging.DEBUG):
        result = probe_endpoints.probe_endpoint(
            client, endpoint, shop_id="12345", hmac_key=HMAC_KEY, dev_keys=dev_keys
        )
    serialized = json.dumps(result)

    assert result["total_entries"] == 1
    assert result["dev_matched_records"] == 1
    assert result["dev_match_rate"] == 1.0
    fields = {item["field"]: item for item in result["fields"]}
    assert fields["name"]["types"] == ["string"]
    assert fields["name"]["non_null_rate"] == 1.0
    assert synthetic_name not in serialized
    assert synthetic_phone not in serialized
    assert SECRET not in serialized
    assert synthetic_name not in caplog.text
    assert synthetic_phone not in caplog.text
    assert SECRET not in caplog.text


def test_customer_alternate_id_is_reported_as_a_separate_hmac_candidate() -> None:
    record = {"id": "customer-internal-id", "customer_id": "customer-order-id"}
    endpoint = next(item for item in probe_endpoints.ENDPOINTS if item["name"] == "customers")
    key = pseudonymize_id(
        "customer-internal-id", key=HMAC_KEY, namespace="xoaif/customer/v1"
    )
    result = probe_endpoints.aggregate_records(
        [record],
        endpoint,
        hmac_key=HMAC_KEY,
        dev_keys={"customer_id": {key}, "order_id": set(), "product_id": set()},
    )

    assert result["dev_match_rate"] == 0.0
    assert result["alternate_join_key_results"]["id"]["dev_matched_records"] == 1
    assert "customer-internal-id" not in json.dumps(result)


def test_sampling_is_capped_and_rating_distribution_is_count_only() -> None:
    records = [
        {"order_id": f"order-{index}", "rating": index % 5 + 1}
        for index in range(probe_endpoints.MAX_SAMPLE_RECORDS + 2)
    ]
    endpoint = next(item for item in probe_endpoints.ENDPOINTS if item["name"] == "shopee_evaluate")
    result = probe_endpoints.aggregate_records(
        records,
        endpoint,
        hmac_key=HMAC_KEY,
        dev_keys={"customer_id": set(), "order_id": set(), "product_id": set()},
    )

    assert result["sampled_records"] == 500
    assert result["rating_distribution"] == {"1": 100, "2": 100, "3": 100, "4": 100, "5": 100}
    assert "order-0" not in json.dumps(result)


@pytest.mark.parametrize("status", [401, 403, 404])
def test_unavailable_endpoint_skips_schema_aggregation(status: int) -> None:
    client = FakeClient(error=PancakeAPIError("sanitized", status_code=status))
    endpoint = probe_endpoints.ENDPOINTS[0]

    result = probe_endpoints.probe_endpoint(
        client,
        endpoint,
        shop_id="12345",
        hmac_key=HMAC_KEY,
        dev_keys={"customer_id": set(), "order_id": set(), "product_id": set()},
    )

    assert result["status"] == "skipped"
    assert result["http_status"] == status
    assert result["fields"] == []


def test_empty_endpoint_skips_aggregation() -> None:
    client = FakeClient({"data": [], "total_entries": 0})

    result = probe_endpoints.probe_endpoint(
        client,
        probe_endpoints.ENDPOINTS[0],
        shop_id="12345",
        hmac_key=HMAC_KEY,
        dev_keys={"customer_id": set(), "order_id": set(), "product_id": set()},
    )

    assert result["status"] == "skipped"
    assert result["sampled_records"] == 0
    assert result["fields"] == []


def test_probe_samples_at_most_500_records_across_pagination() -> None:
    class PagedClient:
        def __init__(self) -> None:
            self.pages: list[int] = []

        def request(self, method: str, path: str, *, params: dict[str, Any]) -> Any:
            page = params["page_number"]
            self.pages.append(page)
            return {
                "data": [{"product_id": f"product-{page}-{index}"} for index in range(50)],
                "total_entries": 10_000,
            }

        def request_with_status(
            self, method: str, path: str, *, params: dict[str, Any]
        ) -> tuple[Any, int]:
            return self.request(method, path, params=params), 200

    client = PagedClient()
    endpoint = probe_endpoints.ENDPOINTS[0]
    result = probe_endpoints.probe_endpoint(
        client,  # type: ignore[arg-type]
        endpoint,
        shop_id="12345",
        hmac_key=HMAC_KEY,
        dev_keys={"customer_id": set(), "order_id": set(), "product_id": set()},
    )

    assert len(client.pages) <= 10
    assert client.pages[0] == 1
    assert client.pages[-1] == 200
    assert result["sampled_records"] == 500
