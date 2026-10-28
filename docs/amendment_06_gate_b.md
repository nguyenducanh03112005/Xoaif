# Báo cáo Gate B — 06-HO2 (nhãn vẫn đóng)

Ngày: 2026-10-28. Phạm vi: khóa giao thức, kiểm tra số lượng tiền T2 và độ chính xác kỳ vọng. Đây **không** phải báo cáo đánh giá HO2. Chưa chạy `scripts/evaluate_test_once.py`; không đọc nhãn, đơn hàng hay hành vi trong cửa sổ HO2.

## 1. Kiểm toán ranh giới dữ liệu

- Snapshot cố định: `20261024T052943Z`; T2 là `2026-04-20` theo `Asia/Ho_Chi_Minh`.
- Script `scripts/count_ho2_eligibility_preregistered.py` kiểm tra `inserted_at` trước. Chỉ nếu ngày địa phương nằm trong `[2024-04-01, 2026-04-20)` mới đọc status, quy tắc quà và mã khách để đếm. Hàng từ T2 trở đi bị bỏ ngay; không truy cập trường khác. Kiểm thử sentinel xác nhận helper chỉ gọi `get("inserted_at")`.
- Audit lần chạy tiền nhãn: 12.011 hàng được kiểm tra trường `inserted_at`; 9.257 hàng có ngày trước T2 trong phạm vi lịch sử; 0 trường outcome/label của HO2 đọc, 0 nhãn test cũ dùng để fit/chọn. Không ghi định danh, dòng đơn, hay nhóm nhỏ.
- Rà soát repo: không tìm thấy evaluator/artifact HO2 có trước giao thức; log test hiện hữu thuộc lần mở cửa sổ cũ. Đây là bằng chứng về hoạt động trong repo/runtime dự án được kiểm tra, không phải chứng minh pháp y cho mọi thao tác ngoài repo.
- Các bước WP5 trước đó dùng `load_dev_orders()` với cổng địa phương `<2025-10-22`; không đọc HO2. Lần đếm hiện tại là lần duy nhất kiểm tra `inserted_at` ở phạm vi mở rộng đến T2 và không xem nội dung khác của hàng từ T2 trở đi.

## 2. Cohort và độ chính xác kỳ vọng

Từ lịch sử hợp lệ trước T2 có **7.282 khách** đủ điều kiện: 988 khách frequency≥2 và 6.294 frequency=1. Đây là số mẫu có thể đánh giá ở T2 theo luật eligibility, không phải số khách có nhãn dương.

| Tham chiếu tỷ lệ nền | Dương kỳ vọng / n | Độ rộng CI 95% tỷ lệ nền (xấp xỉ) | H1: công suất nếu AUC thật 0,60 | H2: công suất nếu RR thật 2 |
|---|---:|---:|---:|---:|
| DEV 7,4% | 539 / 7.282 | 1,20 điểm % | 98,3% | 91,6% |
| Aggregate test cũ 4,6% | 335 / 7.282 | 0,96 điểm % | 91,2% | 75,3% |

H1 dùng xấp xỉ phương sai ROC-AUC Hanley–McNeil với số dương/âm kỳ vọng; CI thực khi được mở vẫn dùng bootstrap theo khách đã khóa. H2 dùng xấp xỉ Wald trên log risk ratio, group size 988/6.294; tỷ lệ hai nhóm được suy từ tỷ lệ nền tham chiếu và RR giả định để giữ tỷ lệ tổng. Các kịch bản không phải dự báo và không bảo đảm công suất thực tế.

**Điều chỉnh trước khóa:** H2 được hạ từ chính xuống phụ vì công suất tại tham chiếu 4,6% và RR=2 khoảng 75,3%, dưới mốc quy ước 80%. Không nới ngưỡng RR 1,5. H1 là giả thuyết chính duy nhất, kiểm định một phía α=0,05 (Holm family còn một giả thuyết). Tại AUC thật 0,60, công suất xấp xỉ 91,2% ở mốc nền 4,6%; ở hiệu ứng sát ngưỡng, công suất thấp hơn. Không tuyên bố H1 chắc chắn có đủ lực cho mọi AUC>0,55.

H6 **không kiểm định**: cohort 180 ngày trưởng thành cuối của DEV là 2025-03; ngoại suy đến T2 trở đi vượt một năm. Artifact aggregate hiện có không cung cấp chuỗi/bootstrap theo khách để tạo dải xu hướng đáng tin cho cả AOV, đơn/khách, khách mới/tháng và tỷ lệ mua lại khách mới. Không thay bằng khoảng DEV tĩnh.

## 3. Tập chiến lược và tiêu chí đã khóa

- Giữ D-005 và v2 theo hai artifact mô hình đóng băng có sẵn; giữ các chiến lược quy tắc S1, S3, S6 với mã/recipe trong kế hoạch WP5b/WP5c. RFM/phân khúc và 24 combo đóng băng theo artifact hiện hữu.
- Loại v3, recency-only và frequency-only khỏi chấm HO2: WP5 chỉ lưu các fit theo temporal-CV, chưa có một artifact final-fit cùng quần thể fit cố định. Không tự tạo artifact sau khi khóa để lách giới hạn.
- Không chọn ứng viên; WP5b không chọn. Không fit/tuning/ngưỡng hóa theo nhãn HO2. Các chiến lược được liệt kê không đồng nghĩa đã chọn mô hình kinh doanh.

**H1 chính:** D-005 ROC-AUC >0,55; đạt nếu cận dưới một phía 95% (bootstrap khách, 2.000 lần, seed 20261028) >0,55.

**Phụ:** H2 risk ratio frequency≥2/frequency=1 >1,5; H3 S1/S3/S6 cận dưới lift top-decile >1 và cận dưới precision@10% > tỷ lệ nền; H4 chiều xếp hạng S6/RFM so với DEV; H5 ít nhất 1/24 combo vượt lift>1, Kulczynski≥0,5, IR≤0,5. H2–H5 không điều chỉnh để tuyên bố xác nhận. H6 không kiểm định. Tỷ lệ nền và calibration-in-the-large chỉ mô tả.

## 4. Hash protocol/config/mô hình

Lock `config/amendment_06_ho2.lock.json` chứa SHA-256 của protocol, config, các mã nguồn/metric DEV được viện dẫn, các artifact mô hình và bảng aggregate đóng băng. Các hash chính:

| Artifact | SHA-256 |
|---|---|
| Protocol `docs/analysis_plan_amendment06_ho2.md` | `CD9197008D6B41F07DF51F117886DFD883E7234B514BAFEFDDBD3182B31584A8` |
| Config `config/amendment_06_ho2.yaml` | `E850AF1E85179EBB2C3598FB7F78ADB5FD1051E53A80B4473BC0C8300AD97B4C` |
| D-005 `outputs/models/day2_dev_final_model.joblib` | `0AC767D24C641F50BDB19634E590DC45A92D9E4CD5513D02871FAC50B109CD4A` |
| v2 `outputs/models/repurchase_features_v2.joblib` | `5CBE48BB9B4944D91DFBA7B85DD5D1608B68574B16D3AC6A6319F8A2F80` |
| RFM `outputs/models/segmenters_dev_frozen_v1.joblib` | `5BABAA2352921F840385BDFE6681948F329B0EE276DE2AEF1CC8500C9146B93F` |
| Combos `outputs/tables/combos_v2.csv` | `AE7DF8760857A9A7AA2CD667704829E71B076A70B5CA2F0A41FD6396EF0538D6` |

## 5. Trạng thái cổng

Gate B bàn giao gồm protocol, config/lock, số đếm/công suất kỳ vọng, quyết định H2/H6, audit ranh giới và commit riêng. Trạng thái Git phải sạch sau commit. **HO2 vẫn đóng. Phase C chưa bắt đầu.** Cửa sổ chỉ được mở khi chủ dự án gửi đúng cụm từ trong protocol.
