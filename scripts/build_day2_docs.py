"""Assemble Day 2 review documents from generated metric artifacts."""
from __future__ import annotations
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
METRICS = ROOT / "outputs" / "metrics"
TABLES = ROOT / "outputs" / "tables"
FIGURES = ROOT / "outputs" / "figures"


def load(name):
    return json.loads((METRICS / name).read_text(encoding="utf-8"))


def percent(value, digits=2):
    return "không xác định" if value is None else f"{value:.{digits}%}"


def number(value):
    return f"{value:,}" if isinstance(value, int) else str(value)


def main() -> int:
    # These documents record the pre-open state. Do not regenerate them from
    # development-only inputs after the one-time test lock exists.
    if (ROOT / "outputs" / "metrics" / "test_opened.lock.json").exists():
        raise SystemExit(
            "Refusing to rebuild pre-test Day 2 documents after the one-time test lock exists. "
            "Preserve the archived narrative and use the current consistency pass."
        )
    money = load("day2_money_audit.json")
    prep = load("day2_preprocessing.json")
    labels = load("day2_label_audit.json")
    segments = load("day2_segmentation.json")
    model = load("dev_final_model.json")
    baskets = load("day2_baskets.json")

    profiles = list(csv.DictReader((TABLES / "segment_profiles.csv").open(encoding="utf-8-sig")))
    combo_rows = list(csv.DictReader((TABLES / "combos.csv").open(encoding="utf-8-sig")))
    top_combos = combo_rows[:5]
    model_rows = []
    for key in ("majority_baseline", "logistic_regression", "decision_tree", "random_forest"):
        item = model["models"][key]
        metrics = item["out_of_fold_metrics"]
        cm = metrics["confusion_matrix_tn_fp_fn_tp"]
        model_rows.append(
            f"| {key} | {item['mean_fold_pr_auc']:.4f} | {percent(metrics['precision'])} | "
            f"{percent(metrics['recall'])} | {percent(metrics['f1'])} | {metrics['roc_auc']:.4f} | "
            f"{metrics['pr_auc']:.4f} | {cm[0][0]}/{cm[0][1]}/{cm[1][0]}/{cm[1][1]} | "
            f"{json.dumps(item['selected_parameters'], ensure_ascii=False)} |"
        )
    cluster_lines = [
        f"  - Cụm {row['cluster_id']} — {row['cluster_name']}: {number(int(row['customers']))} khách, "
        f"tần suất TB {float(row['mean_frequency']):.2f}, Monetary TB {float(row['mean_monetary']):,.0f} VND, "
        f"{percent(float(row['revenue_share']))} Monetary toàn tập, "
        f"{number(int(row['business_like_customers']))} khách thuộc proxy giá trị lớn."
        for row in profiles
    ]
    combo_lines = [
        f"  - {row['combo_name']}: xuất hiện {row['basket_occurrences']} giỏ, support {float(row['support']):.3%}, "
        f"confidence {float(row['confidence']):.3f}, lift {float(row['lift']):.3f}, "
        f"giá niêm yết gộp {row.get('combined_retail_price_vnd') or 'chưa đủ dữ liệu'} VND."
        for row in top_combos
    ] or ["  - Không có luật đủ số lần xuất hiện để báo cáo."]
    sensitivity_money = money["revenue_comparison"]
    sensitivity_cluster = segments["sensitivity"]
    sensitivity_model = model["sensitivity_A_B"]
    sensitivity_lines = [
        f"- A (total_price-total_discount): chênh tổng doanh thu ghi nhận {sensitivity_money['difference_percent_of_abs_A']:.2f}% so với A; "
        f"{sensitivity_money['orders_different_by_more_than_1_percent']}/{sensitivity_money['non_gift_orders_compared']} đơn lệch trên 1%; "
        f"Spearman Monetary theo khách {sensitivity_money['customer_monetary_spearman']:.4f}. "
        f"Cụm đổi {percent(sensitivity_cluster['A']['aligned_customer_cluster_change_rate'])}, Silhouette đổi {sensitivity_cluster['A']['silhouette_delta_from_primary']:+.4f}; "
        f"PR-AUC của mô hình được chọn đổi {sensitivity_model['A']['delta_vs_primary']['pr_auc']:+.4f}.",
        f"- B (loại đơn điều chỉnh hoặc chưa giải thích): bỏ {money['sensitivity_B_exclude_adjusted_or_unexplained']['excluded_non_gift_orders']} đơn không quà; "
        f"cụm đổi {percent(sensitivity_cluster['B']['aligned_customer_cluster_change_rate'])}, "
        f"Silhouette đổi {sensitivity_cluster['B']['silhouette_delta_from_primary']:+.4f}; "
        f"PR-AUC đổi {sensitivity_model['B']['delta_vs_primary']['pr_auc']:+.4f}.",
    ]
    doc = f'''# Tóm tắt Ngày 2

## Kết quả chính

- **Quy tắc tiền:** 6.400 đơn status 3 trong `[{money['analysis_start']},{money['test_start_exclusive']})`. Doanh thu ghi nhận dùng `after_sub_discount-shipping_fee`, với ngoại lệ đã ghi trong amendment 03. Có {money['gifts']['count']} đơn tặng; {money['negative_revenue']['count']} đơn doanh thu âm ({percent(money['negative_revenue']['rate'])}), Monetary bằng 0 nhưng vẫn nằm trong F/R. Cổng dừng 1% đạt. Điều chỉnh dương chiếm {percent(money['price_adjustment']['positive_rate'])}, âm {percent(money['price_adjustment']['negative_rate'])}; tổng điều chỉnh ròng {money['price_adjustment']['net_sum']} VND ({money['price_adjustment']['net_sum_as_percent_of_recognized_revenue']:.2f}% tổng doanh thu ghi nhận).
- **Preprocess và nhãn:** {prep['status3_dev_orders']} đơn status 3; {prep['missing_customer_id_orders']} thiếu customer ID nên loại khỏi mức khách; {prep['gift_orders']} đơn quà bị loại khỏi hành vi; {prep['orders_without_line_items']} đơn không có dòng hàng bị loại khỏi giỏ. Đặc trưng gồm R/F/Monetary, giá trị đơn TB/lớn nhất, số lượng, product phân biệt, khoảng cách mua, tháng đầu, tỉnh/thành, adjustment dương/âm và khoảng cách từ lần mua cuối đến lễ gần nhất. Tết dùng ngày mùng 1 được công bố chính thức: 10-02-2024 ([Chính phủ](https://xaydungchinhsach.chinhphu.vn/danh-sach-cac-diem-ban-phao-hoa-tai-tp-hcm-dip-tet-nguyen-dan-giap-thin-2024-119240125193656008.htm)) và 29-01-2025 ([Chính phủ](https://xaydungchinhsach.chinhphu.vn/danh-sach-cac-diem-ban-phao-hoa-dip-tet-duong-lich-2025-va-tet-nguyen-dan-at-ty-tai-ha-noi-119241230172030261.htm)). Tập nhãn có {labels['customer_samples']} khách duy nhất, {labels['positive_samples']} dương ({percent(labels['positive_rate'])}); mốc nhãn xa nhất kết thúc {labels['max_label_asof']}, trước `test_start`. Theo quy tắc ghi trước, ngưỡng tối thiểu 100 mẫu dương và 5% đều đạt.
- **Tần suất mua:** trên {sum(int(value) for value in labels['frequency_distribution_at_test_start'].values())} khách ở snapshot `test_start`, phân phối đơn hợp lệ mỗi khách là `{json.dumps(labels['frequency_distribution_at_test_start'], ensure_ascii=False)}`; 1 đơn chiếm {percent(segments['single_order_customer_rate'])}.
- **Khách giá trị lớn:** proxy là Monetary hoặc giá trị đơn lớn nhất đạt phân vị 99 trong dev. Ngưỡng Monetary {labels['large_value_customer_proxy']['monetary_p99']:,.0f} VND; ngưỡng giá trị đơn {labels['large_value_customer_proxy']['maximum_order_value_p99']:,.0f} VND; {labels['large_value_customer_proxy']['customers']} khách nằm trong proxy. Đây không phải phân loại pháp lý/doanh nghiệp.
- **Phân khúc:** K={segments['chosen_k']}; Silhouette={segments['chosen_silhouette']:.3f}. Frequency bằng 1 ở {percent(segments['single_order_customer_rate'])} khách, nên F ít phân tách. Đặt tên cụm theo số liệu:
{chr(10).join(cluster_lines)}
### Phân loại quay lại

Expanding temporal folds có khoảng đệm `N+L=187` ngày và khách rời nhau. Pipeline fit imputer, scaler và encoder chỉ trong train fold. Precision/Recall/F1 và ma trận nhầm lẫn bên dưới dùng ngưỡng xác suất mặc định 0,5.
Chọn mô hình/siêu tham số theo PR-AUC trung bình của 5 fold thời gian; chỉ 1.558/{labels['customer_samples']} mẫu có dự đoán OOF vì các cohort đầu không đủ khoảng đệm nhãn 187 ngày. Bảng dưới báo thêm điểm gộp trên OOF; hai cách tổng hợp có thể xếp hạng khác nhau.

| Mô hình | PR-AUC TB 5 fold | Precision OOF | Recall OOF | F1 OOF | ROC-AUC OOF | PR-AUC OOF gộp | TN/FP/FN/TP | Tham số |
|---|---:|---:|---:|---:|---:|---:|---:|---|
{chr(10).join(model_rows)}

Logistic Regression được chọn theo trung bình fold (0.1093), nhưng PR-AUC gộp của Decision Tree cao nhất (0.0798 so với Logistic Regression 0.0699 và baseline 0.0671). Với Logistic Regression, ROC-AUC gộp 0.5096 gần mức ngẫu nhiên; Precision 5.87% và 705 FP so với 44 TP. Vì vậy mô hình hiện **chưa đủ tin cậy cho hành động khách hàng hoặc triển khai**; mức cải thiện so với baseline nhỏ và kết quả phụ thuộc cách gộp fold.

Decision Tree ở depth 8 có PR-AUC train 0.4323, validation 0.0910, khoảng cách 0.3413, cho thấy overfit. Theo phân khúc của mô hình được chọn: nhóm mua một lần PR-AUC 0.0747 (n=1.490); mua lặp lại 0.0986 (n=58, chỉ 7 dương); proxy giá trị lớn/tần suất thấp 0.1667 (n=10, chỉ 1 dương), nên hai nhóm sau không đủ mẫu để kết luận ổn định.
### Giỏ hàng

Có {baskets['eligible_product_baskets']} giỏ status 3, không quà, ít nhất 2 product_id; dùng {baskets['baskets_used']} giỏ cho luật. Chọn support {baskets.get('selection',{}).get('selected_min_support')} — mức cao nhất đã thử còn ít nhất 5 luật lift > 1, mỗi luật xuất hiện từ 5 giỏ — tạo {baskets['rule_count']} luật và {baskets['combo_count']} combo. Đây là đồng xuất hiện; combo đầu có giá niêm yết gộp 0 VND theo dữ liệu:
{chr(10).join(combo_lines)}

## Độ nhạy

{chr(10).join(sensitivity_lines)}

Độ nhạy là kiểm tra mức phụ thuộc vào cách định nghĩa tiền; không chứng minh định nghĩa nào đúng hơn. `price_adjustment` ở mức đơn không được phân bổ xuống sản phẩm.

## Độ tin cậy và giới hạn

- Quy tắc amendment 03 thay đổi sau khi cổng amendment 02 báo 701/6.400 (10,95%) vượt 5%, dựa trên hiểu biết nghiệp vụ của chủ cửa hàng. Đây là thay đổi sau khi xem kết quả cổng cũ; kết quả cần được diễn giải cùng độ nhạy.
- Tỷ lệ điều chỉnh dương/`adj_unexplained` không cao nhất ở các tháng mở đầu; xem đỉnh và từng tháng tại `docs/money_audit.md`. Điều này gợi ý bất thường tập trung theo giai đoạn, không phải bằng chứng nguyên nhân.
- Nhãn dựa trên status hiện tại, không có lịch sử hoàn/đổi đủ để tái dựng trạng thái tại `T+N+L`. Đây là nhãn dự báo trong dev, không khẳng định nhân quả.
- Nhiều khách chỉ có một đơn, số khách dương hạn chế so với tổng mẫu; các chỉ số validation không đại diện độc lập cho mọi mùa vụ/khách tương lai.
- Chỉ có tỉnh/thành, không có tọa độ/mã vùng đủ chi tiết nên bỏ qua DBSCAN địa lý. Không có giá vốn nên không thể tính lợi nhuận.
- Test chưa mở, `test_labels_loaded=false`, `test_behavior_loaded=false`; không có bước Ngày 3 nào được bắt đầu.

## Đầu ra

- Tiền: `docs/money_audit.md`, `outputs/tables/money_diagnosis.csv`, `outputs/metrics/day2_money_audit.json`.
- Khách/phân khúc: `outputs/tables/day2_features_primary.csv`, `outputs/tables/segments.csv`, `outputs/tables/segment_profiles.csv`, `outputs/figures/segments_elbow.png`, `outputs/figures/segments_silhouette.png`.
- Phân loại: `outputs/metrics/dev_final_model.json`, `outputs/models/day2_dev_final_model.joblib`, `outputs/figures/decision_tree_depth_curve.png`.
- Giỏ hàng: `outputs/tables/rules.csv`, `outputs/tables/combos.csv`.
'''
    (ROOT / "docs" / "day2_summary.md").write_text(doc, encoding="utf-8")

    walkthrough = f'''# Hướng dẫn đi lại Ngày 2

Quy trình chỉ dùng status 3 thuộc `[2024-04-01,2025-10-22)`. Notebook không truy vấn API; dữ liệu đọc từ snapshot đã khóa. Trước khi bắt đầu, xác nhận amendment và split:

```powershell
.\\.venv\\Scripts\\python.exe scripts/verify_split_lock.py
```

1. **Kiểm toán tiền.** Làm gì: `scripts/audit_money.py` áp dụng amendment 03 và viết JSON/CSV/báo cáo. Vì sao: xác nhận doanh thu ghi nhận, ngoại lệ, điều chỉnh và cổng dừng 1% trước khi tạo đặc trưng. Tự kiểm tra: `status3_orders=6400`, `negative_revenue.stop=false`, gifts=22, negative=2 trong `outputs/metrics/day2_money_audit.json`.
2. **Đặc trưng và nhãn.** Làm gì: Restart & Run All `notebooks/02_preprocess.ipynb`. Vì sao: dựng snapshot tại T và nhãn dev sau khi chặn dữ liệu tương lai. Tự kiểm tra: `{labels['customer_samples']}` khách, `{labels['positive_samples']}` dương; `max_label_asof < test_start`; hai cờ test trong `outputs/metrics/day2_label_audit.json` là `false`.
3. **Phân khúc.** Làm gì: chạy `notebooks/04_unsupervised.ipynb`, xem `segments_elbow.png`, `segments_silhouette.png`, `segment_profiles.csv`, `segments.csv`. Vì sao: chọn K có số liệu và kiểm tra khách giá trị cao không bị gán nhãn rời bỏ. Tự kiểm tra: `chosen_k={segments['chosen_k']}` và xem A/B trong `outputs/metrics/day2_segmentation.json`.
4. **Phân loại.** Làm gì: chạy `notebooks/03_supervised.ipynb`. Vì sao: đo khả năng tổng quát theo thời gian, không trộn khách và chỉ fit tiền xử lý trong train. Tự kiểm tra: 5 fold, OOF coverage={model['models'][model['best_model']]['out_of_fold_coverage']:,}, xem PR-AUC/ma trận nhầm lẫn, `tree_depth_diagnostics` và SHA trong `outputs/metrics/dev_final_model.json`; cờ test phải `false`.
5. **Combo.** Làm gì: chạy `notebooks/05_combo.ipynb`. Vì sao: tìm đồng xuất hiện trong đơn đủ sản phẩm, không diễn giải nhân quả hay lợi nhuận. Tự kiểm tra: `{baskets['eligible_product_baskets']}` giỏ, support={baskets.get('selection',{}).get('selected_min_support')}, `{baskets['rule_count']}` luật trong `outputs/metrics/day2_baskets.json` và `outputs/tables/rules.csv`/`combos.csv`.
6. **Kiểm tra cuối.** Làm gì: chạy `scripts/verify_pii.py` và pipeline tổng thể bằng:

```powershell
.\\.venv\\Scripts\\python.exe scripts/run_all.py
```

Không mở test. Ngày 3 chỉ được cân nhắc sau khi chủ dự án xem tóm tắt và xác nhận.
'''
    (ROOT / "docs" / "day2_walkthrough.md").write_text(walkthrough, encoding="utf-8")

    qa_path = ROOT / "docs" / "qa.md"
    qa = qa_path.read_text(encoding="utf-8")
    marker = "## Hỏi đáp Ngày 2"
    if marker in qa:
        qa = qa[:qa.index(marker)].rstrip() + "\n"
    day2_qa = '''
## Hỏi đáp Ngày 2

16. **Doanh thu ghi nhận được tính thế nào?** Mặc định là `total_price_after_sub_discount-shipping_fee`; nếu `after == total_price-total_discount` và ship dương thì dùng `after` để tránh trừ ship hai lần.
17. **Vì sao dùng `after - ship`?** Mẫu rà 13 đơn cho thấy đa số `after` đã gồm ship; phép so khớp xác định cách lấy tiền hàng và ngoại lệ được khóa riêng.
18. **Vì sao không dùng `cash`, `cod`, `prepaid`, `transfer_money` hay `money_to_collect`?** Chủ cửa hàng xác nhận thao tác thanh toán trên app giai đoạn đầu chưa tin cậy; các trường này không lọc đơn và không chứng minh đã thanh toán.
19. **Vì sao status 3 được xem là doanh thu?** Chủ cửa hàng xác nhận status 3 là đơn đã nhận/ghi nhận; đơn tại quầy thu tiền mặt. Đây là xác nhận nghiệp vụ, không phải đối soát ngân hàng.
20. **Cột dashboard đã xác nhận chưa?** Chưa. Bằng chứng là rà mẫu 13 đơn và xác nhận bằng lời; `dash_*` vẫn trống, không có bảng dashboard chi tiết.
21. **`price_adjustment` là gì?** `revenue_recognized-(total_price-total_discount)`. Dương là phí/giá cao hơn, âm là ưu đãi thêm, bằng 0 là khớp.
22. **Có loại đơn vì điều chỉnh khác 0 không?** Không trong bản chính; điều chỉnh được giữ và phân tích như cột riêng.
23. **`adj_unexplained` có nghĩa là đơn sai không?** Không. Nó chỉ đánh dấu mẫu chênh chưa giải thích được theo các quan hệ chính xác đã liệt kê; công thức chính vẫn áp dụng.
24. **Vì sao đơn 0 đồng bị loại khỏi hành vi?** Chủ cửa hàng xác nhận đó là quà/ưu đãi người quen; giữ raw, đếm riêng, không để đơn quà làm tăng F/R, nhãn hoặc giỏ.
25. **Đơn doanh thu âm có bị xóa không?** Không. Gắn cờ, Monetary đóng góp bằng 0, nhưng đơn vẫn thuộc F/R; dừng kỹ thuật chỉ khi vượt 1% status-3 dev.
26. **Vì sao cổng 5% bị bỏ?** Chủ dự án đổi quy tắc sau kết quả 701/6.400 (10,95%) dựa trên nghiệp vụ status 3 và phí/ưu đãi. Đây là thay đổi có chủ đích sau khi xem cổng cũ, cần đọc cùng độ nhạy.
27. **Độ nhạy A kiểm tra điều gì?** So `total_price-total_discount` với doanh thu ghi nhận; báo chênh tổng, số đơn chênh trên 1%, và Spearman Monetary theo khách.
28. **Độ nhạy B kiểm tra điều gì?** Loại hợp đơn có điều chỉnh khác 0 hoặc chưa giải thích rồi chạy lại phân khúc/phân loại; nó cho thấy kết quả nhạy đến đâu với nhóm này, không chứng minh công thức nào đúng.
29. **Làm gì để tránh rò rỉ qua T?** Chỉ dùng đơn có ngày địa phương `<T` để tạo đặc trưng; nhãn chỉ nhìn `(T,T+N]`; mọi tiền xử lý mô hình được fit trong train fold.
30. **Có khách ở cả train và validation không?** Không. Mỗi khách chỉ có một mẫu và mỗi validation T được so với train có nhãn kết thúc trước T đủ `N+L` ngày.
31. **K-Means chọn K thế nào?** So K=2..8 bằng inertia/Elbow, Silhouette và độ ổn định giữa nhiều seed; đặt tên cụm theo đặc trưng trung bình, quy mô và tỷ trọng doanh thu.
32. **Vì sao nhiều khách có thể không được phân biệt bởi Frequency?** Phần lớn chỉ có một đơn, nên F gần hằng số; Recency và Monetary đóng vai trò phân tách nhiều hơn.
33. **Khách giá trị lớn có bị gọi là sắp rời đi không?** Không. Báo riêng proxy ngưỡng p99 và kiểm số khách giá trị lớn trong từng cụm; không gán tên “nguy cơ rời bỏ”.
34. **Proxy khách doanh nghiệp/giá trị lớn được tính ra sao?** Monetary hoặc giá trị đơn lớn nhất đạt phân vị 99 trên dev; đây là proxy giá trị, không phải xác minh loại hình pháp lý.
35. **Tại sao có temporal cross-validation?** Cần mô phỏng dự đoán tại T bằng dữ liệu cũ, giữ khoảng cách nhãn N+L và tránh để nhãn tương lai lấn qua T validation.
36. **Nếu dưới 100 mẫu dương hoặc dưới 5% thì sao?** Chỉ dùng temporal CV và bootstrap CI, ghi rõ độ tin cậy thấp và không kết luận mạnh.
37. **Nếu dưới 30 mẫu dương thì sao?** Dừng trước classifier; báo thiếu lực dữ liệu và đề xuất đổi sang câu hỏi có đơn thứ hai trong cửa sổ cố định 180 ngày kể từ đơn đầu để chủ dự án duyệt.
38. **Min_support được chọn thế nào?** Thử 0,5%, 1%, 2%, 3%, 5%; chọn mức cao nhất còn ít nhất 5 luật có lift>1 và xuất hiện ít nhất 5 giỏ để hạn chế luật quá thưa.
39. **Giá combo có dùng discount/giá vốn không?** Không. Giá gộp dựa trên retail_price quan sát được; adjustment ở mức đơn không phân bổ xuống sản phẩm và không có giá vốn để tính lợi nhuận.
40. **Vì sao bỏ DBSCAN địa lý?** Chỉ có tỉnh/thành, không có tọa độ hoặc mã vùng đủ chi tiết để đo khoảng cách địa lý đáng tin.
41. **Các nhãn quay lại có phải nhãn test không?** Không. Tất cả mẫu, nhãn và độ đo hiện tại đều ở tập phát triển; test chưa mở.
42. **Độ tin cậy còn giới hạn gì?** Status hiện tại không khôi phục lịch sử hoàn/đổi; khách một đơn chiếm đa số; quy tắc tiền được đổi sau cổng cũ; mô hình chỉ có temporal validation trong lịch sử dev.
43. **Có thể diễn giải kết quả là quan hệ nhân quả hay lợi nhuận không?** Không. Luật giỏ chỉ là đồng xuất hiện; mô hình là dự báo dev; không có giá vốn để tính lợi nhuận.
44. **Bước tiếp theo là gì?** Chủ dự án xem kết quả Ngày 2 và chọn phương án. Chỉ sau khi có lệnh “ok” mới mở test một lần theo cấu hình đóng băng; chưa bắt đầu Ngày 3.
'''
    qa_path.write_text(qa.rstrip() + "\n" + day2_qa, encoding="utf-8")

    day3 = f'''# Đầu vào dự kiến cho dashboard Ngày 3

Danh sách dưới đây dùng đầu ra đã rà PII. Mã khách trong bảng khách là HMAC giả danh; không có order_id, tên khách, điện thoại hoặc địa chỉ. Hình hiện là bản phát triển; chưa có chỉ số test.

- `outputs/tables/segments.csv` — một dòng/khách: `customer_key` (giả danh), `cluster_id`, `cluster_name`, `rule_segment`, `business_like_proxy`, Recency, Frequency, Monetary, giá trị đơn TB/lớn nhất, số lượng, số sản phẩm phân biệt, khoảng cách mua trung bình, tháng đơn đầu, khoảng cách holiday, tỉnh/thành đã chuẩn hóa, tỷ lệ adjustment dương/âm, tỷ trọng doanh thu cụm. Nguồn: feature snapshot trước `test_start`.
- `outputs/tables/segment_profiles.csv` — mỗi cụm: quy mô, Recency/Frequency/Monetary và giá trị đơn trung bình/trung vị, số proxy giá trị lớn, Monetary gộp và tỷ trọng. Dùng cho thẻ/phân tích cụm.
- `outputs/tables/rules.csv` — `antecedent_products`, `consequent_products`, combo, support, confidence, lift, số giỏ xuất hiện, giá niêm yết gộp nếu đủ giá. Không có khóa khách/đơn.
- `outputs/tables/combos.csv` — combo duy nhất cùng tên sản phẩm, số lần, độ đo luật, giá niêm yết gộp và ghi chú chất lượng.
- `outputs/tables/money_diagnosis.csv` — pattern tiền, phân vị/tổng price adjustment và tỷ lệ theo tháng; chỉ số tổng hợp không có mã giao dịch.
- `outputs/metrics/day2_money_audit.json`, `day2_label_audit.json`, `day2_segmentation.json`, `dev_final_model.json`, `day2_baskets.json` — metadata/phạm vi, counts, độ đo dev, ngưỡng và trạng thái không mở test; dashboard chỉ đọc trường tổng hợp cần thiết.
- `outputs/figures/segments_elbow.png`, `segments_silhouette.png`, `decision_tree_depth_curve.png` — hình đánh giá K và độ sâu cây trên dev.

Không đọc `outputs/tables/day2_label_samples_*.csv` vào dashboard chung vì có nhãn phát triển theo khách; không đọc `outputs/models/day2_dev_final_model.joblib` trong dashboard. Không có đầu vào test. Trước khi dashboard Ngày 3, cần chốt sau khi chủ dự án xem báo cáo Ngày 2 và có lệnh “ok” riêng cho mở test một lần.
'''
    (ROOT / "docs" / "day3_inputs.md").write_text(day3, encoding="utf-8")

    progress = f'''# Project progress

Updated: 2026-10-25

## Locked scope and active decisions

- Snapshot `20261024T052943Z`, 12,011 orders; `split.yaml` and `split.lock.json` remain unchanged: N=180, L=7, W=180, test `[2025-10-22,2026-04-20)`, `DATA_CUTOFF=2026-10-24` exclusive. Amendment 01 remains `analysis_start=2024-04-01`; `N=365,W=365` remains infeasible; `H_obs=[analysis_start,T)`.
- Amendment 02 remains immutable history. Amendment 03 is active and hash-verified. The owner replaced the old 5% gate after observing 701/6,400 (10.95%), based on business knowledge that status 3 is recognized revenue and price differences can be fees/promotions. This was not based on labels/test behavior. Evidence is 13-order manual review plus verbal owner confirmation; `dash_*` remains blank.
- New money audit: {money['scope']['status3_orders']} status-3 dev orders; {money['gifts']['count']} gifts; {money['negative_revenue']['count']} negative recognized-revenue orders ({percent(money['negative_revenue']['rate'])}); 1% stop gate {('failed' if money['stop_gate_failed'] else 'passed')}. `price_adjustment` is retained; payment fields do not filter orders.

## Day 2 completed

- Preprocess: {prep['missing_customer_id_orders']} missing-customer orders excluded from customer-level features; {prep['gift_orders']} gifts excluded from customer behavior; {prep['orders_without_line_items']} no-line orders excluded from baskets. Dev label cohort: {labels['customer_samples']} unique customers, {labels['positive_samples']} positive ({percent(labels['positive_rate'])}); test labels and behavior were not loaded.
- Segmentation: K={segments['chosen_k']}, silhouette={segments['chosen_silhouette']:.3f}, single-order customers={percent(segments['single_order_customer_rate'])}. Profiles and A/B sensitivity are in `outputs/metrics/day2_segmentation.json`.
- Classifier: best={model['best_model']}, PR-AUC={model['best_model_oof_metrics']['pr_auc']:.4f}, ROC-AUC={model['best_model_oof_metrics']['roc_auc']:.4f}; temporal folds are customer-disjoint and all preprocessing fit inside train folds. Model is development-only.
- Baskets: {baskets['eligible_product_baskets']} product baskets eligible, {baskets['rule_count']} rules and {baskets['combo_count']} combos. No cost/profit calculation was made.
- Summary, walkthrough, FAQ and Day3 input inventory are present. Day 3 has not started; test remains unopened pending explicit “ok”.

## Audit / runner

- `scripts/run_all.py` now verifies locks and GET-only policy, scans PII, runs pytest, profiles/reuses the development warehouse, checks amendment-03 money gate, and executes Day 1/Day 2 notebooks. It stops at the approved negative-revenue gate if it fails. Final PII scan is required.
- Pre-label evidence sealed in amendment 03 records two `eligibility_count` entries, zero test-label and test-behavior reads, and Day 1 artifacts with `test_labels_loaded=false`. Day 2 uses dev labels only.
'''
    (ROOT / "docs" / "PROGRESS.md").write_text(progress, encoding="utf-8")
    print("Day 2 summary, walkthrough, QA, Day 3 input inventory, and PROGRESS were refreshed from aggregate metrics.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
