# Định nghĩa cohort và số lượng

Các số dưới đây đến từ manifest/tóm tắt aggregate đã có và kho DEV chỉ đọc. Chúng mô tả các universe khác nhau; không cộng/trừ để suy ra quan hệ hàng-ngang nếu chưa có đối soát được khóa.

| Cohort | Số lượng | Cửa sổ / bộ lọc | Nguồn và cách dùng |
|---|---:|---|---|
| Snapshot hiện hành | 12.011 đơn | Snapshot `20261024T052943Z`, 601 trang; toàn bộ khoảng ngày nguồn | `outputs/tables/day1_analysis_start_profile.json`, `docs/api_notes.md`; số manifest, không đọc raw pages trong giai đoạn này |
| Trước ngày bắt đầu phân tích | 476 đơn | Trước `2024-04-01`; retained trong raw nhưng loại khỏi hành vi | `outputs/tables/day1_analysis_start_profile.json`, `docs/data_gap_report.md`; theo xác nhận chủ cửa hàng tại D-014 |
| Development warehouse | 6.517 đơn | `2024-04-01 <= local_date < 2025-10-22`; status gồm 3, 5, 6 | `data/restricted/xoaif_dev.duckdb` qua kết nối read-only; 6.517 dòng, không có ngày ngoài cửa sổ |
| Đơn mua hợp lệ DEV | 6.400 đơn | Status 3 trong cửa sổ DEV | Kho DEV; status 3 là quy ước hợp lệ tại D-013 |
| Khách có ít nhất một đơn status 3 DEV | 5.174 khách | Distinct customer key không thiếu, status 3, trước T | `outputs/tables/day1_development_cohort_summary.json` và `outputs/tables/dev_quality_summary.json`; chỉ dùng số distinct tổng hợp |
| Eligibility preflight N=180 | 5.499 khách | Candidate `2025-10-22`, quy tắc eligibility đã khóa; đây là kết quả preflight, không phải nhãn hay hành vi test | `outputs/tables/eligibility_preflight.csv`; chỉ đọc dòng aggregate preflight |
| Cohort scoring được chốt trước mở test | 5.169 khách | Khách có lịch sử mua đủ điều kiện trước T, loại đơn quà theo pipeline tiền xử lý đã khóa | `outputs/metrics/day2_segmentation.json` và `docs/day2_summary.md`; số tổng hợp pre-open, không dùng để dựng EDA DEV |
| Mẫu nhãn phát triển | 3.508 mẫu; 260 dương | Historical T từ 2024-05-01 đến 2025-04-01; feature orders trước từng T; nhãn mua lại trong `(T, T+180 ngày]`, N=180, L=7 | `outputs/metrics/day2_label_audit.json`; DEV only, tỷ lệ dương 7,41% |

## Cần giữ riêng

- 5.499, 5.174 và 5.169 đều là số khách nhưng đến từ nguồn, mốc và quy tắc khác nhau. Chưa giải thích được phần chênh lệch; xem [đối soát aggregate](cohort_reconciliation.md). Không gán nguyên nhân hoặc tự tái dựng row-level cohort.
- 6.517 là số đơn của warehouse DEV, còn 5.174 là khách duy nhất có đơn status 3. Chúng không cùng đơn vị.
- 3.508 là mẫu supervised DEV qua nhiều mốc T; không phải toàn bộ khách scoring và không phải cohort test.
- EDA mới dùng warehouse trước T và bảng nhãn DEV. Không dùng hành vi/nhãn test hoặc bảng feature test để vẽ hình DEV.
