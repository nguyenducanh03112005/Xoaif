"""Build a restricted star schema from the locked snapshot, before test_start only."""

from __future__ import annotations

from collections import Counter
import argparse
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Any
from zoneinfo import ZoneInfo

import duckdb
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from ingest.analysis_amendment import load_analysis_amendment
from ingest.identifiers import pseudonymize_id
from ingest.settings import load_analytics_hmac_key

RAW_ROOT = PROJECT_ROOT / "data" / "raw" / "pancake_orders"
RESTRICTED_ROOT = PROJECT_ROOT / "data" / "restricted"
LOCAL_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


def parse_source_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    else:
        parsed = parsed.astimezone(timezone.utc)
    return parsed.astimezone(LOCAL_TZ)


def load_locked_inputs() -> tuple[dict[str, Any], str, dict[str, Any], Path, dict[str, Any], str]:
    config_path = PROJECT_ROOT / "config" / "split.yaml"
    lock_path = PROJECT_ROOT / "config" / "split.lock.json"
    config_bytes = config_path.read_bytes()
    config = yaml.safe_load(config_bytes)
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    split_hash = hashlib.sha256(config_bytes).hexdigest()
    if config.get("status") != "locked" or split_hash != lock.get("config_sha256"):
        raise ValueError("split configuration is not locked to its sidecar hash")
    snapshot_id = config.get("snapshot_id")
    if not isinstance(snapshot_id, str) or snapshot_id != lock.get("snapshot_id"):
        raise ValueError("snapshot ID does not match the split lock")
    snapshot_dir = RAW_ROOT / snapshot_id
    manifest_path = snapshot_dir / "manifest.json"
    manifest_bytes = manifest_path.read_bytes()
    manifest_hash = hashlib.sha256(manifest_bytes).hexdigest()
    if (
        manifest_hash != lock.get("snapshot_manifest_sha256")
        or manifest_hash != config.get("snapshot_manifest_sha256")
    ):
        raise ValueError("snapshot manifest hash does not match the split lock")
    manifest = json.loads(manifest_bytes)
    if manifest.get("status") != "complete" or manifest.get("snapshot_id") != snapshot_id:
        raise ValueError("locked snapshot is incomplete or has a different ID")
    if config.get("source_timestamp_timezone") != "UTC":
        raise ValueError("source timestamp interpretation is not the locked UTC rule")
    if config.get("timezone") != "Asia/Ho_Chi_Minh":
        raise ValueError("local analysis timezone does not match the split")
    amendment, amendment_hash, _ = load_analysis_amendment(PROJECT_ROOT)
    return config, split_hash, manifest, snapshot_dir, amendment, amendment_hash


def safe_status(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reuse-if-current",
        action="store_true",
        help="reuse a verified warehouse built from the exact locked snapshot and split",
    )
    args = parser.parse_args()
    try:
        config, split_hash, manifest, snapshot_dir, amendment, amendment_hash = load_locked_inputs()
        hmac_key = load_analytics_hmac_key(PROJECT_ROOT / "xoaif.env")
        test_start = date.fromisoformat(str(config["test_start"]))
        analysis_start = date.fromisoformat(str(amendment["analysis_start"]))
        snapshot_id = str(config["snapshot_id"])
        allowed = set(config["n_candidates_days"])
        if config.get("primary_n_days") not in allowed:
            raise ValueError("primary N is outside the locked candidate set")
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError, yaml.YAMLError) as exc:
        print(f"Warehouse build stopped ({type(exc).__name__}); restricted output was not replaced.")
        return 2

    db_path = RESTRICTED_ROOT / "xoaif_dev.duckdb"
    prior_manifest_path = RESTRICTED_ROOT / "day1_warehouse_manifest.json"
    if args.reuse_if_current and db_path.is_file() and prior_manifest_path.is_file():
        try:
            prior = json.loads(prior_manifest_path.read_text(encoding="utf-8"))
            expected_tables = {
                "dim_customer", "dim_date", "dim_order_status", "dim_product",
                "fact_order_items", "fact_orders",
            }
            check = duckdb.connect(str(db_path), read_only=True)
            tables = {row[0] for row in check.execute("SHOW TABLES").fetchall()}
            latest = check.execute("SELECT MAX(local_date) FROM fact_orders").fetchone()[0]
            earliest = check.execute("SELECT MIN(local_date) FROM fact_orders").fetchone()[0]
            order_count = int(check.execute("SELECT COUNT(*) FROM fact_orders").fetchone()[0])
            check.close()
            if (
                prior.get("snapshot_id") == config.get("snapshot_id")
                and prior.get("split_sha256") == split_hash
                and prior.get("analysis_start") == analysis_start.isoformat()
                and prior.get("analysis_amendment_sha256") == amendment_hash
                and prior.get("development_exclusive_end") == date.fromisoformat(str(config["test_start"])).isoformat()
                and prior.get("test_labels_loaded") is False
                and tables == expected_tables
                and order_count == prior.get("development_orders")
                and (earliest is None or earliest >= analysis_start)
                and (latest is None or latest < date.fromisoformat(str(config["test_start"])))
            ):
                public_quality_path = PROJECT_ROOT / "outputs" / "tables" / "dev_quality_summary.json"
                if public_quality_path.is_file():
                    public_quality = json.loads(public_quality_path.read_text(encoding="utf-8"))
                    public_quality.pop("split_sha256", None)
                    public_quality_path.write_text(
                        json.dumps(public_quality, indent=2) + "\n", encoding="utf-8"
                    )
                print(f"Current development warehouse reused: {order_count} orders; test labels were not loaded.")
                return 0
        except Exception:
            # A stale or unreadable artifact is not trusted; rebuild from the
            # checksum-verified source snapshot below.
            pass

    order_rows: list[tuple[str, str | None, date, int | None, int]] = []
    item_rows: set[tuple[str, str]] = set()
    status_counts: Counter[str] = Counter()
    quality: Counter[str] = Counter()
    dates: set[date] = set()
    seen_order_keys: set[str] = set()
    rows_seen = 0
    source_rows_seen = 0
    snapshot_root = snapshot_dir.resolve()

    try:
        for expected_page, page_record in enumerate(manifest["pages"], start=1):
            page_path = (snapshot_dir / page_record["file"]).resolve()
            if not page_path.is_relative_to(snapshot_root):
                raise ValueError("snapshot page path escaped its directory")
            page_bytes = page_path.read_bytes()
            if hashlib.sha256(page_bytes).hexdigest() != page_record.get("sha256"):
                raise ValueError("snapshot page checksum mismatch")
            payload = json.loads(page_bytes)
            pagination = manifest.get("pagination", {})
            expected_metadata = {
                "page_number": expected_page,
                "page_size": pagination.get("page_size_effective"),
                "total_pages": pagination.get("total_pages"),
                "total_entries": pagination.get("total_entries"),
            }
            if any(payload.get(key) != value for key, value in expected_metadata.items()):
                raise ValueError("snapshot page metadata mismatch")
            source_rows = payload.get("data")
            if not isinstance(source_rows, list) or len(source_rows) != page_record.get("rows"):
                raise ValueError("snapshot page row count mismatch")

            for row in source_rows:
                source_rows_seen += 1
                if not isinstance(row, dict):
                    raise ValueError("snapshot order row had an invalid shape")
                # For every row, inspect only inserted_at until it is proven to be
                # development data. No fields from the reserved test are accessed.
                local_timestamp = parse_source_timestamp(row.get("inserted_at"))
                if local_timestamp is None:
                    continue
                local_day = local_timestamp.date()
                if local_day >= test_start:
                    continue
                if local_day < analysis_start:
                    continue

                rows_seen += 1
                dates.add(local_day)
                status = safe_status(row.get("status"))
                status_key = str(status) if status is not None else "<UNMAPPED>"
                status_counts[status_key] += 1
                if status is None:
                    quality["missing_or_non_integer_status"] += 1

                # Only status-3 purchases enter customer and product analysis.
                customer_key: str | None = None
                product_count = 0
                if status == 3:
                    source_id = row.get("id")
                    if source_id is None or str(source_id).strip() == "":
                        raise ValueError("development order missing its stable ID")
                    order_key = pseudonymize_id(
                        source_id, key=hmac_key, namespace="xoaif/order/v1"
                    )
                    if order_key in seen_order_keys:
                        raise ValueError("duplicate pseudonymized development order key")
                    seen_order_keys.add(order_key)

                    customer = row.get("customer")
                    customer_id = customer.get("customer_id") if isinstance(customer, dict) else None
                    if customer_id is not None and str(customer_id).strip():
                        customer_key = pseudonymize_id(
                            customer_id, key=hmac_key, namespace="xoaif/customer/v1"
                        )
                    else:
                        quality["valid_orders_missing_customer_id"] += 1

                    source_items = row.get("items")
                    if not isinstance(source_items, list) or not source_items:
                        quality["valid_orders_without_items"] += 1
                        source_items = []
                    product_keys: set[str] = set()
                    for item in source_items:
                        if not isinstance(item, dict):
                            quality["invalid_item_shapes"] += 1
                            continue
                        product_id = item.get("product_id")
                        if product_id is None or str(product_id).strip() == "":
                            quality["item_rows_missing_product_id"] += 1
                            continue
                        product_keys.add(
                            pseudonymize_id(
                                product_id, key=hmac_key, namespace="xoaif/product/v1"
                            )
                        )
                    product_count = len(product_keys)
                    item_rows.update((order_key, product_key) for product_key in product_keys)
                else:
                    # Retain only pseudonymous order key on restricted status DQ rows.
                    source_id = row.get("id")
                    if source_id is None or str(source_id).strip() == "":
                        raise ValueError("development order missing its stable ID")
                    order_key = pseudonymize_id(
                        source_id, key=hmac_key, namespace="xoaif/order/v1"
                    )
                    if order_key in seen_order_keys:
                        raise ValueError("duplicate pseudonymized development order key")
                    seen_order_keys.add(order_key)

                order_rows.append((order_key, customer_key, local_day, status, product_count))

    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(f"Warehouse build stopped ({type(exc).__name__}); restricted output was not replaced.")
        return 2

    if (
        source_rows_seen != manifest.get("row_count")
        or rows_seen != len(order_rows)
        or len(order_rows) > source_rows_seen
    ):
        print("Warehouse build stopped: development row reconciliation failed.")
        return 2
    if any(code not in {"0", "1", "3", "4", "5", "6"} for code in status_counts if not code.startswith("<")):
        print("Warehouse build stopped: unmapped status found; owner decision is required.")
        return 2
    if quality["missing_or_non_integer_status"]:
        print("Warehouse build stopped: missing/non-integer development status found.")
        return 2

    RESTRICTED_ROOT.mkdir(parents=True, exist_ok=True)
    temporary_db = RESTRICTED_ROOT / "xoaif_dev.building.duckdb"
    if temporary_db.exists():
        temporary_db.unlink()
    try:
        connection = duckdb.connect(str(temporary_db))
        connection.execute("CREATE TABLE dim_date (local_date DATE PRIMARY KEY, year INTEGER, quarter INTEGER, month INTEGER, day INTEGER, day_of_week INTEGER)")
        connection.executemany(
            "INSERT INTO dim_date VALUES (?, ?, ?, ?, ?, ?)",
            [(d, d.year, (d.month - 1) // 3 + 1, d.month, d.day, d.weekday()) for d in sorted(dates)],
        )
        connection.execute("CREATE TABLE dim_order_status (status_code INTEGER PRIMARY KEY)")
        connection.executemany("INSERT INTO dim_order_status VALUES (?)", [(int(code),) for code in sorted(status_counts, key=lambda value: int(value))])
        connection.execute("CREATE TABLE dim_customer (customer_key VARCHAR PRIMARY KEY)")
        connection.executemany(
            "INSERT INTO dim_customer VALUES (?)",
            [(key,) for key in sorted({row[1] for row in order_rows if row[1] is not None})],
        )
        connection.execute("CREATE TABLE dim_product (product_key VARCHAR PRIMARY KEY)")
        connection.executemany("INSERT INTO dim_product VALUES (?)", [(key,) for key in sorted({product_key for _, product_key in item_rows})])
        connection.execute("CREATE TABLE fact_orders (order_key VARCHAR PRIMARY KEY, customer_key VARCHAR, local_date DATE, status_code INTEGER, distinct_product_count INTEGER)")
        connection.executemany("INSERT INTO fact_orders VALUES (?, ?, ?, ?, ?)", order_rows)
        connection.execute("CREATE TABLE fact_order_items (order_key VARCHAR, product_key VARCHAR, PRIMARY KEY (order_key, product_key))")
        connection.executemany("INSERT INTO fact_order_items VALUES (?, ?)", sorted(item_rows))
        connection.execute("CREATE INDEX fact_orders_date_idx ON fact_orders(local_date)")
        connection.execute("CREATE INDEX fact_orders_customer_idx ON fact_orders(customer_key)")
        connection.close()
        temporary_db.replace(db_path)
    except Exception as exc:
        try:
            temporary_db.unlink(missing_ok=True)
        except OSError:
            pass
        print(f"Warehouse build stopped ({type(exc).__name__}); restricted output was not replaced.")
        return 2

    output_dir = PROJECT_ROOT / "outputs" / "tables"
    output_dir.mkdir(parents=True, exist_ok=True)
    status_path = output_dir / "dev_status_counts.csv"
    with status_path.open("w", encoding="utf-8-sig", newline="") as handle:
        import csv

        writer = csv.writer(handle)
        writer.writerow(["status_code", "development_order_count"])
        for code, count in sorted(status_counts.items(), key=lambda item: (item[0].startswith("<"), item[0])):
            writer.writerow([code, count])

    quality_path = output_dir / "dev_quality_summary.json"
    safe_quality = {
        "snapshot_id": snapshot_id,
        "split_sha256": split_hash,
        "analysis_start": analysis_start.isoformat(),
        "analysis_amendment_sha256": amendment_hash,
        "development_exclusive_end": test_start.isoformat(),
        "development_orders": rows_seen,
        "valid_status_3_orders": status_counts.get("3", 0),
        "valid_status_3_orders_missing_customer_id": quality["valid_orders_missing_customer_id"],
        "valid_status_3_orders_without_items": quality["valid_orders_without_items"],
        "valid_item_rows_missing_product_id": quality["item_rows_missing_product_id"],
        "invalid_item_shapes": quality["invalid_item_shapes"],
        "development_customer_keys": connection_count(db_path, "dim_customer"),
        "development_product_keys": connection_count(db_path, "dim_product"),
        "development_date_min": min(dates).isoformat() if dates else None,
        "development_date_max": max(dates).isoformat() if dates else None,
        "money_fields_used": False,
        "test_labels_loaded": False,
    }
    public_quality = {key: value for key, value in safe_quality.items() if key != "split_sha256"}
    quality_path.write_text(json.dumps(public_quality, indent=2) + "\n", encoding="utf-8")
    run_manifest = {
        **safe_quality,
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
        "database_path": "data/restricted/xoaif_dev.duckdb",
        "tables": ["fact_orders", "fact_order_items", "dim_customer", "dim_product", "dim_date", "dim_order_status"],
    }
    (RESTRICTED_ROOT / "day1_warehouse_manifest.json").write_text(
        json.dumps(run_manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Development warehouse built: {rows_seen} orders; local dates in [{analysis_start.isoformat()}, {test_start.isoformat()}).")
    print(f"Status-3 orders: {status_counts.get('3', 0)}; customer keys: {safe_quality['development_customer_keys']}.")
    print(f"Restricted DuckDB: {db_path.relative_to(PROJECT_ROOT)}")
    print("Pre-opening orders, monetary fields, text fields, test labels, and post-test-start behavior were not written.")
    return 0


def connection_count(db_path: Path, table: str) -> int:
    connection = duckdb.connect(str(db_path), read_only=True)
    try:
        return int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
    finally:
        connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
