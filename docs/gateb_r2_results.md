# R2 — RR DEV và quyết định H2

Kế hoạch đăng ký trước: `docs/analysis_plan_gateb_r2.md`, commit `04351e5`; kết quả tính sau commit này, chỉ từ `load_dev_orders()` (DEV), không dùng test/HO2. Snapshot đa mốc 21.638 snapshot / 3.508 khách, N=180, khoảng đệm L=7; bootstrap cụm khách 2.000 lần, seed 20261028.

## RR mua lại theo frequency

| Nhóm tại snapshot T | Snapshot n | Khách duy nhất | Dương snapshot | Tỷ lệ snapshot |
|---|---:|---:|---:|---:|
| frequency=1 | 19.442 | 3.329 | 780 | 4,012% |
| frequency≥2 | 2.196 | 382 | 306 | 13,934% |

RR snapshot-weighted (frequency≥2 / frequency=1) = **3,473**; bootstrap 95% CI **[2,656; 4,520]**; 2.000/2.000 draw hợp lệ. Mọi snapshot của cùng khách được lấy cùng nhau trong bootstrap. Đây là liên hệ mô tả DEV, không phải tác động của việc tăng frequency.

## Bảng công suất tiền nhãn đầy đủ

Hai prevalence tham chiếu: DEV 7,4% (539/7.282 dương kỳ vọng) và aggregate test cũ 4,6% (335/7.282). Tính toán H1 dùng Hanley–McNeil, alpha một phía 0,025 bảo thủ cho bước đầu Holm; H2 dùng Wald log-RR, alpha 0,025, n nhóm cố định 6.294/988. Số dương/sự kiện là kỳ vọng theo kịch bản, không phải kết quả HO2.

### H1: công suất để cận dưới ROC-AUC > 0,55

| AUC giả định thật | DEV 7,4% | Mốc aggregate 4,6% |
|---:|---:|---:|
| 0,55 | 2,50% | 2,50% |
| 0,60 | 96,38% | 84,99% |
| 0,65 | 100,00% | 100,00% |
| 0,70 | 100,00% | 100,00% |

### H2: công suất để cận dưới RR > 1,5

| RR giả định thật | DEV 7,4% | Mốc aggregate 4,6% |
|---:|---:|---:|
| 1,500 | 2,50% | 2,50% |
| 2,000 | 85,70% | 64,43% |
| 2,500 | 99,99% | 99,23% |
| 3,000 | 100,00% | 100,00% |
| Cận dưới DEV: 2,656 | 100,00% | 99,87% |

**Quyết định theo quy tắc đăng ký:** cận dưới DEV 2,656 > 1,5; công suất tại giá trị này lớn hơn 80% ở cả hai mốc nền. Vì vậy **H2 trở lại giả thuyết chính**. H1 và H2 tạo họ Holm hai kiểm định; kiểm định có p nhỏ hơn dùng alpha 0,025, kế tiếp alpha 0,05. Chưa có giả thuyết nào được kiểm trên HO2.

## Giới hạn

Power là xấp xỉ theo số đếm tiền nhãn và prevalence tham chiếu. H2 RR DEV gộp snapshot nên khách có nhiều snapshot đóng góp nhiều hàng; CI dùng cluster bootstrap theo khách để phản ánh phụ thuộc trong khách. Kết quả DEV là khám phá, chưa xác nhận ngoài mẫu.
