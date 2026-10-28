"""Count pre-T2 eligible customers for Amendment 06-HO2 power planning only.

Never inspects fields other than inserted_at for rows at/after T2 and never
reads or computes HO2 labels. Output contains aggregate counts only.
"""
from __future__ import annotations

from collections import Counter
from datetime import date
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from features.day2_data import local_day, safe_status  # noqa: E402
from features.money import assess_order_money  # noqa: E402
from ingest.identifiers import pseudonymize_id  # noqa: E402
from ingest.settings import load_analytics_hmac_key  # noqa: E402

T2 = date(2026, 4, 20)
ANALYSIS_START = date(2024, 4, 1)


def pre_t2_day(order: Mapping[str, Any], *, t2: date = T2) -> date | None:
    """Read only inserted_at; return an eligible-history date strictly before T2."""
    day = local_day(order.get("inserted_at"))
    if day is None or day >= t2 or day < ANALYSIS_START:
        return None
    return day


def count_pre_t2() -> dict[str, int | str]:
    # Snapshot identity is fixed in the amendment; no test evaluator/config is loaded.
    snapshot = ROOT / "data/raw/pancake_orders/20261024T052943Z"
    manifest_bytes = (snapshot / "manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    if hashlib.sha256(manifest_bytes).hexdigest() != "3536a0e5303d83a6fbddd19e6f52375ed70dd53a070d1cadb8691a66ad4acf5c":
        raise ValueError("locked snapshot manifest hash mismatch")
    key = load_analytics_hmac_key(ROOT / "xoaif.env")
    frequency: Counter[str] = Counter()
    source_rows_checked = 0
    pre_t2_rows = 0
    valid_orders = 0
    missing_customer_orders = 0
    for page_no, page_record in enumerate(manifest["pages"], 1):
        page_path = (snapshot / page_record["file"]).resolve()
        if not page_path.is_relative_to(snapshot.resolve()):
            raise ValueError("snapshot page escaped the locked snapshot directory")
        payload_bytes = page_path.read_bytes()
        if hashlib.sha256(payload_bytes).hexdigest() != page_record["sha256"]:
            raise ValueError("snapshot page checksum mismatch")
        payload = json.loads(payload_bytes)
        if payload.get("page_number") != page_no or len(payload.get("data", [])) != page_record["rows"]:
            raise ValueError("snapshot page metadata mismatch")
        for order in payload.get("data", []):
            source_rows_checked += 1
            if not isinstance(order, dict):
                continue
            day = pre_t2_day(order)
            if day is None:
                continue
            pre_t2_rows += 1
            if safe_status(order.get("status")) != 3:
                continue
            if assess_order_money(order).is_gift:
                continue
            customer = order.get("customer")
            customer_id = customer.get("customer_id") if isinstance(customer, dict) else None
            if customer_id is None or not str(customer_id).strip():
                missing_customer_orders += 1
                continue
            key_id = pseudonymize_id(customer_id, key=key, namespace="xoaif/customer/v1")
            frequency[key_id] += 1
            valid_orders += 1
    n_customers = len(frequency)
    n_repeat_eligible = sum(n >= 2 for n in frequency.values())
    return {
        "snapshot_id": "20261024T052943Z",
        "feature_date_rule": "2024-04-01 <= local date < 2026-04-20",
        "source_rows_inserted_at_checked": source_rows_checked,
        "rows_with_pre_t2_date": pre_t2_rows,
        "valid_status3_non_gift_orders_with_customer": valid_orders,
        "valid_orders_missing_customer_id": missing_customer_orders,
        "eligible_customers": n_customers,
        "frequency_ge_2_customers": n_repeat_eligible,
        "frequency_eq_1_customers": n_customers - n_repeat_eligible,
        "ho2_fields_or_labels_read": 0,
        "old_test_labels_used": 0,
    }


if __name__ == "__main__":
    print(json.dumps(count_pre_t2(), ensure_ascii=False, indent=2))
