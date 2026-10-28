"""Offline Day 3 dashboard built only from checked aggregate outputs."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st
import yaml

ROOT = Path(__file__).resolve().parents[2]
TABLES = ROOT / "outputs" / "tables"
METRICS = ROOT / "outputs" / "metrics"


@st.cache_data(show_spinner=False)
def read_csv(name: str) -> pd.DataFrame:
    path = TABLES / name
    if not path.is_file():
        raise FileNotFoundError(name)
    return pd.read_csv(path)


@st.cache_data(show_spinner=False)
def read_json(name: str) -> dict[str, Any]:
    path = METRICS / name
    if not path.is_file():
        raise FileNotFoundError(name)
    return json.loads(path.read_text(encoding="utf-8"))


def money(value: float) -> str:
    return f"{value:,.0f} đ".replace(",", ".")


def pct(value: float) -> str:
    return f"{value:.1%}".replace(".", ",", 1)


def metric(value: float, digits: int = 4) -> str:
    return f"{value:.{digits}f}".replace(".", ",")


def localized_frame(frame: pd.DataFrame) -> pd.DataFrame:
    display = frame.copy()
    for column in display.columns:
        if not pd.api.types.is_numeric_dtype(display[column]) or pd.api.types.is_bool_dtype(display[column]):
            continue
        key = str(column).lower()
        if "share" in key or "rate" in key:
            display[column] = display[column].map(lambda value: pct(float(value)) if pd.notna(value) else "")
        elif any(token in key for token in ("vnd", "revenue", "monetary", "price")):
            display[column] = display[column].map(lambda value: f"{float(value):,.0f}".replace(",", ".") if pd.notna(value) else "")
        else:
            display[column] = display[column].map(
                lambda value: f"{int(value):,}".replace(",", ".") if pd.notna(value) and float(value).is_integer()
                else metric(float(value), 3) if pd.notna(value) else ""
            )
    return display


def _model_rows(dev: dict[str, Any], test: dict[str, Any]) -> pd.DataFrame:
    dev_v2 = dev["repurchase_features_v2"]["selected_oof_metrics"]
    test_rows = test["models"]
    labels = {
        "majority_baseline": "Baseline majority",
        "amendment_03_logistic_regression": "Logistic Regression C=10 — mô hình chính theo D-005",
        "repurchase_features_v2_logistic_regression": "Logistic Regression feature-v2 C=0,1 — khảo sát bổ sung theo Amendment 04; không thay mô hình chính",
    }
    rows = []
    for key, label in labels.items():
        current = test_rows[key]
        ci = test["bootstrap_95_ci"][key]["metrics_95_ci"]
        delta_ci = test["bootstrap_95_ci"]["paired_average_precision_delta_vs_baseline_95_ci"].get(key)
        baseline_ap = test_rows["majority_baseline"]["average_precision"]
        rows.append({
            "Mô hình": label,
            "P / R / F1": " / ".join(metric(current[name]) for name in ("precision", "recall", "f1")),
            "ROC-AUC (CI 95%)": (
                f"{metric(current['roc_auc'])} ({metric(ci['roc_auc']['lower'],4)}–{metric(ci['roc_auc']['upper'],4)})"
                if ci["roc_auc"] else "NA"
            ),
            "AP (CI 95%)": (
                f"{metric(current['average_precision'])} ({metric(ci['average_precision']['lower'],4)}–{metric(ci['average_precision']['upper'],4)})"
                if ci["average_precision"] else "NA"
            ),
            "ΔAP vs baseline (CI 95%)": (
                f"{current['average_precision'] - baseline_ap:+.4f} ({delta_ci['lower']:+.4f}–{delta_ci['upper']:+.4f})".replace(".", ",")
                if delta_ci else "—"
            ),
            "TN / FP / FN / TP": " / ".join(
                f"{int(x):,}".replace(",", ".") for row in current["confusion_matrix_tn_fp_fn_tp"] for x in row
            ),
        })
    return pd.DataFrame(rows)


def main() -> None:
    st.set_page_config(page_title="Xoaif Garden | Kho & Khai phá dữ liệu", layout="wide")
    st.title("Xoaif Garden · Bán hàng và khai phá dữ liệu")
    st.caption("Snapshot offline · Chỉ số tổng hợp · Không hiển thị khách hàng, đơn hàng hay thông tin liên hệ")

    refresh_enabled = st.sidebar.toggle("Cho phép làm mới bảng snapshot cục bộ", value=False)
    if st.sidebar.button("Làm mới dữ liệu cục bộ", disabled=not refresh_enabled):
        st.cache_data.clear()
        st.rerun()

    try:
        sales = read_csv("dashboard_sales_monthly.csv")
        products = read_csv("dashboard_product_orders.csv")
        statuses = read_csv("dashboard_status_counts.csv")
        segments = read_csv("test_segment_profiles.csv")
        combo_test = read_csv("test_combos_frozen.csv")
        combo_dev = read_csv("combos_v2.csv")
        seasonality = read_csv("seasonal_pair_metrics.csv")
        gift_audit = read_csv("gift_line_audit.csv")
        monthly_gifts = read_csv("gift_line_rates_monthly.csv")
        size_gifts = read_csv("gift_line_rates_order_size.csv")
        test = read_json("test_eval.json")
        dev = read_json("dev_final_models_v2.json")
        dev_primary = read_json("dev_final_model.json")
        money_audit = read_json("day2_money_audit.json")
        day3 = read_json("day3_combo_prereg.json")
        segmentation_metrics = read_json("day2_segmentation.json")
        split = yaml.safe_load((ROOT / "config" / "split.yaml").read_bytes())
        split_lock = json.loads((ROOT / "config" / "split.lock.json").read_text(encoding="utf-8"))
        snapshot_hash = split_lock.get("snapshot_manifest_sha256", "")
        snapshot_id = split.get("snapshot_id")
        if not isinstance(snapshot_id, str):
            raise ValueError("Locked snapshot ID is missing.")
        snapshot_time = datetime.strptime(snapshot_id, "%Y%m%dT%H%M%SZ")
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        st.error(f"Không đọc được bảng dashboard: {type(exc).__name__}.")
        st.stop()

    st.sidebar.markdown("**Nguồn dữ liệu đang hiển thị: snapshot khóa**")
    st.sidebar.caption(
        f"Cập nhật snapshot khóa (UTC): {snapshot_time:%Y-%m-%d %H:%M:%S} · ID {snapshot_id}"
    )
    st.sidebar.caption(
        "Dữ liệu làm mới: chưa có trong dashboard; refresh API chưa được xác minh. "
        "Nút chỉ nạp lại CSV/JSON aggregate local, không gọi API."
    )

    sales["month"] = sales["month"].astype(str)
    months = sorted(sales["month"].unique())
    start_month, end_month = st.sidebar.select_slider(
        "Khoảng tháng", options=months, value=(months[0], months[-1])
    )
    segment_schemes = sorted(segments["scheme"].dropna().unique().tolist())
    selected_scheme = st.sidebar.selectbox("Nhóm khách", segment_schemes, index=0)
    selected_segments = sorted(
        segments.loc[segments["scheme"] == selected_scheme, "segment"].astype(str).unique().tolist()
    )
    selected_segment = st.sidebar.selectbox("Phân khúc", ["Tất cả"] + selected_segments)
    product_names = sorted(products["product_name"].dropna().astype(str).unique().tolist())
    selected_product = st.sidebar.selectbox("Sản phẩm", ["Tất cả"] + product_names)

    tabs = st.tabs([
        "Tổng quan doanh số", "Phân khúc khách", "Combo gợi ý",
        "Chất lượng & kiểm toán", "Mô hình mua lại",
    ])

    with tabs[0]:
        st.subheader("Doanh thu ghi nhận và số đơn theo tháng")
        month_view = sales[sales["month"].between(start_month, end_month)].copy()
        revenue = float(month_view["recognized_revenue_vnd"].sum())
        order_count = int(month_view["orders"].sum())
        first, second, third = st.columns(3)
        first.metric("Doanh thu ghi nhận", money(revenue))
        second.metric("Đơn status 3 không tặng", f"{order_count:,}".replace(",", "."))
        third.metric("Tháng đang chọn", f"{len(month_view)}")
        monthly_chart = px.line(
            month_view, x="month", y="recognized_revenue_vnd", markers=True,
            labels={"month": "Tháng", "recognized_revenue_vnd": "Doanh thu ghi nhận (VND)"},
        )
        st.plotly_chart(monthly_chart, width="stretch")
        st.caption(f"Khoảng đang hiển thị {start_month} đến {end_month} ({len(month_view)} tháng). Dữ liệu mặc định 2024-04 đến 2026-04 gồm DEV và cửa sổ test, không phải chỉ DEV; 2026-04 chưa trọn tháng. Tổng bảng đủ 25 tháng: 9.104 đơn, 4.200.024.995 đ. Chỉ gồm status 3 và loại đơn quà cấp đơn; dữ liệu trước 04/2024 là giai đoạn bán thử.")
        st.info("Không so sánh doanh thu theo tỉnh/thành: 91,92% UNKNOWN trên phạm vi dashboard DEV+test. Riêng DEV, 91,56% đơn mua hợp lệ thiếu tỉnh và nhóm này chiếm 90,73% doanh thu; chưa xác định nguyên nhân nghiệp vụ. Bài phân loại phản hồi bị bỏ qua vì thiếu dữ liệu có nhãn.")

        st.markdown("**Sản phẩm theo số đơn**")
        prod_view = products.copy()
        if selected_product != "Tất cả":
            prod_view = prod_view[prod_view["product_name"] == selected_product]
        else:
            prod_view = prod_view.head(20)
        st.dataframe(localized_frame(prod_view), width="stretch", hide_index=True)
        st.caption(
            "Sản phẩm có dưới 10 lượt đơn được gộp thành “Khác”; không cộng order_count "
            "vì một đơn có thể chứa nhiều sản phẩm. Không phân bổ doanh thu ghi nhận xuống sản phẩm."
        )

    with tabs[1]:
        st.subheader("Phân khúc theo quy tắc nghiệp vụ và K-Means")
        proxy = segmentation_metrics["business_like_proxy"]
        p1, p2 = st.columns(2)
        p1.metric("Khách doanh nghiệp (proxy)", f"{int(proxy['customers']):,}".replace(",", "."))
        p2.metric("Ngưỡng proxy theo Monetary", money(proxy["p99_monetary"]))
        segment_view = segments[
            (segments["scheme"] == selected_scheme)
            & (segments["cohort"].isin(["development", "test_pre_T"]))
        ].copy()
        if selected_segment != "Tất cả":
            segment_view = segment_view[segment_view["segment"].astype(str) == selected_segment]
        display = segment_view.rename(columns={
            "scheme": "Phương pháp", "segment": "Nhóm", "cohort": "Tập",
            "customers": "Khách", "customer_share": "Tỷ trọng khách",
            "pre_T_recognized_revenue_vnd": "Doanh thu trước T (VND)",
            "pre_T_revenue_share": "Tỷ trọng trước T",
            "mean_recency_days": "R trung bình (ngày)", "mean_frequency": "F trung bình",
            "mean_monetary_vnd": "Monetary TB (VND)",
            "test_window_recognized_revenue_vnd": "Doanh thu test (VND)",
            "test_window_revenue_share": "Tỷ trọng doanh thu test",
        })
        st.dataframe(localized_frame(display), width="stretch", hide_index=True)
        st.info("K=2 là phân đoạn mô tả theo tần suất mua (một lần / lặp lại); chưa chứng minh đây là các nhóm có ý nghĩa kinh doanh hoặc giúp quyết định vận hành. Nhóm doanh nghiệp là proxy giá trị lớn/tần suất thấp, không phải nhận diện pháp lý. Phân phối RFM tại T dùng cùng snapshot phát triển; doanh thu test được trình bày riêng.")
        st.caption("Khoảng cách phân phối được khóa trước: TV = 0 trên cùng hồ sơ DEV tại T; F có IQR DEV bằng 0 nên Wasserstein chuẩn hóa không xác định.")

    with tabs[2]:
        st.subheader("Các cặp đã đóng băng trước khi mở test")
        view = combo_test.merge(
            combo_dev[["combo_name", "combined_nonzero_listed_price_vnd", "seasonal_label", "stable_cells"]],
            on="combo_name", how="left", validate="one_to_one",
        )
        view = view.merge(
            seasonality[["product_a", "product_b", "overlap_month_count", "overlap_support"]],
            on=["product_a", "product_b"], how="left", validate="one_to_one",
        )
        view = view.rename(columns={
            "support": "Support test", "confidence_a_to_b": "Confidence A→B test",
            "confidence_b_to_a": "Confidence B→A test", "lift": "Lift test",
            "dev_support": "Support dev", "dev_lift": "Lift dev",
            "combined_nonzero_listed_price_vnd": "Giá niêm yết gộp (VND)",
            "test_lift_gt_1": "Lift test > 1", "seasonal_label": "Nhãn mô tả theo lịch lễ",
            "stable_cells": "Cấu hình ổn định / 6",
            "overlap_month_count": "Tháng chồng lấp",
            "overlap_support": "Support trong khoảng chồng lấp",
        })
        columns = [c for c in [
            "combo_name", "Support dev", "Support test", "Confidence A→B test",
            "Confidence B→A test", "Lift dev", "Lift test",
            "Giá niêm yết gộp (VND)", "Tháng chồng lấp",
            "Support trong khoảng chồng lấp", "Nhãn mô tả theo lịch lễ", "Cấu hình ổn định / 6",
        ] if c in view.columns]
        st.dataframe(localized_frame(view[columns]), width="stretch", hide_index=True)
        st.caption("Luật chỉ nói các sản phẩm đồng xuất hiện trong cùng giỏ. Giá gộp là giá niêm yết quan sát được; không có giá vốn hay phân bổ giảm giá.")

    with tabs[3]:
        st.subheader("Chất lượng dữ liệu và kiểm toán")
        st.markdown("**Số đơn theo trạng thái hiện tại**")
        st.dataframe(localized_frame(statuses), width="stretch", hide_index=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("Status 3 DEV", f"{money_audit['scope']['status3_orders']:,}".replace(",", "."))
        c2.metric("Đơn quà cấp đơn", f"{money_audit['gifts']['count']:,}".replace(",", "."))
        c3.metric("Đơn âm", f"{money_audit['negative_revenue']['count']:,}".replace(",", "."))
        st.markdown("**Kiểm toán dòng quà tặng DEV**")
        st.dataframe(localized_frame(gift_audit), width="stretch", hide_index=True)
        st.caption("903 dòng inferred_subset có độ tin cậy thấp; quy tắc dựa vào tổng giảm giá có thể gán nhầm.")
        left, right = st.columns(2)
        with left:
            st.markdown("**Tỷ lệ dòng quà theo tháng**")
            monthly_gift_view = monthly_gifts.copy()
            monthly_gift_view["gift_line_rate"] = monthly_gift_view["gift_line_rate"].map(pct)
            st.dataframe(localized_frame(monthly_gift_view[["month", "line_count", "gift_line_count", "gift_line_rate"]]), width="stretch", hide_index=True)
        with right:
            st.markdown("**Tỷ lệ dòng quà theo kích thước đơn**")
            size_gift_view = size_gifts.copy()
            size_gift_view["gift_line_rate"] = size_gift_view["gift_line_rate"].map(pct)
            st.dataframe(localized_frame(size_gift_view[["development_order_value_quartile", "line_count", "gift_line_count", "gift_line_rate"]]), width="stretch", hide_index=True)
        st.markdown("**Độ nhạy luật kết hợp**")
        st.dataframe(localized_frame(pd.DataFrame(day3["sensitivity_cells"])), width="stretch", hide_index=True)
        st.markdown("**Tỷ lệ gift line**")
        st.caption("Ngưỡng đơn lớn = phân vị 90 giá trị đơn DEV: " + money(day3["order_value_thresholds_vnd"]["p90"]))
        st.caption(f"Snapshot: {split.get('snapshot_id', '20261024T052943Z')} · hash split: {split_lock.get('config_sha256', '')} · manifest: {snapshot_hash}")

    with tabs[4]:
        st.subheader("Mô hình mua lại: DEV và test")
        dev_metrics = dev["repurchase_features_v2"]["selected_oof_metrics"]
        primary_oof = dev_primary["best_model_oof_metrics"]
        left, right = st.columns(2)
        left.metric("Tỷ lệ dương DEV", pct(dev["repurchase_features_v2"]["positive_rate"]))
        right.metric("Tỷ lệ dương test", pct(test["cohort"]["test_positive_rate"]))
        st.table(_model_rows(dev, test))
        st.markdown(
            f"**DEV OOF:** Logistic Regression C=10 — mô hình chính theo D-005: ROC-AUC {metric(primary_oof['roc_auc'])}, AP {metric(primary_oof['pr_auc'])}. "
            f"Logistic Regression feature-v2 C=0,1 — khảo sát bổ sung theo Amendment 04; không thay mô hình chính: ROC-AUC {metric(dev_metrics['roc_auc'])}, AP {metric(dev_metrics['pr_auc'])}."
        )
        st.info("ROC-AUC DEV OOF C=10 gần mức ngẫu nhiên (0,5096). ROC-AUC test khoảng 0,70 là tín hiệu yếu chưa được development xác nhận; không kết luận mô hình hoạt động tốt. Test đã mở, không dùng để tinh chỉnh hoặc chọn lại mô hình.")
        st.markdown("Amendment 05 ghi ngưỡng tín hiệu cho các classifier: cận dưới CI ROC-AUC > 0,55 và cận dưới CI ΔAP paired > 0. CI aggregate của cả hai classifier thỏa các cận trong lần chạy thực tế; trường `feature_v2_signal_supported=True` chỉ được lưu cho v2.")
        st.warning("Cấu hình ghi >T, evaluator dùng [T,end) (gồm ngày T); ảnh hưởng chưa xác định; đây là kết quả số liệu của lần chạy thực tế, không phải khẳng định tuân thủ đầy đủ giao thức, không gọi là 'đạt cổng ghi trước'.")
        st.caption("Chênh lệch DEV OOF với test chưa được giải thích; lịch sử đặc trưng dài hơn, prevalence khác nhau và Tết 2026 là giả thuyết chưa kiểm chứng. Chi tiết: docs/test_provenance_note.md. Ngưỡng phân loại 0,5; bootstrap 2.000 lượt, seed 20261026.")

    st.sidebar.markdown("---")
    st.sidebar.caption("Snapshot: 20261024T052943Z · cửa hàng bắt đầu 04/2024 · test đã mở đúng một lần")


if __name__ == "__main__":
    main()
