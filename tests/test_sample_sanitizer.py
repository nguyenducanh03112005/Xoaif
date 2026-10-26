from ingest.sample_sanitizer import sanitize_samples


def test_unknown_fields_and_identifiers_are_not_preserved() -> None:
    rows = [
        {
            "order_id": "real-order-1",
            "customer_id": "real-customer-1",
            "status": 16,
            "phone": "0901234567",
            "note": "Call Lan at 0901234567",
            "future_api_field": "unexpected secret text",
        }
    ]

    result = sanitize_samples(
        rows,
        allowed_fields={"status"},
        identifier_fields={"order_id", "customer_id"},
        free_text_fields={"note"},
    )
    rendered = repr(result)

    assert result[0]["status"] == 16
    assert "real-order-1" not in rendered
    assert "real-customer-1" not in rendered
    assert "0901234567" not in rendered
    assert "unexpected secret text" not in rendered
    assert result[0]["order_id"].startswith("FAKE_")


def test_repeated_identifiers_map_to_same_fake_id_within_sample_batch() -> None:
    rows = [{"customer_id": "same-real-id"}, {"customer_id": "same-real-id"}]
    result = sanitize_samples(rows, allowed_fields=[])

    assert result[0]["customer_id"] == result[1]["customer_id"]
    assert result[0]["customer_id"] != "same-real-id"
