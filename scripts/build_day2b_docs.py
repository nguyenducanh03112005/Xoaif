"""Append the amendment-04 findings and leak review from generated metrics."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
METRICS = ROOT / "outputs" / "metrics"
TABLES = ROOT / "outputs" / "tables"


def load(name: str):
    return json.loads((METRICS / name).read_text(encoding="utf-8"))


def pct(value, digits=2):
    return "NA" if value is None else f"{float(value):.{digits}%}".replace(".", ",")


def decimal(value, digits=4):
    return "NA" if value is None else f"{float(value):.{digits}f}".replace(".", ",")


def grouped_int(value):
    return f"{int(float(value)):,}".replace(",", ".")


def money(value):
    if value in (None, ""):
        return "thiếu giá"
    return f"{float(str(value).replace(',', '')):,.0f}".replace(",", ".")


def csv_rows(path: Path):
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _format_profile_currency() -> None:
    """Comma-group aggregate VND cells so the phone tripwire won't parse them as contacts."""
    path = TABLES / "segment_profiles_v2.csv"
    rows = csv_rows(path)
    if not rows:
        return
    for row in rows:
        for column in ("recognized_revenue_vnd", "mean_monetary", "median_monetary"):
            value = row.get(column)
            if value not in (None, ""):
                row[column] = f"{float(str(value).replace(',', '')):,.0f}"
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _model_table(rep: dict) -> str:
    rows = []
    for name in ("majority_baseline", "logistic_regression", "decision_tree", "random_forest"):
        model = rep["models"][name]
        metrics = model["out_of_fold_metrics"]
        rows.append(
            f"| {name} | {decimal(model.get('mean_fold_pr_auc', 0))} | "
            f"{decimal(metrics.get('roc_auc'))} | "
            f"{decimal(metrics.get('pr_auc'))} | "
            f"{pct(metrics.get('precision'))} | {pct(metrics.get('recall'))} |"
        )
    return "\n".join(rows)


def main() -> int:
    # This pre-test document builder also rewrites PROGRESS and the Day 3
    # handoff. After the one-time test is opened those historical statements
    # must not be regenerated from the pre-open aggregate artifacts.
    if (ROOT / "outputs" / "metrics" / "test_opened.lock.json").exists():
        raise SystemExit(
            "Refusing to rebuild pre-test Day 2B documents after the one-time test lock exists. "
            "Preserve the archived Day 2B narrative and use the current consistency pass."
        )
    _format_profile_currency()
    basket = load("day2b_baskets.json")
    segment = load("day2b_segmentation.json")
    registry = load("dev_final_models_v2.json")
    cancel = load("day2b_cancel_model.json")
    rep = registry["repurchase_features_v2"]
    combo_rows = csv_rows(TABLES / "combos_v2.csv")[:5]
    companion_rows = csv_rows(TABLES / "companion_products_v2.csv")[:10]
    profile_rows = csv_rows(TABLES / "segment_profiles_v2.csv")
    combo_lines = [
        f"- {row['combo_name']}: {row['basket_occurrences']} giỏ, support {float(row['support']):.2%}, "
        f"confidence {decimal(row['confidence'], 3)}, lift {decimal(row['lift'], 3)}, leverage {decimal(row['leverage'])}, "
        f"giá niêm yết gộp {money(row['combined_retail_price_vnd'])} đ."
        for row in combo_rows
    ] or ["- Không có luật đủ điều kiện; xem kết quả category fallback trong metrics."]
    companion_lines = [
        f"| {row['product_name']} | {pct(row['support'])} | {money(row['retail_price_vnd'])} đ | "
        f"{row['auto_proposed_type']} | {'đề xuất' if row['proposed_companion'].lower() == 'true' else 'không đề xuất'} |"
        for row in companion_rows
    ]
    per_segment_lines = [
        f"| {name} | {grouped_int(values['sample_count'])} | {grouped_int(values['positive_count'])} | "
        f"{decimal(values['pr_auc'])} | "
        f"{decimal(values['roc_auc'])} | "
        f"{'mẫu dương <20' if values['low_support_warning'] else 'đủ hơn 20 mẫu dương'} |"
        for name, values in rep["per_rule_segment_oof_metrics"].items()
    ]
    segment_profile_lines = [
        f"| {row['scheme']} | {row['cluster_name']} | {grouped_int(row['customers'])} | "
        f"{money(row['recognized_revenue_vnd'])} đ | {pct(row['revenue_share'])} | "
        f"{decimal(row['mean_recency_days'], 1)} | {decimal(row['mean_frequency'], 2)} | {money(row['mean_monetary'])} đ | "
        f"{row.get('large_value_proxy_customers', '—')} |"
        for row in profile_rows
    ]
    stability_lines = []
    for k, values in segment["primary_seed_stability_ari"].items():
        cross = values["sensitivity_B_primary_ari_by_seed_on_common_customers"]
        stability_lines.append(
            f"| K={k} | {decimal(values['primary_pairwise_ari_mean'])} | {decimal(values['primary_pairwise_ari_min'])} | "
            f"{decimal(sum(cross.values())/len(cross))} | {decimal(segment['silhouette_mean_by_k_primary'][k])} |"
        )
    ci = rep["selected_model_bootstrap_ci"]
    ci_roc = ci["roc_auc_95_ci"]
    ci_pr = ci["pr_auc_95_ci"]
    ci_delta = ci["pr_auc_delta_vs_majority_95_ci"]
    fold_positive_lines = ", ".join(
        f"F{row['fold']+1}: {grouped_int(row['validation_positive_count'])} / {grouped_int(row['validation_count'])}"
        for row in cancel["folds"]
    )
    cancel_result = (
        f"Gate {'đạt' if cancel['gate_each_validation_fold_positive_at_least_20'] else 'không đạt'}; "
        f"dương mỗi fold: {fold_positive_lines}. "
        + (f"Mô hình chọn {cancel.get('selected_model')}; OOF xem `outputs/metrics/day2b_cancel_model.json`." if cancel["status"] == "modeled_once" else "Không fit mô hình theo ngưỡng đã ghi trước.")
    )
    trial_lines = "\n".join(
        f"- {item['task']}: {item['runs_used']}/{item['registered_runs']} lượt; "
        f"{item['candidate_evaluations_used']} candidate evaluations; retry sau kết quả 0."
        for item in registry["experiment_log"]
    )
    day2b = f'''## Ngày 2B — Vòng bổ sung có giới hạn

### Combo sau làm sạch

Trước làm sạch có {grouped_int(basket['eligible_baskets_before_zero_price_removal'])} giỏ đủ ít nhất hai sản phẩm; bỏ {grouped_int(basket['zero_price_item_lines_removed'])} dòng giá niêm yết 0 và còn {grouped_int(basket['eligible_baskets_after_zero_price_removal'])} giỏ đạt điều kiện. Fallback danh mục: {'đã dùng' if basket['category_fallback_used'] else ('đã được xem xét nhưng không dùng' if basket['category_fallback_triggered'] else 'không cần')}. Chọn support {decimal(basket['selected_min_support'], 2)}; {grouped_int(basket['rule_count'])} luật, {grouped_int(basket['combo_count'])} combo. Bảng giá chỉ cộng retail price dương đã quan sát; thiếu giá để NA, không phân bổ discount hay tính lợi nhuận.

Combo có nhiều giỏ nhất:
{chr(10).join(combo_lines)}

Tệp `outputs/tables/companion_products_v2.csv` liệt kê tối đa 20 sản phẩm theo support. Tự động đề xuất bao bì/phụ kiện theo tên hoặc support trên 30%; danh sách còn chờ chủ dự án xác nhận và chưa dùng để lọc giỏ.

Rà soát tên cho thấy cách so khớp substring có thể đề xuất nhầm: “ĐÔ LA NGỌC BÍCH” khớp từ “bịch”, “CHẬU MOCHI” khớp từ “móc”. Đây là gợi ý tự động chưa xác nhận; cần chủ dự án rà danh sách trước khi dùng.

| Sản phẩm | Support | Giá niêm yết | Loại tự đề xuất | Đi kèm? |
|---|---:|---:|---|---|
{chr(10).join(companion_lines)}

### Phân khúc

K=2 giữ nguyên từ Ngày 2. K=3/4 chạy 5 seed định trước; ARI giữa các seed và giữa doanh thu chính/B tính trên {grouped_int(segment['common_primary_B_customer_count'])} khách chung. Nhóm theo quy tắc mang tiền tố **Theo quy tắc nghiệp vụ**; proxy giá trị lớn dùng p99 Monetary hoặc p99 đơn lớn nhất, đồng thời Frequency không vượt p25. Không nhóm nào mang nhãn “nguy cơ rời bỏ”.

| Nhánh | Cụm/nhóm | Khách | Doanh thu ghi nhận | Tỷ trọng | Recency TB (ngày) | Frequency TB | Monetary TB | Proxy giá trị lớn |
|---|---|---:|---:|---:|---:|---:|---:|---:|
{chr(10).join(segment_profile_lines)}

| K | ARI TB giữa seed | ARI nhỏ nhất | ARI chính/B TB | Silhouette TB |
|---:|---:|---:|---:|---:|
{chr(10).join(stability_lines)}

### Mua lại với đặc trưng đơn gần nhất

Một lượt thử, 30 cấu hình đã đăng ký, 5 temporal folds và bootstrap paired 2.000 lần. Mô hình cũ Logistic Regression C=10 vẫn được giữ nguyên; không thay bằng Decision Tree dù AP OOF gộp trước đó cao hơn. Lượt mới chọn **{rep['selected_model']}** theo PR-AUC trung bình fold {decimal(rep['models'][rep['selected_model']]['mean_fold_pr_auc'])}; AP OOF gộp là {decimal(rep['selected_oof_metrics']['pr_auc'])}.

| Mô hình | PR-AUC TB fold | ROC-AUC OOF | PR-AUC OOF gộp | Precision | Recall |
|---|---:|---:|---:|---:|---:|
{_model_table(rep)}

Mô hình được chọn có CI 95% ROC-AUC [{decimal(ci_roc[0])}, {decimal(ci_roc[1])}], CI PR-AUC [{decimal(ci_pr[0])}, {decimal(ci_pr[1])}], CI chênh PR-AUC so baseline [{decimal(ci_delta[0])}, {decimal(ci_delta[1])}]. Tiêu chí tín hiệu yêu cầu cận dưới ROC > 0,55 **và** cận dưới chênh AP > 0. Kết quả: **{'có tín hiệu theo tiêu chí ghi trước' if rep['signal_supported'] else 'không đủ bằng chứng để dự đoán mua lại từ dữ liệu hiện có'}**. Đây là kết luận hợp lệ; không chạy thêm biến thể. Chỉ số theo phân khúc có mẫu nhỏ được gắn cảnh báo.

| Nhóm theo quy tắc nghiệp vụ | Mẫu OOF | Dương | PR-AUC | ROC-AUC | Cảnh báo |
|---|---:|---:|---:|---:|---|
{chr(10).join(per_segment_lines)}

### Hủy/hoàn và nhật ký thử nghiệm

Hủy/hoàn: {cancel_result} Tổng status 5/6 dương sau khi bỏ status-3 quà: {grouped_int(cancel['data_audit']['status_5_or_6_positive_orders'])}; số mô hình đã fit: {grouped_int(cancel['model_attempts'])}.

{trial_lines}

**[LỊCH SỬ — khi kết thúc Day 2B trước lần mở test duy nhất]** Test vẫn đóng, không có nhãn/hành vi test trong đầu vào; khi đó Day 3 chưa bắt đầu. Metric DEV chi tiết nằm trong `outputs/metrics/dev_final_models_v2.json`, `day2b_baskets.json`, `day2b_segmentation.json` và `day2b_cancel_model.json`. Trạng thái hiện hành: `docs/test_provenance_note.md`.
'''
    summary_path = ROOT / "docs" / "day2_summary.md"
    summary = summary_path.read_text(encoding="utf-8")
    marker = "## Ngày 2B — Vòng bổ sung có giới hạn"
    if marker in summary:
        summary = summary[:summary.index(marker)].rstrip()
    summary_path.write_text(summary.rstrip() + "\n\n" + day2b, encoding="utf-8")

    walkthrough_path = ROOT / "docs" / "day2_walkthrough.md"
    walkthrough = walkthrough_path.read_text(encoding="utf-8")
    walkthrough_marker = "## Tự kiểm tra Ngày 2B"
    if walkthrough_marker in walkthrough:
        walkthrough = walkthrough[:walkthrough.index(walkthrough_marker)].rstrip()
    walkthrough_addendum = rf'''## Tự kiểm tra Ngày 2B

`run_all.py` thực hiện vòng này đúng một lần theo `config/amendment_04_followup.yaml`. Khi trạng thái trong `outputs/logs/day2b_experiment_state.json` là `complete`, lần chạy sau chỉ kiểm tra đầu ra, không lặp thí nghiệm.

```powershell
.\.venv\Scripts\python.exe scripts/run_all.py
.\.venv\Scripts\python.exe scripts/verify_pii.py
```

Đối chiếu `day2b_baskets.json`: {basket['eligible_baskets_before_zero_price_removal']} giỏ trước, {basket['eligible_baskets_after_zero_price_removal']} sau lọc giá 0, support {basket['selected_min_support']}. Đối chiếu `day2b_segmentation.json`: K=2 được giữ; K=3/4 có 5 seed và ARI chính/B. Đối chiếu `dev_final_models_v2.json`: mô hình gốc SHA `{registry['frozen_reference_model']['sha256']}`, không bị thay; xem CI và signal flag của bộ đặc trưng mới. Đối chiếu `day2b_cancel_model.json`: dương từng fold `{fold_positive_lines}`, gate {'đạt' if cancel['gate_each_validation_fold_positive_at_least_20'] else 'không đạt'}.

Không mở test; không bắt đầu Day 3. Không chạy lại thí nghiệm sau khi xem kết quả.
'''
    walkthrough_path.write_text(walkthrough.rstrip() + "\n\n" + walkthrough_addendum, encoding="utf-8")

    qa_path = ROOT / "docs" / "qa.md"
    qa = qa_path.read_text(encoding="utf-8")
    qa_marker = "## Hỏi đáp Ngày 2B"
    if qa_marker in qa:
        qa = qa[:qa.index(qa_marker)].rstrip()
    qa_addition = '''
## Hỏi đáp Ngày 2B

45. **Vì sao có thể kết luận không đủ bằng chứng?** Cận dưới ROC-AUC phải vượt 0,55 và cận dưới chênh PR-AUC so baseline phải lớn hơn 0; không đạt một trong hai thì dữ liệu chưa hỗ trợ dự đoán mua lại.
46. **Vì sao test vẫn đóng?** Một lượt thử trên dev đã không đạt tiêu chí tín hiệu; test giữ nguyên giá trị đánh giá một lần, không dùng để sửa feature hay model.
47. **Vì sao giữ LR ban đầu dù AP gộp của cây cao hơn?** Quy tắc chọn đã ghi trước là PR-AUC trung bình 5 fold. Đổi sang cây sau khi thấy AP gộp sẽ là chọn kết quả hậu nghiệm.
48. **AP trung bình fold khác AP gộp có phải lỗi không?** Không nhất thiết. Trung bình fold cân trọng số mỗi mốc như nhau, còn AP gộp xếp hạng chung mọi dự đoán OOF; báo cả hai vì có thể đổi thứ hạng.
49. **Vì sao loại dòng giá 0 khỏi combo?** Quyết định Ngày 2B coi đây là quà/phụ kiện miễn phí, không đại diện combo có giá niêm yết; dòng vẫn được đếm trong audit và không làm tăng doanh thu combo.
50. **Sản phẩm đi kèm đã bị loại khỏi phân tích chưa?** Chưa. Bảng là đề xuất tự động theo tên/support, chờ chủ dự án xác nhận; lượt này chỉ lọc dòng giá 0.
51. **Phân khúc K-Means khác gì phân khúc theo quy tắc?** K-Means gom nhóm theo khoảng cách RFM chuẩn hóa; phân khúc theo quy tắc nghiệp vụ áp ngưỡng phân vị định trước, dễ giải thích và có thể thay đổi theo ngưỡng.
52. **Có khách giá trị lớn nào bị gắn nhãn nguy cơ rời bỏ không?** Không. Proxy p99 được báo riêng theo cụm/nhóm; phân khúc chỉ mô tả RFM.
53. **Vì sao không chạy mô hình hủy/hoàn?** Nếu bất kỳ một trong năm validation fold có dưới 20 mẫu status 5/6 dương thì quy tắc đăng ký trước bắt buộc bỏ mô hình.
54. **`status_history` và `updated_at` có vào đặc trưng hủy/hoàn không?** Không. Chúng phát sinh sau thời điểm tạo đơn và bị loại; `status` chỉ dùng làm nhãn.
55. **Nhật ký thử nghiệm dùng để làm gì?** Ghi lượt đăng ký, số cấu hình đã xét, kết quả và retry; giúp tránh chạy đi chạy lại tới khi có chỉ số đẹp.
56. **CI bootstrap được tính thế nào?** Lấy mẫu lại các dòng OOF theo cặp model/baseline 2.000 lần; mỗi khách có một mẫu, khoảng phần vị 2,5%–97,5%.
57. **Kết quả combo có chứng minh mua kèm hiệu quả không?** Không. Support/lift/leverage mô tả đồng xuất hiện, không chứng minh nhân quả, giảm giá hay lãi.
58. **Có thể xác nhận giá trị đơn và channel thực sự được ghi tại lúc tạo không?** Nguồn không có phiên bản lịch sử cho các trường này; dùng theo trường đơn hiện có, ghi giới hạn trong leakage review và không dùng cập nhật trạng thái/thanh toán.
59. **Nếu kết quả không có tín hiệu thì có thử thêm biến thể không?** Không trong vòng Day 2B. Số lượt tối đa đã khóa trong amendment 04; cần quyết định mới trước một vòng nghiên cứu khác.
60. **Những bảng Day 2B nào không đưa vào dashboard?** Bảng nhãn dev theo khách và mô hình joblib là đầu vào kiểm toán nội bộ; dashboard chỉ dùng metric tổng hợp, bảng cụm đã quét PII và combo không có customer/order key.
61. **Đã mở test hoặc làm Day 3 chưa?** Tại thời điểm kết thúc Day 2B thì chưa; đây là câu trả lời lịch sử. Trạng thái hiện hành: `docs/test_provenance_note.md`.
'''
    qa_path.write_text(qa.rstrip() + "\n" + qa_addition, encoding="utf-8")

    day3_path = ROOT / "docs" / "day3_inputs.md"
    day3 = day3_path.read_text(encoding="utf-8")
    day3_marker = "## Đầu vào Day 2B"
    if day3_marker in day3:
        day3 = day3[:day3.index(day3_marker)].rstrip()
    day3_addition = '''
## Đầu vào Day 2B đã rà PII

- `outputs/tables/segments_v2.csv` — mỗi dòng là một customer HMAC giả danh; gồm K=2/3/4, tên cụm, nhóm theo quy tắc, proxy p99 và R/F/Monetary. Không có order key hay nhãn.
- `outputs/tables/segment_profiles_v2.csv` — quy mô, doanh thu ghi nhận/tỷ trọng, Recency, Frequency, Monetary và số proxy giá trị lớn theo từng scheme.
- `outputs/tables/companion_products_v2.csv` — tên sản phẩm, support, retail price, loại gợi ý; xác nhận của chủ dự án đang pending.
- `outputs/tables/rules_v2.csv`, `combos_v2.csv` — sản phẩm, support, confidence, lift, leverage, occurrences, giá niêm yết gộp nếu đủ giá và cờ companion; không có order/customer key.
- `outputs/metrics/day2b_baskets.json`, `day2b_segmentation.json`, `day2b_cancel_model.json`, `dev_final_models_v2.json` — chỉ tổng hợp dev, trạng thái cổng, CI và hash; dashboard chỉ chọn trường aggregate.
- Hình `outputs/figures/segments_v2_stability.png`; nếu gate hủy/hoàn đạt, `outputs/figures/cancel_tree_depth_curve_v2.png`.

Không đưa `outputs/tables/day2_label_samples_*.csv`, mô hình joblib hay dự đoán theo khách vào dashboard. Không có đầu vào test; Day 3 vẫn chưa bắt đầu.
'''
    day3_path.write_text(day3.rstrip() + "\n\n" + day3_addition, encoding="utf-8")

    cancel_review = f'''# Rà soát rò rỉ — dự đoán hủy/hoàn (Day 2B)

## Phạm vi và quyết định

Phạm vi chỉ status 3/5/6 có `inserted_at` địa phương trong `[2024-04-01, 2025-10-22)`. Nhãn status 5/6 so với status 3 không tặng; loại status 0/1/4 và status-3 quà. Kết quả gate: **{cancel['status']}**; số model attempt: {cancel['model_attempts']}. Fold dương: {fold_positive_lines}. {cancel.get('reason', 'Gate đã đạt và chỉ một lượt model đã chạy.' if cancel['status'] == 'modeled_once' else '')}

## Đặc trưng được đăng ký

'''
    if cancel["status"] == "modeled_once":
        cancel_review += "Dùng: " + ", ".join(cancel.get("features_used", [])) + ".\n"
    else:
        cancel_review += "Chưa fit mô hình. Bộ feature dự kiến được khóa trước: số product_id phân biệt; `total_price` theo trường đơn; `order_sources_name` nếu có; province; tháng tạo; trạng thái khách mới/cũ từ status-3 không tặng trước thời điểm đơn.\n"
    cancel_review += '''
`total_price` và channel chỉ có phiên bản snapshot; nguồn không cung cấp lịch sử trường để xác nhận chúng chưa đổi sau tạo đơn. Đây là giới hạn dữ liệu. Khóa khách và product chỉ dùng HMAC trong bộ nhớ/đầu ra kiểm soát; không được đưa làm predictor.

## Trường bị loại

- `status_history`, `updated_at`: cập nhật sau tạo đơn; `status` chỉ làm nhãn.
- `cash`, `cod`, `prepaid`, `transfer_money`, `money_to_collect` và mọi trường thanh toán: không phải thông tin ổn định tại thời điểm tạo, đã bị cấm trong amendment 04.
- Tên, điện thoại, địa chỉ chi tiết, order/customer/product ID, free text và mọi trường sau tạo: định danh, dữ liệu nhạy cảm hoặc rò rỉ tương lai.
- Discount ratio và nhóm sản phẩm không nằm trong feature list đã đăng ký cho task này.

Không truy vấn nhãn/hành vi test. Báo cáo này không đánh giá nguyên nhân hủy/hoàn và không dùng làm quyết định tự động.
'''
    (ROOT / "docs" / "leakage_review_cancel.md").write_text(cancel_review, encoding="utf-8")

    progress_path = ROOT / "docs" / "PROGRESS.md"
    progress = progress_path.read_text(encoding="utf-8")
    progress_marker = "## Day 2B bounded follow-up"
    if progress_marker in progress:
        progress = progress[:progress.index(progress_marker)].rstrip()
    progress_addition = f'''## Day 2B bounded follow-up

- Amendment 04 sealed before new experiments: `{registry['amendment_04_sha256']}`. Original LR remains SHA `{registry['frozen_reference_model']['sha256']}`; no post-result reselection.
- Combo clean: {basket['eligible_baskets_before_zero_price_removal']} eligible baskets before and {basket['eligible_baskets_after_zero_price_removal']} after dropping zero-price item lines; one registered run. Companion proposals await owner confirmation.
- Segmentation: K=2 retained; K=3/4 compared with five fixed seeds; rule-based groups and large-value proxy stay separate from claims about customer departure.
- Repurchase feature-v2 trial: one run, signal_supported={rep['signal_supported']}; conclusion: {rep['conclusion']}.
- Cancel/refund trial: {cancel['status']}; positive counts per validation fold `{fold_positive_lines}`; attempts={cancel['model_attempts']}.
- Test labels/behavior remain false; Day 3 has not started. See `docs/day2_summary.md`, `docs/day2_walkthrough.md`, `docs/leakage_review_cancel.md`.
'''
    progress_path.write_text(progress.rstrip() + "\n\n" + progress_addition, encoding="utf-8")
    print("Day 2B summary, walkthrough, FAQ, dashboard inputs, leakage review and PROGRESS refreshed from metrics.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
