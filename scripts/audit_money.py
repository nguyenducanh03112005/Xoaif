"""Audit amendment-03 money rules on status-3 development orders only."""

from __future__ import annotations

import csv
from datetime import date, datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sys
from typing import Any
from zoneinfo import ZoneInfo

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from features.money import assess_order_money, decimal_value
from ingest.analysis_amendment import load_analysis_amendment
from ingest.decision_amendment import load_money_adjustment_amendment
from ingest.identifiers import pseudonymize_id
from ingest.settings import load_analytics_hmac_key

RAW_ROOT = ROOT / "data" / "raw" / "pancake_orders"
LOCAL_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
ZERO = Decimal(0)


def local_day(value: Any) -> date | None:
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
    return parsed.astimezone(LOCAL_TZ).date()


def safe_status(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def dec(value: Decimal | None) -> str | None:
    return str(value) if value is not None else None


def rate(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def _rank(values: list[Decimal]) -> list[float]:
    """Average ranks for ties, sufficient for a Spearman calculation."""
    ordered = sorted(enumerate(values), key=lambda pair: pair[1])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(ordered):
        j = i + 1
        while j < len(ordered) and ordered[j][1] == ordered[i][1]:
            j += 1
        average_rank = (i + 1 + j) / 2
        for k in range(i, j):
            ranks[ordered[k][0]] = average_rank
        i = j
    return ranks


def spearman(left: list[Decimal], right: list[Decimal]) -> float | None:
    if len(left) < 2 or len(right) != len(left):
        return None
    a = _rank(left)
    b = _rank(right)
    mean_a = sum(a) / len(a)
    mean_b = sum(b) / len(b)
    numerator = sum((x - mean_a) * (y - mean_b) for x, y in zip(a, b))
    denom_a = sum((x - mean_a) ** 2 for x in a) ** 0.5
    denom_b = sum((y - mean_b) ** 2 for y in b) ** 0.5
    return numerator / (denom_a * denom_b) if denom_a and denom_b else None


def load_development_orders() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    split = yaml.safe_load((ROOT / "config" / "split.yaml").read_bytes())
    amendment_01, _, _ = load_analysis_amendment(ROOT)
    amendment_03, amendment_hash = load_money_adjustment_amendment(ROOT)
    analysis_start = date.fromisoformat(str(amendment_01["analysis_start"]))
    test_start = date.fromisoformat(str(split["test_start"]))
    snapshot_id = str(split["snapshot_id"])
    snapshot_root = (RAW_ROOT / snapshot_id).resolve()
    manifest_path = snapshot_root / "manifest.json"
    manifest_bytes = manifest_path.read_bytes()
    manifest_hash = hashlib.sha256(manifest_bytes).hexdigest()
    if manifest_hash != split.get("snapshot_manifest_sha256"):
        raise ValueError("snapshot manifest hash differs from locked config")
    manifest = json.loads(manifest_bytes)
    hmac_key = load_analytics_hmac_key(ROOT / "xoaif.env")
    orders: list[dict[str, Any]] = []
    source_rows_seen = 0
    for page_no, page_record in enumerate(manifest["pages"], start=1):
        page_path = (snapshot_root / page_record["file"]).resolve()
        if not page_path.is_relative_to(snapshot_root):
            raise ValueError("snapshot page path escaped its directory")
        page_bytes = page_path.read_bytes()
        if hashlib.sha256(page_bytes).hexdigest() != page_record.get("sha256"):
            raise ValueError("snapshot page checksum mismatch")
        payload = json.loads(page_bytes)
        rows = payload.get("data", [])
        if payload.get("page_number") != page_no or len(rows) != page_record.get("rows"):
            raise ValueError("snapshot page metadata or row count mismatch")
        for source_order in rows:
            source_rows_seen += 1
            if not isinstance(source_order, dict):
                continue
            # For the reserved interval, read inserted_at only; skip before status or any other field.
            day = local_day(source_order.get("inserted_at"))
            if day is None or day >= test_start or day < analysis_start:
                continue
            if safe_status(source_order.get("status")) != 3:
                continue
            assessment = assess_order_money(source_order)
            customer = source_order.get("customer")
            customer_id = customer.get("customer_id") if isinstance(customer, dict) else None
            customer_key = None
            if customer_id is not None and str(customer_id).strip():
                customer_key = pseudonymize_id(customer_id, key=hmac_key, namespace="xoaif/customer/v1")
            orders.append({
                "month": day.strftime("%Y-%m"),
                "customer_key": customer_key,
                "assessment": assessment,
            })
    if source_rows_seen != manifest.get("row_count"):
        raise ValueError("source snapshot row reconciliation failed")
    meta = {
        "snapshot_id": snapshot_id,
        "manifest_sha256": manifest_hash,
        "amendment_03_sha256": amendment_hash,
        "analysis_start": analysis_start.isoformat(),
        "test_start_exclusive": test_start.isoformat(),
        "test_labels_loaded": False,
        "test_behavior_loaded": False,
        "amendment_03_pre_label_access_audit_clean": amendment_03["pre_label_access_audit"]["label_load_entries"] == 0
            and amendment_03["pre_label_access_audit"]["test_behavior_load_entries"] == 0,
    }
    return orders, meta


def diagnose() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    orders, meta = load_development_orders()
    total = len(orders)
    # Keep zero-count relationship classes in the audit so every requested
    # exact pattern and residual family is visible in JSON/CSV/report output.
    pattern_names = (
        "missing_fields",
        "after_equals_total_minus_discount_plus_shipping",
        "after_equals_total_minus_discount_ship_not_added",
        "after_equals_total_plus_shipping_discount_not_subtracted",
        "after_equals_total",
        "residual_plus_shipping",
        "residual_minus_shipping",
        "residual_plus_discount",
        "residual_minus_discount",
        "other_distance_le_10000",
        "other_distance_10001_50000",
        "other_distance_50001_100000",
        "other_distance_gt_100000",
    )
    pattern_counts: dict[str, int] = dict.fromkeys(pattern_names, 0)
    adjustment_values: list[Decimal] = []
    recognized_total = ZERO
    a_total = ZERO
    non_gift_count = 0
    missing_money = 0
    gifts = 0
    negative = 0
    zero_total_positive_after = 0
    unexplained = 0
    identity_comparable = 0
    identity_matches = 0
    retail_comparable = 0
    retail_matches = 0
    negative_causes: dict[str, int] = {}
    customer_primary: dict[str, Decimal] = {}
    customer_a: dict[str, Decimal] = {}
    monthly: dict[str, dict[str, int]] = {}
    sensitivity_b_removed = 0
    sensitivity_b_removed_all = 0
    sensitivity_b_retained_non_gift = 0
    sensitivity_b_revenue = ZERO

    for row in orders:
        assessment = row["assessment"]
        month = row["month"]
        pattern_counts[assessment.after_pattern] = pattern_counts.get(assessment.after_pattern, 0) + 1
        m = monthly.setdefault(month, {"orders": 0, "gifts": 0, "adjusted": 0, "unexplained": 0, "negative": 0})
        m["orders"] += 1
        if not assessment.money_fields_usable:
            missing_money += 1
        if assessment.identity_matches is not None:
            identity_comparable += 1
            identity_matches += int(assessment.identity_matches)
        if assessment.retail_line_matches_total is not None:
            retail_comparable += 1
            retail_matches += int(assessment.retail_line_matches_total)
        if assessment.total_zero_after_positive:
            zero_total_positive_after += 1
        if assessment.is_gift:
            gifts += 1
            m["gifts"] += 1
        if assessment.adj_unexplained:
            unexplained += 1
            m["unexplained"] += 1
        if assessment.negative_revenue:
            negative += 1
            m["negative"] += 1
            # Cause categories are descriptive and can overlap; no payment fields are inspected.
            for cause in assessment.negative_revenue_causes:
                negative_causes[cause] = negative_causes.get(cause, 0) + 1

        adjustment = assessment.price_adjustment
        excluded_b = (adjustment is not None and adjustment != ZERO) or assessment.adj_unexplained
        if excluded_b:
            sensitivity_b_removed_all += 1
        if assessment.is_gift:
            continue
        non_gift_count += 1
        revenue = assessment.revenue_recognized
        base = assessment.revenue_A
        if revenue is not None:
            recognized_total += revenue
        if base is not None:
            a_total += base
        if adjustment is not None:
            adjustment_values.append(adjustment)
            if adjustment != ZERO:
                m["adjusted"] += 1
        customer_key = row["customer_key"]
        if customer_key and assessment.monetary_contribution is not None and assessment.monetary_A_contribution is not None:
            customer_primary[customer_key] = customer_primary.get(customer_key, ZERO) + assessment.monetary_contribution
            customer_a[customer_key] = customer_a.get(customer_key, ZERO) + assessment.monetary_A_contribution
        if excluded_b:
            sensitivity_b_removed += 1
        else:
            sensitivity_b_retained_non_gift += 1
            if revenue is not None:
                sensitivity_b_revenue += revenue
    status3_count = len(orders)
    # Order-level sensitivity comparison excludes gifts, consistent with the gift rule.
    difference_orders = 0
    for row in orders:
        assessment = row["assessment"]
        if assessment.is_gift or assessment.revenue_recognized is None or assessment.revenue_A is None:
            continue
        difference = abs(assessment.revenue_recognized - assessment.revenue_A)
        threshold = Decimal("0.01") * abs(assessment.revenue_A)
        if (assessment.revenue_A == ZERO and difference != ZERO) or (assessment.revenue_A != ZERO and difference > threshold):
            difference_orders += 1

    customer_keys = sorted(set(customer_primary) & set(customer_a))
    primary_values = [customer_primary[key] for key in customer_keys]
    a_values = [customer_a[key] for key in customer_keys]
    rho = spearman(primary_values, a_values)
    nonzero_count = sum(value != ZERO for value in adjustment_values)
    positive = [value for value in adjustment_values if value > ZERO]
    negative_adj = [value for value in adjustment_values if value < ZERO]
    sorted_adjustments = sorted(adjustment_values)

    def quantile(p: float) -> Decimal | None:
        if not sorted_adjustments:
            return None
        position = (len(sorted_adjustments) - 1) * p
        low = int(position)
        high = min(low + 1, len(sorted_adjustments) - 1)
        fraction = Decimal(str(position - low))
        return sorted_adjustments[low] + (sorted_adjustments[high] - sorted_adjustments[low]) * fraction

    positive_sum = sum(positive, ZERO)
    negative_sum = sum(negative_adj, ZERO)
    adjustment_net = positive_sum + negative_sum
    total_difference = recognized_total - a_total
    comparison = {
        "non_gift_orders_compared": non_gift_count,
        "revenue_recognized_total": dec(recognized_total),
        "revenue_A_total": dec(a_total),
        "difference_primary_minus_A": dec(total_difference),
        "difference_percent_of_abs_A": float(total_difference / abs(a_total) * 100) if a_total != ZERO else None,
        "orders_different_by_more_than_1_percent": difference_orders,
        "orders_different_by_more_than_1_percent_rate": rate(difference_orders, non_gift_count),
        "customer_monetary_spearman": rho,
        "customer_count_compared": len(customer_keys),
    }
    gate_threshold = 0.01
    negative_share = rate(negative, status3_count) or 0.0
    stop = negative_share > gate_threshold
    adjustment_summary = {
        "eligible_non_gift_orders_with_adjustment": len(adjustment_values),
        "zero_count": len(adjustment_values) - nonzero_count,
        "zero_rate": rate(len(adjustment_values) - nonzero_count, len(adjustment_values)),
        "positive_count": len(positive),
        "positive_rate": rate(len(positive), len(adjustment_values)),
        "negative_count": len(negative_adj),
        "negative_rate": rate(len(negative_adj), len(adjustment_values)),
        "quantiles": {f"p{int(p*100):02d}": dec(quantile(p)) for p in (0, .25, .5, .75, .9, .95, .99, 1)},
        "positive_sum": dec(positive_sum),
        "negative_sum_signed": dec(negative_sum),
        "net_sum": dec(adjustment_net),
        "positive_sum_as_percent_of_recognized_revenue": float(positive_sum / recognized_total * 100) if recognized_total else None,
        "negative_sum_as_percent_of_recognized_revenue": float(negative_sum / recognized_total * 100) if recognized_total else None,
        "net_sum_as_percent_of_recognized_revenue": float(adjustment_net / recognized_total * 100) if recognized_total else None,
    }
    monthly_summary = {}
    for month, values in sorted(monthly.items()):
        monthly_summary[month] = {
            **values,
            "adjustment_rate_non_gift": rate(values["adjusted"], values["orders"] - values["gifts"]),
            "unexplained_rate": rate(values["unexplained"], values["orders"]),
            "negative_rate": rate(values["negative"], values["orders"]),
        }
    month_order = sorted(monthly_summary)
    first_months = month_order[:5]
    first_month_rate = float(sum(monthly_summary[m]["adjustment_rate_non_gift"] or 0.0 for m in first_months) / len(first_months)) if first_months else None
    peak_month = max(month_order, key=lambda month: monthly_summary[month]["adjustment_rate_non_gift"] or 0.0) if month_order else None
    monthly_concentration = {
        "first_five_months": first_months,
        "first_five_months_mean_adjustment_rate": first_month_rate,
        "peak_month": peak_month,
        "peak_adjustment_rate": monthly_summary[peak_month]["adjustment_rate_non_gift"] if peak_month else None,
        "interpretation": "adjustment rates do not peak in the opening months" if peak_month and peak_month not in first_months else "peak includes an opening month",
    }
    metrics = {
        **meta,
        "scope": {"status": 3, "status3_orders": status3_count, "denominator_for_negative_gate": "all status-3 orders in effective development"},
        "money_fields_usable_orders": status3_count - missing_money,
        "money_fields_missing_orders": missing_money,
        "after_pattern_counts": dict(sorted(pattern_counts.items())),
        "identity": {"comparable_orders": identity_comparable, "matches": identity_matches, "match_rate": rate(identity_matches, identity_comparable)},
        "retail_line_reconciliation": {"comparable_orders": retail_comparable, "matches": retail_matches, "match_rate": rate(retail_matches, retail_comparable), "formula": "sum(items.variation_info.retail_price * items.quantity) = total_price"},
        "gifts": {"count": gifts, "rate": rate(gifts, status3_count)},
        "negative_revenue": {"count": negative, "rate": negative_share, "causes_by_after_pattern": dict(sorted(negative_causes.items())), "stop_threshold": gate_threshold, "stop": stop},
        "adj_unexplained": {"count": unexplained, "rate": rate(unexplained, status3_count)},
        "total_price_zero_after_positive_count": zero_total_positive_after,
        "price_adjustment": adjustment_summary,
        "monthly": monthly_summary,
        "monthly_concentration": monthly_concentration,
        "revenue_comparison": comparison,
        "sensitivity_B_exclude_adjusted_or_unexplained": {
            "excluded_status3_orders_including_gifts": sensitivity_b_removed_all,
            "excluded_non_gift_orders": sensitivity_b_removed,
            "retained_non_gift_orders": sensitivity_b_retained_non_gift,
            "recognized_revenue_total": dec(sensitivity_b_revenue),
        },
        "stop_gate_failed": stop,
        "test_labels_loaded": False,
        "test_behavior_loaded": False,
    }
    csv_rows: list[dict[str, Any]] = []
    for pattern, count in sorted(pattern_counts.items()):
        csv_rows.append({"section": "after_pattern", "period": "all", "category": pattern, "orders": count, "denominator": status3_count, "rate": rate(count, status3_count), "value": "", "unit": "count"})
    for section, category, count, denominator in (
        ("money_flag", "is_gift", gifts, status3_count),
        ("money_flag", "negative_revenue", negative, status3_count),
        ("money_flag", "adj_unexplained", unexplained, status3_count),
        ("money_flag", "total_price_zero_after_positive", zero_total_positive_after, status3_count),
        ("price_adjustment_rate", "zero", len(adjustment_values) - nonzero_count, len(adjustment_values)),
        ("price_adjustment_rate", "positive", len(positive), len(adjustment_values)),
        ("price_adjustment_rate", "negative", len(negative_adj), len(adjustment_values)),
        ("revenue_comparison", "orders_diff_over_1_percent", difference_orders, non_gift_count),
    ):
        csv_rows.append({"section": section, "period": "all", "category": category, "orders": count, "denominator": denominator, "rate": rate(count, denominator), "value": "", "unit": "rate"})
    csv_rows.append({"section": "revenue_comparison", "period": "all", "category": "customer_monetary_spearman", "orders": len(customer_keys), "denominator": len(customer_keys), "rate": "", "value": rho if rho is not None else "", "unit": "correlation"})
    csv_rows.append({"section": "sensitivity_B", "period": "all", "category": "retained_non_gift_orders", "orders": sensitivity_b_retained_non_gift, "denominator": non_gift_count, "rate": rate(sensitivity_b_retained_non_gift, non_gift_count), "value": str(sensitivity_b_revenue), "unit": "count_and_vnd"})
    for month, values in sorted(monthly_summary.items()):
        for metric_name, count_key, den_key in (
            ("adjustment_rate", "adjusted", "orders"),
            ("adj_unexplained_rate", "unexplained", "orders"),
            ("negative_revenue_rate", "negative", "orders"),
        ):
            denom = values[den_key] - values["gifts"] if metric_name == "adjustment_rate" else values[den_key]
            count = values[count_key]
            csv_rows.append({"section": "monthly", "period": month, "category": metric_name, "orders": count, "denominator": denom, "rate": rate(count, denom), "value": "", "unit": "rate"})
    for q, value in adjustment_summary["quantiles"].items():
        csv_rows.append({"section": "price_adjustment_quantile", "period": "all", "category": q, "orders": "", "denominator": len(adjustment_values), "rate": "", "value": value or "", "unit": "VND"})
    for name, value in (("positive_sum", positive_sum), ("negative_sum_signed", negative_sum), ("net_sum", adjustment_net), ("revenue_recognized_total", recognized_total), ("revenue_A_total", a_total)):
        csv_rows.append({"section": "money_total", "period": "all", "category": name, "orders": "", "denominator": non_gift_count, "rate": "", "value": str(value), "unit": "VND"})
    return metrics, csv_rows


def write_outputs(metrics: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    write_json(ROOT / "outputs" / "metrics" / "day2_money_audit.json", metrics)
    path = ROOT / "outputs" / "tables" / "money_diagnosis.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=["section", "period", "category", "orders", "denominator", "rate", "value", "unit"])
        writer.writeheader()
        writer.writerows(rows)


def write_report(metrics: dict[str, Any]) -> None:
    patterns = metrics["after_pattern_counts"]
    adj = metrics["price_adjustment"]
    comparison = metrics["revenue_comparison"]
    gifts = metrics["gifts"]
    neg = metrics["negative_revenue"]
    total_orders = metrics["scope"]["status3_orders"]
    identity = metrics["identity"]
    retail = metrics["retail_line_reconciliation"]
    pattern_labels = {
        "missing_fields": "Thiếu trường tiền",
        "after_equals_total_minus_discount_plus_shipping": "Khớp `total - discount + shipping`",
        "after_equals_total_minus_discount_ship_not_added": "`after = total - discount` (chưa cộng ship; ngoại lệ đã duyệt)",
        "after_equals_total_plus_shipping_discount_not_subtracted": "`after = total + shipping` (chưa trừ discount)",
        "after_equals_total": "`after = total`",
        "residual_plus_shipping": "Lệch dư `+shipping` so với công thức chuẩn",
        "residual_minus_shipping": "Lệch dư `-shipping` so với công thức chuẩn",
        "residual_plus_discount": "Lệch dư `+discount` so với công thức chuẩn",
        "residual_minus_discount": "Lệch dư `-discount` so với công thức chuẩn",
        "other_distance_le_10000": "Lệch khác, khoảng cách ≤ 10.000 VND",
        "other_distance_10001_50000": "Lệch khác, khoảng cách 10.001–50.000 VND",
        "other_distance_50001_100000": "Lệch khác, khoảng cách 50.001–100.000 VND",
        "other_distance_gt_100000": "Lệch khác, khoảng cách > 100.000 VND",
    }
    pattern_lines = "\n".join(
        f"- {label}: {patterns.get(key, 0):,} ({(patterns.get(key, 0) / total_orders if total_orders else 0):.2%})."
        for key, label in pattern_labels.items()
    )
    month_lines = "\n".join(
        f"- {month}: điều chỉnh khác 0 {item['adjustment_rate_non_gift'] or 0:.2%}; chưa giải thích {item['unexplained_rate'] or 0:.2%}; doanh thu âm {item['negative_rate'] or 0:.2%}."
        for month, item in metrics["monthly"].items()
    )
    concentration = metrics["monthly_concentration"]
    concentration_line = (
        f"Tỷ lệ điều chỉnh bình quân 5 tháng đầu ({', '.join(concentration['first_five_months'])}) là "
        f"{concentration['first_five_months_mean_adjustment_rate'] or 0:.2%}; đỉnh ở {concentration['peak_month']} "
        f"({concentration['peak_adjustment_rate'] or 0:.2%}). "
        f"{'Tỷ lệ điều chỉnh không đạt đỉnh ở giai đoạn mở đầu' if concentration['peak_month'] and concentration['peak_month'] not in concentration['first_five_months'] else 'Đỉnh có nằm trong giai đoạn mở đầu'} theo nhóm tháng này."
    )
    gate = (
        f"DỪNG theo quy tắc duy nhất: {neg['count']}/{total_orders} đơn âm ({neg['rate']:.2%}) vượt 1%."
        if metrics["stop_gate_failed"]
        else f"ĐẠT: {neg['count']}/{total_orders} đơn âm ({neg['rate']:.2%}), không vượt ngưỡng 1%; có thể tiếp tục Ngày 2."
    )
    report = f'''# Kiểm toán tiền theo amendment 03

Phạm vi: status 3 trong `[{metrics['analysis_start']},{metrics['test_start_exclusive']})`, giờ `Asia/Ho_Chi_Minh`; {total_orders:,} đơn. Số liệu lấy từ `outputs/metrics/day2_money_audit.json`; bảng tổng hợp không định danh là `outputs/tables/money_diagnosis.csv`. Không có mã đơn/PII; nhãn và hành vi test chưa được nạp.

## Cách diễn giải

Status 3 được chủ cửa hàng xác nhận là doanh thu đã nhận/ghi nhận. Bằng chứng gồm rà soát mẫu 13 đơn và xác nhận bằng lời; `dash_*` vẫn trống, nên không trình bày như đối soát dashboard chi tiết. Trường thanh toán app không làm bộ lọc hay bằng chứng thu tiền. Amendment 03 thay quy tắc sau khi cổng cũ ghi nhận 701/6.400 (10,95%) vượt 5%; lý do là kiến thức nghiệp vụ rằng chênh lệch có thể là phí/ưu đãi, không dựa trên nhãn/hành vi test. Cổng 5% đã bị thay thế.

Doanh thu chính là `after_sub_discount - shipping_fee`, ngoại lệ dùng `after` khi `after == total_price-total_discount` và ship dương. `price_adjustment = revenue_recognized - (total_price-total_discount)`. Điều chỉnh được giữ; `adj_unexplained` chỉ đánh dấu mẫu khác các quan hệ chính xác đã ghi trong amendment 03.

## Quan hệ trường tiền

- Khớp `after = total-discount+shipping`: {identity['matches']}/{identity['comparable_orders']} ({identity['match_rate'] or 0:.2%}).
- Khớp `total_price = Σ retail_price × quantity`: {retail['matches']}/{retail['comparable_orders']} ({retail['match_rate'] or 0:.2%}); chỉ tính đơn có đủ dòng hàng.
- Đếm theo từng mẫu `after` (các nhóm loại trừ lẫn nhau):
{pattern_lines}

## Điều chỉnh và ngoại lệ

- Đơn không tặng có điều chỉnh xác định: {adj['eligible_non_gift_orders_with_adjustment']:,}; bằng 0: {adj['zero_count']:,} ({adj['zero_rate'] or 0:.2%}); dương: {adj['positive_count']:,} ({adj['positive_rate'] or 0:.2%}); âm: {adj['negative_count']:,} ({adj['negative_rate'] or 0:.2%}).
- Phân vị price_adjustment (VND): `{json.dumps(adj['quantiles'], ensure_ascii=False)}`.
- Tổng điều chỉnh dương: {adj['positive_sum']} VND ({adj['positive_sum_as_percent_of_recognized_revenue'] or 0:.2f}% doanh thu ghi nhận); tổng điều chỉnh âm có dấu: {adj['negative_sum_signed']} VND ({adj['negative_sum_as_percent_of_recognized_revenue'] or 0:.2f}%); ròng {adj['net_sum']} VND ({adj['net_sum_as_percent_of_recognized_revenue'] or 0:.2f}%).
- Đơn tặng: {gifts['count']:,} ({gifts['rate'] or 0:.2%}); doanh thu âm: {neg['count']:,} ({neg['rate']:.2%}), phân nhóm nguyên nhân theo mẫu trường tiền `{json.dumps(neg['causes_by_after_pattern'], ensure_ascii=False)}`; `adj_unexplained`: {metrics['adj_unexplained']['count']:,}; `total_price=0` và `after>0`: {metrics['total_price_zero_after_positive_count']:,}.
- Tỷ lệ theo tháng:
{month_lines}
- So sánh đầu kỳ và đỉnh: {concentration_line}

## So sánh độ nhạy A

A dùng `total_price-total_discount`; so sánh loại quà. Doanh thu ghi nhận chính là {comparison['revenue_recognized_total']} VND; A là {comparison['revenue_A_total']} VND; chênh chính trừ A là {comparison['difference_primary_minus_A']} VND ({comparison['difference_percent_of_abs_A'] if comparison['difference_percent_of_abs_A'] is not None else 'không xác định'}% theo trị tuyệt đối A). {comparison['orders_different_by_more_than_1_percent']}/{comparison['non_gift_orders_compared']} đơn khác trên 1% ({comparison['orders_different_by_more_than_1_percent_rate'] or 0:.2%}). Spearman Monetary theo {comparison['customer_count_compared']:,} khách ghép được là {comparison['customer_monetary_spearman'] if comparison['customer_monetary_spearman'] is not None else 'không xác định'}; Monetary đặt đóng góp từng đơn âm bằng 0.

## Độ nhạy B và cổng

Độ nhạy B loại hợp đơn có `price_adjustment != 0` hoặc `adj_unexplained`: giữ {metrics['sensitivity_B_exclude_adjusted_or_unexplained']['retained_non_gift_orders']:,} đơn không quà; doanh thu ghi nhận tổng của các đơn còn lại là {metrics['sensitivity_B_exclude_adjusted_or_unexplained']['recognized_revenue_total']} VND. Các phân tích khách hàng sẽ chạy lại trên cùng mốc thời gian/chia khách.

**Cổng tiền:** {gate}

Giới hạn: chỉ có status hiện tại; không dùng `status_history`, nên không thể khôi phục trạng thái tại `T+N+L`. Đây là doanh thu ghi nhận theo quy tắc nghiệp vụ, không phải lợi nhuận hay đối soát kế toán.
'''
    (ROOT / "docs" / "money_audit.md").write_text(report, encoding="utf-8")


def main() -> int:
    try:
        metrics, rows = diagnose()
        write_outputs(metrics, rows)
        write_report(metrics)
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError, yaml.YAMLError) as exc:
        print(f"Money audit stopped ({type(exc).__name__}); no order IDs or monetary rows were printed.")
        return 2
    gate = "FAILED" if metrics["stop_gate_failed"] else "PASSED"
    print(
        f"Amendment-03 money audit: status3={metrics['scope']['status3_orders']}, gifts={metrics['gifts']['count']}, "
        f"negative_revenue={metrics['negative_revenue']['count']} ({metrics['negative_revenue']['rate']:.2%}); gate={gate}."
    )
    return 3 if metrics["stop_gate_failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
