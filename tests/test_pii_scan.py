from __future__ import annotations

from scripts.verify_pii import PATTERNS


def test_pii_tripwire_matches_email_phone_address_and_sensitive_field_values() -> None:
    sample = """
    contact: sample.user@example.invalid
    phone: 0912345678
    address: 12 Nguyen Hue, phường 1
    full_name: Nguyen Van A
    """

    assert PATTERNS["email"].search(sample)
    assert PATTERNS["phone"].search(sample)
    assert PATTERNS["address_like"].search(sample)
    assert PATTERNS["sensitive_field_value"].search(sample)


def test_pii_tripwire_does_not_match_project_aggregate_fields() -> None:
    safe = "status_code,order_count,missing_records,missing_pct\n3,11841,0,0.00"

    assert all(pattern.search(safe) is None for pattern in PATTERNS.values())


def test_phone_tripwire_does_not_join_digits_across_csv_rows() -> None:
    csv_fragment = "2022-10-01,0\n2022-11-01,0"

    assert PATTERNS["phone"].search(csv_fragment) is None


def test_phone_tripwire_does_not_treat_decimal_features_as_phone_numbers() -> None:
    safe_decimals = "first_order_month_sin,0.8660254037844387\npositive_rate,0.10206961429915334"

    assert PATTERNS["phone"].search(safe_decimals) is None


def test_address_tripwire_does_not_join_csv_rows() -> None:
    csv_fragment = "8403,UNKNOWN\n663,HA NOI\n38,Other provinces"

    assert PATTERNS["address_like"].search(csv_fragment) is None
