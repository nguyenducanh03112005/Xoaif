"""Fail-closed sanitization for API samples written into documentation."""

from __future__ import annotations

import secrets
from collections.abc import Iterable, Mapping
from typing import Any

_PII_NAME_MARKERS = (
    "name",
    "phone",
    "mobile",
    "email",
    "address",
    "social",
    "facebook",
    "zalo",
    "note",
    "comment",
    "message",
    "content",
    "description",
    "conversation",
    "review",
    "link",
    "url",
    "token",
    "secret",
    "password",
)


def _placeholder(value: Any) -> Any:
    """Return a typed dummy value without retaining user content or list sizes."""
    if isinstance(value, bool):
        return False
    if isinstance(value, int):
        return 0
    if isinstance(value, float):
        return 0.0
    if isinstance(value, str):
        return "[synthetic]"
    if isinstance(value, list):
        return []
    if isinstance(value, dict):
        return {}
    return None


def sanitize_samples(
    records: Iterable[Mapping[str, Any]],
    *,
    allowed_fields: Iterable[str],
    identifier_fields: Iterable[str] = (),
    free_text_fields: Iterable[str] = (),
) -> list[dict[str, Any]]:
    """Preserve only explicitly approved scalar values; replace IDs and text.

    Field paths use dot notation, such as order.status. Unknown fields are
    replaced with typed placeholders. Real identifier values are kept only in
    this function's temporary memory and are never emitted.
    """
    allowed = set(allowed_fields)
    identifiers = {name.lower() for name in identifier_fields}
    free_text = {name.lower() for name in free_text_fields}
    fake_ids: dict[tuple[str, str], str] = {}

    def clean(value: Any, path: str) -> Any:
        leaf = path.rsplit(".", 1)[-1].lower()
        if leaf in identifiers or leaf.endswith("_id") or leaf == "id":
            key = (path, repr(value))
            fake_ids.setdefault(key, f"FAKE_{secrets.token_hex(4).upper()}")
            return fake_ids[key]
        if leaf in free_text or any(marker in leaf for marker in _PII_NAME_MARKERS):
            return "[synthetic text]"
        if path not in allowed:
            return _placeholder(value)
        if isinstance(value, dict):
            return {
                str(key): clean(item, f"{path}.{key}")
                for key, item in value.items()
            }
        if isinstance(value, list):
            return []
        return value

    return [
        {str(key): clean(value, str(key)) for key, value in record.items()}
        for record in records
    ]
