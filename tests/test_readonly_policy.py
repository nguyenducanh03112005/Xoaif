from __future__ import annotations

import pytest

from ingest.readonly_policy import scan_source_text


@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_scanner_rejects_requests_write_methods_outside_client(method: str) -> None:
    source = f"import requests\nrequests.{method}('https://example.invalid')\n"

    findings = scan_source_text(source, "scripts/unsafe.py")

    assert findings


def test_scanner_rejects_requests_get_outside_client_too() -> None:
    findings = scan_source_text("import requests\nrequests.get('https://example.invalid')\n", "scripts/unsafe.py")

    assert findings


@pytest.mark.parametrize(
    "source",
    [
        "import httpx\nhttpx.post('https://example.invalid')\n",
        "import httpx\nhttpx.delete('https://example.invalid')\n",
    ],
)
def test_scanner_rejects_httpx_outside_client(source: str) -> None:
    assert scan_source_text(source, "notebooks/unsafe.py")


@pytest.mark.parametrize(
    "source",
    [
        "curl -X POST https://example.invalid",
        "curl --request DELETE https://example.invalid",
        "curl https://example.invalid",
        "Invoke-RestMethod -Method Post https://example.invalid",
        "fetch('https://example.invalid')",
    ],
)
def test_scanner_rejects_shell_or_alternate_http_clients(source: str) -> None:
    assert scan_source_text(source, "scripts/unsafe.sh")


def test_scanner_allows_requests_only_inside_approved_client() -> None:
    source = "import requests\nsession.get(url, params=params)\n"

    assert scan_source_text(source, "src/ingest/client.py") == []


def test_scanner_rejects_python_standard_library_network_calls() -> None:
    findings = scan_source_text("from urllib.request import urlopen\nurlopen(url)\n", "src/unsafe.py")

    assert findings
