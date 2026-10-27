"""Build aggregate-only pre-T cohort and UNKNOWN-region evidence.

Only rows whose normalized local date is strictly before test_start are examined
beyond the timestamp field. Identifiers are HMACed with the project's key and
kept in memory only. No row-level data or category text is written.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

import duckdb
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from features.day2_data import canonical_province, local_day, normalize_product_name, safe_status
from features.money import assess_order_money
from ingest.analysis_amendment import load_analysis_amendment
from ingest.decision_amendment import load_money_adjustment_amendment
from ingest.identifiers import pseudonymize_id
from ingest.settings import load_analytics_hmac_key

SOURCE_FIELDS = ("order_sources_name", "order_sources", "ads_source", "p_utm_source")
ADDRESS_FIELD_RE = re.compile(r"address|province|city|district", re.IGNORECASE)
SOURCE_FIELD_RE = re.compile(r"source|channel|origin", re.IGNORECASE)
MISSING = "__MISSING__"


def _distinct_key(customer: Any, key: bytes) -> str | None:
    raw = customer.get("customer_id") if isinstance(customer, dict) else None
    if raw is None or not str(raw).strip():
        return None
    return pseudonymize_id(raw, key=key, namespace="xoaif/customer/v1")


def _category_key(value: Any, *, canonical_channel: bool = False) -> str:
    if value is None or value == "":
        return MISSING
    if isinstance(value, str):
        return normalize_product_name(value) or MISSING
    if canonical_channel:
        return MISSING
    # Structured source fields are grouped by their type only. Their contents
    # are never displayed or written to the aggregate artifact.
    return "__TYPE_" + type(value).__name__ + "__"


def _fmt(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def _group_categories(
    counts: Counter[str], revenue: dict[str, Decimal], total_revenue: Decimal
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    missing_n = counts.get(MISSING, 0)
    regular = sorted((value for value, n in counts.items() if value != MISSING and n >= 5))
    mapping: dict[str, str] = {MISSING: "thiếu trường" if missing_n >= 5 else "khác"}
    for i, value in enumerate(regular, 1):
        mapping[value] = f"nhóm {i}"
    small_values = [value for value, n in counts.items() if value != MISSING and n < 5]
    for value in small_values:
        mapping[value] = "khác"

    rows: list[dict[str, Any]] = []
    buckets: dict[str, list[str]] = defaultdict(list)
    for value in counts:
        buckets[mapping[value]].append(value)
    for label, values in buckets.items():
        n = sum(counts[value] for value in values)
        rev = sum((revenue.get(value, Decimal(0)) for value in values), Decimal(0))
        if label == "khác" and n < 5:
            rows.append({"group": label, "orders": None, "revenue_vnd": None, "suppressed": True})
            continue
        rows.append({
            "group": label,
            "orders": n,
            "revenue_vnd": int(rev),
            "revenue_share_percent": round(float(rev / total_revenue * 100), 4) if total_revenue else None,
            "suppressed": False,
        })
    rows.sort(key=lambda row: (row["group"] == "thiếu trường", row["group"]))
    return rows, mapping


def _read_duckdb_counts(path: Path) -> dict[str, int]:
    if not path.is_file():
        return {"available": False}  # type: ignore[return-value]
    con = duckdb.connect(str(path), read_only=True)
    values = con.execute("""
        SELECT
          COUNT(DISTINCT order_key),
          COUNT(DISTINCT order_key) FILTER (WHERE status_code = 3),
          COUNT(DISTINCT order_key) FILTER (WHERE status_code <> 3),
          COUNT(DISTINCT customer_key),
          COUNT(DISTINCT customer_key) FILTER (WHERE status_code = 3),
          COUNT(DISTINCT customer_key) FILTER (WHERE status_code <> 3),
          COUNT(DISTINCT customer_key) FILTER (
            WHERE status_code = 3 AND customer_key IS NOT NULL
          ),
          COUNT(DISTINCT customer_key) FILTER (
            WHERE status_code <> 3 AND customer_key IS NOT NULL
          ),
          (SELECT COUNT(*) FROM (
            SELECT customer_key FROM fact_orders
            WHERE customer_key IS NOT NULL
            GROUP BY customer_key
            HAVING BOOL_OR(status_code = 3) AND BOOL_OR(status_code <> 3)
          ) AS status_intersection),
          COUNT(DISTINCT customer_key) FILTER (
            WHERE status_code = 3 AND customer_key IS NOT NULL
          ),
          COUNT(DISTINCT order_key) FILTER (
            WHERE status_code <> 3 AND customer_key IS NULL
          ),
          COUNT(DISTINCT order_key) FILTER (
            WHERE status_code = 3 AND customer_key IS NULL
          )
        FROM fact_orders
    """).fetchone()
    con.close()
    names = (
        "dev_orders", "dev_status3_orders", "dev_other_status_orders",
        "dev_customers_nonnull", "dev_customers_status3", "dev_customers_other_status",
        "dev_customers_status3_only", "dev_customers_other_status_only",
        "dev_customers_status3_other_status_intersection",
        "dev_customers_status3_nonnull", "other_status_null_customer_orders",
        "status3_null_customer_orders",
    )
    return dict(zip(names, map(int, values))) | {"available": True}  # type: ignore[dict-item]


def _scan_snapshot() -> tuple[dict[str, Any], str]:
    split = yaml.safe_load((ROOT / "config/split.yaml").read_bytes())
    amendment01, _, _ = load_analysis_amendment(ROOT)
    amendment03, amendment03_hash = load_money_adjustment_amendment(ROOT)
    start = date.fromisoformat(str(amendment01["analysis_start"]))
    test_start = date.fromisoformat(str(split["test_start"]))
    snapshot_id = str(split["snapshot_id"])
    snapshot_root = (ROOT / "data/raw/pancake_orders" / snapshot_id).resolve()
    manifest_bytes = (snapshot_root / "manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    manifest_hash = hashlib.sha256(manifest_bytes).hexdigest()
    if manifest_hash != split.get("snapshot_manifest_sha256"):
        raise ValueError("raw snapshot manifest does not match the locked split")
    key = load_analytics_hmac_key(ROOT / "xoaif.env")
    profile = json.loads((ROOT / "outputs/tables/day1_analysis_start_profile.json").read_text(encoding="utf-8"))
    trial_start = date.fromisoformat(profile["pre_analysis_date_min"])
    trial_end = date.fromisoformat(profile["pre_analysis_date_max"])
    expected_trial_orders = int(profile["pre_analysis_order_count"])

    all_status3: set[str] = set()
    pre_only_candidates: set[str] = set()
    dev_status3: set[str] = set()
    trial_customer_keys: set[str] = set()
    dev_flags: dict[str, list[bool]] = {}
    trial_orders = 0
    source_rows_seen = 0
    status3_dev_orders = 0
    status3_dev_missing_customer = 0
    gift_orders_dev = 0
    total_revenue = Decimal(0)
    revenue_missing_orders = 0
    province_counts: Counter[str] = Counter()
    province_revenue: defaultdict[str, Decimal] = defaultdict(Decimal)
    source_counts: dict[str, Counter[str]] = {name: Counter() for name in SOURCE_FIELDS}
    source_revenue: dict[str, defaultdict[str, Decimal]] = {name: defaultdict(Decimal) for name in SOURCE_FIELDS}
    province_source_counts: dict[str, Counter[tuple[str, str]]] = {
        name: Counter() for name in SOURCE_FIELDS
    }
    province_source_revenue: dict[str, defaultdict[tuple[str, str], Decimal]] = {
        name: defaultdict(Decimal) for name in SOURCE_FIELDS
    }
    field_paths: set[str] = set()
    field_nonempty: Counter[str] = Counter()

    for page_no, page_record in enumerate(manifest["pages"], start=1):
        page_path = (snapshot_root / page_record["file"]).resolve()
        if not page_path.is_relative_to(snapshot_root):
            raise ValueError("snapshot page escaped its root")
        page_bytes = page_path.read_bytes()
        if hashlib.sha256(page_bytes).hexdigest() != page_record.get("sha256"):
            raise ValueError("snapshot page checksum mismatch")
        payload = json.loads(page_bytes)
        rows = payload.get("data", [])
        if payload.get("page_number") != page_no or len(rows) != page_record.get("rows"):
            raise ValueError("snapshot page metadata mismatch")
        for row in rows:
            source_rows_seen += 1
            if not isinstance(row, dict):
                continue
            # The timestamp is the only field read until the row is known to be
            # strictly before T. No status, ID, address, label, or other field
            # from T-or-later rows is accessed.
            day = local_day(row.get("inserted_at"))
            if day is None or day >= test_start:
                continue

            customer = row.get("customer") if isinstance(row.get("customer"), dict) else None
            key_for_row = _distinct_key(customer, key)
            if trial_start <= day <= trial_end:
                trial_orders += 1
                if key_for_row is not None:
                    trial_customer_keys.add(key_for_row)

            if safe_status(row.get("status")) != 3:
                continue
            if key_for_row is not None:
                all_status3.add(key_for_row)
            if day < start:
                if key_for_row is not None:
                    pre_only_candidates.add(key_for_row)
                continue

            status3_dev_orders += 1
            if key_for_row is None:
                status3_dev_missing_customer += 1
            else:
                dev_status3.add(key_for_row)
                dev_flags.setdefault(key_for_row, [False, False])
            assessment = assess_order_money(row)
            if assessment.is_gift:
                gift_orders_dev += 1
                if key_for_row is not None:
                    dev_flags[key_for_row][0] = True
            elif key_for_row is not None:
                dev_flags[key_for_row][1] = True

            address = row.get("shipping_address")
            province_value = address.get("province_name") if isinstance(address, dict) else None
            province = canonical_province(province_value)
            province_group = "missing" if province is None else "present"
            province_counts[province_group] += 1

            for field in row:
                field_text = str(field)
                if ADDRESS_FIELD_RE.search(field_text):
                    field_paths.add(field_text)
                if SOURCE_FIELD_RE.search(field_text):
                    field_paths.add(field_text)
            if isinstance(address, dict):
                for field in address:
                    field_text = str(field)
                    if ADDRESS_FIELD_RE.search(field_text):
                        field_paths.add("shipping_address." + field_text)
            if isinstance(customer, dict):
                for field in customer:
                    field_text = str(field)
                    if ADDRESS_FIELD_RE.search(field_text):
                        field_paths.add("customer." + field_text)

            revenue = assessment.revenue_recognized
            if revenue is None:
                revenue_missing_orders += 1
            else:
                total_revenue += revenue
                province_revenue[province_group] += revenue

            for field in SOURCE_FIELDS:
                value = row.get(field)
                category = _category_key(value, canonical_channel=(field == "order_sources_name"))
                source_counts[field][category] += 1
                if category != MISSING:
                    field_nonempty[field] += 1
                if revenue is not None:
                    source_revenue[field][category] += revenue
                province_source_counts[field][(province_group, category)] += 1
                if revenue is not None:
                    province_source_revenue[field][(province_group, category)] += revenue

    if source_rows_seen != manifest.get("row_count"):
        raise ValueError("snapshot row count does not match its manifest")
    if trial_orders != expected_trial_orders:
        raise ValueError("pre-analysis trial-order aggregate differs from the locked profile")

    pre_only = all_status3 - dev_status3
    pre_only_trial = pre_only & trial_customer_keys
    gift_only = {customer for customer in dev_status3 if not dev_flags[customer][1]}
    scoring_keys = dev_status3 - gift_only
    duckdb_counts = _read_duckdb_counts(ROOT / "data/restricted/xoaif_dev.duckdb")
    preflight_rows = list(__import__("csv").DictReader(
        (ROOT / "outputs/tables/eligibility_preflight.csv").open(encoding="utf-8-sig", newline="")
    ))
    preflight = int(next(row["eligible_customers"] for row in preflight_rows if row["candidate"] == "N180"))
    frozen_scoring = int(json.loads((ROOT / "outputs/metrics/day2_segmentation.json").read_text(encoding="utf-8"))["customer_count"])
    unexplained = preflight - len(pre_only) - len(gift_only) - len(scoring_keys)

    t1 = {
        "unit": "distinct_customers_with_nonnull_id",
        "A_all_status3_before_T": len(all_status3),
        "preflight_reference": preflight,
        "A_matches_preflight": len(all_status3) == preflight,
        "B_status3_in_DEV": len(dev_status3),
        "B_matches_DuckDB": bool(duckdb_counts.get("available")) and len(dev_status3) == duckdb_counts.get("dev_customers_status3_nonnull"),
        "A_minus_B_only_pre_analysis": len(pre_only),
        "A_minus_B_customers_with_any_476_trial_order": len(pre_only_trial),
        "trial_orders_in_profile_window": trial_orders,
        "B_customers_with_only_gift_status3_orders": len(gift_only),
        "B_after_non_gift_customer_filter": len(scoring_keys),
        "scoring_reference": frozen_scoring,
        "scoring_matches_reference": len(scoring_keys) == frozen_scoring,
        "pre_analysis_only_x_gift_only_intersection": len(pre_only & gift_only),
        "preflight_minus_direct_removals_minus_scoring_residual": unexplained,
        "status3_dev_missing_customer_id_orders": status3_dev_missing_customer,
        "status3_dev_gift_orders": gift_orders_dev,
        "primary_feature_filters": {
            "status3": "required before customer set",
            "customer_id_nonnull": "required before customer set",
            "local_date": "analysis_start <= date < T",
            "order_gift": "customer kept if at least one non-gift status-3 DEV order exists",
            "exclude_adjusted": False,
            "line_items_required_for_customer_cohort": False,
            "other_customer_filters": [],
        },
    }

    t2_groups: dict[str, Any] = {}
    for field in SOURCE_FIELDS:
        rows, mapping = _group_categories(source_counts[field], source_revenue[field], total_revenue)
        cross_counter: Counter[tuple[str, str]] = Counter()
        cross_rev: defaultdict[tuple[str, str], Decimal] = defaultdict(Decimal)
        for (province_group, raw_category), n in province_source_counts[field].items():
            mapped = mapping.get(raw_category, "khác")
            cross_counter[(province_group, mapped)] += n
            cross_rev[(province_group, mapped)] += province_source_revenue[field].get((province_group, raw_category), Decimal(0))
        cross_rows = []
        for province_group in ("missing", "present"):
            small_n = sum(n for (pg, group), n in cross_counter.items() if pg == province_group and n < 5)
            small_rev = sum((v for (pg, group), v in cross_rev.items() if pg == province_group and cross_counter[(pg, group)] < 5), Decimal(0))
            if small_n:
                cross_rows.append({"province": province_group, "source_group": "other", "orders": small_n if small_n >= 5 else None,
                                   "revenue_vnd": int(small_rev) if small_n >= 5 else None, "suppressed": small_n < 5})
            for (pg, group), n in sorted(cross_counter.items()):
                if pg != province_group or n < 5:
                    continue
                rev = cross_rev[(pg, group)]
                cross_rows.append({"province": pg, "source_group": group, "orders": n, "revenue_vnd": int(rev),
                                   "revenue_share_percent": round(float(rev / total_revenue * 100), 4) if total_revenue else None,
                                   "suppressed": False})
        t2_groups[field] = {
            "nonempty_orders": field_nonempty[field] if field_nonempty[field] >= 5 else None,
            "missing_orders": status3_dev_orders - field_nonempty[field] if status3_dev_orders - field_nonempty[field] >= 5 else None,
            "small_cell_suppressed": field_nonempty[field] < 5 or status3_dev_orders - field_nonempty[field] < 5,
            "groups": rows,
            "province_missing_intersection": cross_rows,
        }

    province_summary = []
    for group, label in (("missing", "missing_province"), ("present", "province_present")):
        n = province_counts[group]
        amount = province_revenue[group]
        province_summary.append({
            "group": label,
            "orders": n if n >= 5 else None,
            "revenue_vnd": int(amount) if n >= 5 else None,
            "revenue_share_percent": round(float(amount / total_revenue * 100), 4) if total_revenue and n >= 5 else None,
            "suppressed": n < 5,
        })
    t2 = {
        "scope": "status3 DEV orders with local_date in [2024-04-01, 2025-10-22)",
        "unit": "orders",
        "status3_dev_orders": status3_dev_orders,
        "province_field": "shipping_address.province_name",
        "province_missing_orders": province_counts["missing"],
        "province_missing_rate_percent": round(province_counts["missing"] / status3_dev_orders * 100, 4) if status3_dev_orders else None,
        "province_and_revenue_groups": province_summary,
        "revenue_recognized_orders": status3_dev_orders - revenue_missing_orders,
        "revenue_missing_orders": revenue_missing_orders,
        "revenue_recognized_total_vnd": int(total_revenue),
        "missing_province_revenue_vnd": int(province_revenue["missing"]),
        "missing_province_revenue_share_percent": round(float(province_revenue["missing"] / total_revenue * 100), 4) if total_revenue else None,
        "source_address_field_names_present": sorted(field_paths),
        "source_channel_fields_analyzed": list(SOURCE_FIELDS),
        "source_channel_group_distributions": t2_groups,
        "source_channel_values_printed": False,
        "small_cells_suppressed": True,
        "total_revenue_unit": "VND; Amendment 03 assess_order_money.revenue_recognized",
    }

    payload = {
        "snapshot_id": snapshot_id,
        "analysis_start": start.isoformat(),
        "test_start_exclusive": test_start.isoformat(),
        "snapshot_manifest_sha256": manifest_hash,
        "amendment_03_sha256": amendment03_hash,
        "test_labels_loaded": False,
        "test_behavior_loaded": False,
        "unit_note": "No source identifiers or raw values are stored; HMAC pseudonyms exist only in memory during the run.",
        "t1": t1,
        "duckdb": duckdb_counts,
        "t2": t2,
    }
    return payload, amendment03["revenue_rule"]["primary_expression"]


def _write_cohort_report(data: dict[str, Any]) -> None:
    t1 = data["t1"]
    db = data["duckdb"]
    residual = t1["preflight_minus_direct_removals_minus_scoring_residual"]
    report = f"""# Đối soát cohort bằng đếm trực tiếp

Phạm vi: snapshot {data['snapshot_id']}; chỉ status 3 có local_date < T được đưa vào cohort A. Đếm ID khác biệt bằng HMAC chuẩn của dự án trong RAM; không in/lưu ID. DuckDB được mở read-only.

## Cầu nối khách

| Cohort/bước | Định nghĩa | Khách distinct | Đếm trực tiếp và đối chiếu |
|---|---|---:|---|
| A | >=1 đơn status 3, có ID, local_date < 2025-10-22; không cận dưới | {_fmt(t1['A_all_status3_before_T'])} | { 'khớp' if t1['A_matches_preflight'] else 'không khớp' } với preflight 5.499 |
| A − B | Chỉ có đơn status 3 trước 2024-04-01 | {_fmt(t1['A_minus_B_only_pre_analysis'])} | Trực tiếp từ set HMAC A trừ B; trong đó {_fmt(t1['A_minus_B_customers_with_any_476_trial_order'])} có ít nhất một đơn thuộc {_fmt(t1['trial_orders_in_profile_window'])} đơn bán thử 2022-06-04 đến 2022-09-21. |
| B | >=1 đơn status 3, ID không NULL, [2024-04-01, 2025-10-22) | {_fmt(t1['B_status3_in_DEV'])} | { 'khớp' if t1['B_matches_DuckDB'] else 'không khớp' } với DuckDB 5.174 |
| B bị loại | Mọi đơn status 3 DEV của khách đều là đơn quà theo Amendment 03 | {_fmt(t1['B_customers_with_only_gift_status3_orders'])} | Trực tiếp bằng cờ is_gift từ assess_order_money |
| Scoring | B trừ khách chỉ có status-3 order quà; customer ID hợp lệ và trước T | {_fmt(t1['B_after_non_gift_customer_filter'])} | So với metric đóng băng {_fmt(t1['scoring_reference'])}: { 'khớp' if t1['scoring_matches_reference'] else 'không khớp' } |

Số học: 5.499 − {_fmt(t1['A_minus_B_only_pre_analysis'])} − {_fmt(t1['B_customers_with_only_gift_status3_orders'])} = {_fmt(t1['B_after_non_gift_customer_filter'])}. **phần dư chưa giải thích: {_fmt(residual)}**.

Giao điều kiện: A−B với 476 đơn bán thử = {_fmt(t1['A_minus_B_customers_with_any_476_trial_order'])} khách. A−B với gift-only B = {_fmt(t1['pre_analysis_only_x_gift_only_intersection'])}; hai nhóm nằm hai phía lower-bound nên rời nhau.

## Bộ lọc pipeline scoring chính

- status 3, ID không NULL, local_date trong [analysis_start,T), rồi giữ khách nếu có ít nhất một đơn không quà. COUNT DISTINCT trực tiếp cho thấy 5 khách B chỉ có đơn quà; còn 5.169.
- exclude_adjusted không bật trong cohort chính (chỉ dùng ở độ nhạy B); không loại thêm khách.
- Có dòng hàng không phải điều kiện tạo customer set; không loại khách thiếu item lines khỏi cohort scoring.
- Có {_fmt(t1['status3_dev_missing_customer_id_orders'])} đơn status 3 DEV thiếu ID; đây là số đơn, không phải khách distinct. Số đơn quà status 3 DEV: {_fmt(t1['status3_dev_gift_orders'])}.

## Kiểm tra cấu trúc DuckDB (không phải phát hiện hành vi)

- Đơn DEV: {_fmt(db['dev_orders'])}; status 3: {_fmt(db['dev_status3_orders'])}; status khác 3: {_fmt(db['dev_other_status_orders'])}.
- Customer key NULL: status khác 3 {_fmt(db['other_status_null_customer_orders'])} đơn; status 3 {_fmt(db['status3_null_customer_orders'])} đơn. Đây là kiểm kê cấu trúc kho. Có: builder chỉ tạo `customer_key` trong nhánh `status == 3`; đơn status khác 3 được giữ `customer_key=NULL` (xem `scripts/build_dev_warehouse.py`).
- Khách có status khác 3 trong kho: {_fmt(db['dev_customers_other_status'])}; giao khách status 3/status khác 3: {_fmt(db['dev_customers_status3_other_status_intersection'])}. Các số 0 là kiểm tra cấu trúc kho, không phải phát hiện về hành vi.

Nguồn: docs/cohort_definitions.md; outputs/tables/eligibility_preflight.csv; outputs/metrics/day2_segmentation.json; COUNT DISTINCT read-only trong scripts/build_pretest_evidence.py; chính sách cohort ở scripts/prepare_day2.py và src/features/day2_data.py.
"""
    (ROOT / "docs/cohort_reconciliation.md").write_text(report, encoding="utf-8")


def _write_unknown_report(data: dict[str, Any]) -> None:
    t2 = data["t2"]
    groups = t2["source_channel_group_distributions"]
    rows = []
    for field, details in groups.items():
        nonempty = "<5 (gộp/ẩn)" if details["nonempty_orders"] is None else _fmt(details["nonempty_orders"])
        missing = "<5 (gộp/ẩn)" if details["missing_orders"] is None else _fmt(details["missing_orders"])
        rows.append(f"| {field} | {nonempty} | {missing} |")
    grouped = []
    for field, details in groups.items():
        for row in details["groups"]:
            count = "<5 (gộp/ẩn)" if row["suppressed"] else _fmt(row["orders"])
            share = "ẩn" if row["suppressed"] else f"{row.get('revenue_share_percent', 0):.2f}%"
            grouped.append(f"| {field} | {row['group']} | {count} | {share} |")
    cross = []
    for field, details in groups.items():
        for row in details["province_missing_intersection"]:
            n = "<5 (gộp/ẩn)" if row["suppressed"] else _fmt(row["orders"])
            share = "ẩn" if row["suppressed"] else f"{row.get('revenue_share_percent', 0):.2f}%"
            cross.append(f"| {field} | {row['province']} | {row['source_group']} | {n} | {share} |")
    field_names = ", ".join(t2["source_address_field_names_present"])
    report = f"""# Chẩn đoán UNKNOWN theo tỉnh và nguồn (DEV only)

Phạm vi: đơn status 3 có local_date trong [2024-04-01, 2025-10-22), n={_fmt(t2['status3_dev_orders'])}. Đã dùng local_day, canonical_province, normalize_product_name và assess_order_money của dự án. Không in địa chỉ, giá trị nguồn/kênh, ID hay văn bản tự do; nhóm kênh được đặt nhãn số. Mọi ô dưới 5 được gộp/ẩn.

## Trường có mặt trong các đơn status 3 trước T

Tên trường/path được thấy: {field_names}.

Trường tỉnh dùng bởi pipeline là shipping_address.province_name. UNKNOWN trong feature mapping là province rỗng sau canonical_province; kết quả này mô tả đúng thiếu trường, không suy ra nguyên nhân nghiệp vụ.

| Trường nguồn/kênh | Giá trị không rỗng (đơn) | Thiếu/rỗng (đơn) |
|---|---:|---:|
{chr(10).join(rows)}

## Tỷ lệ rỗng tỉnh/thành và doanh thu ghi nhận

- Đơn status 3 thiếu province_name: {_fmt(t2['province_missing_orders'])}/{_fmt(t2['status3_dev_orders'])} = {t2['province_missing_rate_percent']:.2f}%.
- Tổng doanh thu ghi nhận DEV tính được: {_fmt(t2['revenue_recognized_total_vnd'])} VND qua {_fmt(t2['revenue_recognized_orders'])} đơn; thiếu số tiền ghi nhận ở {_fmt(t2['revenue_missing_orders'])} đơn.
- Doanh thu nhóm thiếu province_name: {_fmt(t2['missing_province_revenue_vnd'])} VND = {t2['missing_province_revenue_share_percent']:.2f}% doanh thu DEV.
- Tỷ lệ 91,92% trong dashboard là phạm vi DEV+test. Số ở đây chỉ DEV, khác phạm vi và mẫu số; không coi là mâu thuẫn.

## Doanh thu theo nhóm nguồn/kênh (nhãn nhóm đã ẩn)

| Trường | Nhóm | Đơn | Tỷ trọng doanh thu DEV |
|---|---|---:|---:|
{chr(10).join(grouped)}

## Giao ô tỉnh rỗng × nguồn/kênh

| Trường nguồn/kênh | Tỉnh/thành | Nhóm ẩn danh | Đơn | Tỷ trọng doanh thu DEV |
|---|---|---|---:|---:|
{chr(10).join(cross)}

Kết luận: [Chắc chắn] UNKNOWN tương ứng trường tỉnh/thành rỗng theo mapping hiện hành; trong DEV tỷ lệ đơn thiếu tỉnh là {t2['province_missing_rate_percent']:.2f}% và doanh thu ghi nhận của nhóm này chiếm {t2['missing_province_revenue_share_percent']:.2f}%. [Chắc chắn] Các trường nguồn/kênh hiện diện được tổng hợp theo nhóm ẩn danh ở trên. Chưa kết luận nguồn/kênh nào gây thiếu tỉnh hoặc vì sao; không suy diễn nguyên nhân kinh doanh.
"""
    (ROOT / "docs/unknown_region_diagnostic.md").write_text(report, encoding="utf-8")


def main() -> int:
    data, revenue_expression = _scan_snapshot()
    data["t2"]["revenue_expression"] = revenue_expression
    (ROOT / "outputs/tables/cohort_bridge_verified.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    _write_cohort_report(data)
    _write_unknown_report(data)
    print(
        "Pre-T aggregate evidence: "
        f"A={data['t1']['A_all_status3_before_T']}, "
        f"B={data['t1']['B_status3_in_DEV']}, "
        f"pre-only={data['t1']['A_minus_B_only_pre_analysis']}, "
        f"gift-only={data['t1']['B_customers_with_only_gift_status3_orders']}, "
        f"scoring={data['t1']['B_after_non_gift_customer_filter']}; "
        f"province-empty DEV share={data['t2']['province_missing_rate_percent']:.2f}% orders / "
        f"{data['t2']['missing_province_revenue_share_percent']:.2f}% revenue."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
