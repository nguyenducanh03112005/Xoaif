# Kết quả hiệu chuẩn DEV cho tiêu chí Gate B R4

**Khám phá, chưa xác nhận ngoài mẫu.** Không nạp nhãn, hành vi hay đơn HO2. Quy tắc và ngưỡng được đăng ký trước tại `docs/analysis_plan_gateb_r4.md` (commit `6737615`); số dưới đây được tính sau commit đăng ký.

- Nguồn: `scripts/calibrate_gateb_r4_dev.py`; đầu vào snapshot đa mốc DEV từ `load_dev_orders()` và bảng 24 combo đóng băng, chỉ đọc các cột DEV cần cho bộ lọc.
- Cohort: 21.638 snapshot / 3.508 khách, 12 mốc T; n là snapshot trừ khi ghi khác.
- S1 có điểm 1 (frequency≥2) ở 2.196/21.638 snapshot = 13,93%.
- H4 tham chiếu chia 6 mốc đầu (2024-05 đến 2024-10) và 6 mốc sau (2024-11 đến 2025-04), giữ mức có n≥30 mỗi nửa. S6 có 8 mức dùng được, `rho_dev_half=0,9762`; RFM có 6 mức, `rho_dev_half=1,0000`. Cả hai đạt điều kiện hiệu chuẩn đã đăng ký (ít nhất 4 mức; rho≥0,50). Khi đánh giá HO2, ngưỡng tương ứng là rho HO2 không thấp hơn các mức tham chiếu này; hiện chưa tính rho HO2.
- H5: 1/24 combo qua đồng thời bộ lọc DEV (`lift>1`, `Kulczynski≥0,5`, `IR≤0,5`), vì vậy H5 chỉ mô tả theo quy tắc đã đăng ký; không có ngưỡng xác nhận HO2.

Mức tham chiếu rho có ít nhóm (S6 8, RFM 6) và là tương quan thứ hạng trên tỷ lệ snapshot, không phải bằng chứng nhân quả. Tỷ lệ S1 cũng là mô tả, không phải hiệu quả chiến dịch.
