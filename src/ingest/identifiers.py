"""Stable, domain-separated pseudonyms for identifiers in restricted data."""

from __future__ import annotations

import hashlib
import hmac


def pseudonymize_id(identifier: str | int, *, key: bytes, namespace: str) -> str:
    """Create an HMAC-SHA-256 pseudonym without retaining the source ID."""
    if len(key) < 32:
        raise ValueError("HMAC key must contain at least 32 bytes.")
    if not namespace or "\x00" in namespace:
        raise ValueError("namespace must be non-empty and cannot contain NUL.")
    message = namespace.encode("utf-8") + b"\x00" + str(identifier).encode("utf-8")
    return hmac.new(key, message, hashlib.sha256).hexdigest()
