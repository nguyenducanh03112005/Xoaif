# Định nghĩa cohort và số lượng

Các số dưới đây đến từ manifest/tóm tắt aggregate đã có và kho DEV chỉ đọc. Chúng mô tả các universe khác nhau; không cộng/trừ để suy ra quan hệ hàng-ngang nếu chưa có đối soát được khóa.

| Cohort | Số lượng | Cửa sổ / bộ lọc | Nguồn và cách dùng |
|---|---:|---|---|
| Snapshot hiện hành | 12.011 đơn | Snapshot `20261024T052943Z`, 601 trang; toàn bộ khoảng ngày nguồn | `outputs/tables/day1_analysis_start_profile.json`, `docs/api_notes.md`; số manifest, không đọc raw pages trong giai đoạn này |
| Trước ngày bắt đầu phân tích | 476 đơn | Trước `2024-04-01`; retained trong raw nhưng loại khỏi hành vi | `outputs/tables/day1_analysis_start_profile.json`, `docs/data_gap_report.md`; theo xác nhận chủ cửa hàng tại D-014 |
| Development warehouse | 6.517 đơn | `2024-04-01 <= local_date < 2025-10-22`; status gồm 3, 5, 6 | `data/restricted/xoaif_dev.duckdb` qua kết nối read-only; 6.517 dòng, không có ngày ngoài cửa sổ |
| Đơn mua hợp lệ DEV | 6.400 đơn | Status 3 trong cửa sổ DEV | Kho DEV; status 3 là quy ước hợp lệ tại D-013 |
| Khách có ít nhất một đơn status 3 DEV | 5.174 khách | Distinct customer ID không NULL, ít nhất một status 3 trong `[2024-04-01, 2025-10-22)` | Đếm trực tiếp từ snapshot bằng HMAC chuẩn, khớp DuckDB read-only; `docs/cohort_reconciliation.md` |
| Eligibility preflight N=180 | 5.499 khách | Candidate `2025-10-22`; có ít nhất một đơn status 3 có ID trước T, không có cận dưới `analysis_start` | Đếm trực tiếp từ snapshot, khớp `outputs/tables/eligibility_preflight.csv`; không phải nhãn hay hành vi test |
| Cohort scoring được chốt trước mở test | 5.169 khách | Khách trong B còn ít nhất một đơn status 3 DEV không quà theo Amendment 03 | Đếm trực tiếp bằng `assess_order_money`; khớp `outputs/metrics/day2_segmentation.json`; xem `docs/cohort_reconciliation.md` |
| Mẫu nhãn phát triển | 3.508 mẫu nhãn qua nhiều mốc T; 260 dương | Historical T từ 2024-05-01 đến 2025-04-01; feature orders trước từng T; nhãn mua lại trong `(T, T+180 ngày]`, N=180, L=7 | `outputs/metrics/day2_label_audit.json`; DEV only, tỷ lệ dương 7,41% |

## Quy ước mẫu số và cầu nối

- 12.011 là tổng đơn trong snapshot nguồn, không phải cohort phân tích. 476 đơn trước `analysis_start` và 6.517 đơn DEV là các phạm vi lọc riêng; không dùng tổng snapshot để suy ra số đơn/khách thuộc split hoặc nhãn.
- 6.517 là mọi đơn có `local_date` trong `[2024-04-01, 2025-10-22)` (mọi status). 6.400 là tập con status 3, kể cả 286 đơn thiếu customer ID. 5.174 là khách distinct có ID với ít nhất một đơn status 3 trong cùng cửa sổ; đơn thiếu ID không tạo khách.
- Eligibility A có cận dưới mở: status 3 có ID trước `2025-10-22`, không áp `analysis_start`. B là A sau khi áp cận dưới `2024-04-01`; vì vậy 325 khách A−B chỉ có đơn status 3 trước ngày bắt đầu. Scoring tiếp loại 5 khách B chỉ có đơn quà; giữ nguyên khách có đơn không quà dù thiếu item lines. Cầu nối `5.499 − 325 − 5 = 5.169`, dư chưa giải thích `0`.
- 3.508 là số **mẫu khách–T**, không phải số đơn hoặc số khách scoring. Mỗi khách chỉ được gán một T lịch sử theo quy tắc preflight; có 12 candidate T. Feature dùng đơn trước T. Label DEV hiện hành dùng đơn status 3 không quà trong `(T, T+180 ngày]`, tức loại ngày T và gồm ngày cuối cửa sổ; không đồng nhất định nghĩa này với cửa sổ thực thi của lần test.

## Cần giữ riêng

- Cầu nối đã đếm trực tiếp: 5.499 khách trước T trừ 325 khách chỉ có status 3 trước `analysis_start` bằng 5.174 khách B; trừ tiếp 5 khách B chỉ có đơn quà bằng 5.169 khách scoring. `phần dư chưa giải thích: 0`. Mốc 476 đơn bán thử thuộc giai đoạn 2022-06-04 đến 2022-09-21; 325 khách A−B có ít nhất một đơn trong giai đoạn đó. Chi tiết ở [đối soát cohort](cohort_reconciliation.md).
- 6.517 là số đơn của warehouse DEV, còn 5.174 là khách duy nhất có đơn status 3. Chúng không cùng đơn vị.
- 3.508 là số mẫu nhãn supervised DEV qua nhiều mốc T; không phải số khách scoring hoặc cohort test.
- EDA mới dùng warehouse trước T và bảng nhãn DEV. Không dùng hành vi/nhãn test hoặc bảng feature test để vẽ hình DEV.
