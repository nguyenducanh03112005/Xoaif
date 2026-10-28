# Kết quả đóng băng chiến lược Gate B R5

**Khám phá, chưa xác nhận ngoài mẫu.** Chỉ fit trên DEV; không chấm, nạp hay đọc HO2/test. Kế hoạch đã commit trước tại `docs/analysis_plan_gateb_r5.md` (commit `16c1714`).

Nguồn: `scripts/freeze_gateb_strategies_dev.py`; cohort DEV đa mốc 21.638 snapshot / 3.508 khách, 1.086 snapshot dương, 12 mốc T. Artifact `.joblib` và bảng S6 được giữ local/ignored; result chỉ lưu metadata, SHA-256, số dòng/cỡ mẫu và không chứa khóa hay mã khách.

| Chiến lược | Trạng thái Gate B | Quần thể fit / artifact |
|---|---|---|
| S1 | Đủ điều kiện; quy tắc mô tả | Không fit; score=1 khi frequency≥2. |
| S3 | Đủ điều kiện, phương án A | Final-fit toàn DEV đa mốc; cây depth=3, leaf=50, seed 20261028. SHA-256 `63e47afbe0a1ef73c01d0be2974c354d753a7299f3d1952146b91bd8b2d1706b`. |
| S6 | Đủ điều kiện, phương án A | `repurchase_wp5c_train_rates.csv` là mapping theo fold train, không phải full DEV. Mapping final được fit trên toàn DEV; 11 nhóm sau gộp, min n=100. SHA-256 `17af23fa3a84a40c357856271489badd6a1061fd15cac62ace1573627b64d048`. |
| D-005 | Đủ điều kiện; artifact cũ giữ nguyên | `outputs/models/day2_dev_final_model.joblib`, hash khớp amendment 04: `0ac767d24c641f50bdc19634e590dc45a92d9e4cd5513d02871fac50b109cd4a`. |
| v2 | Đủ điều kiện; artifact cũ giữ nguyên | `outputs/models/repurchase_features_v2.joblib`, hash khớp metadata đóng băng: `5cbe48bb9b4944d91dfba7b85dd5d1608eb836b68574b16d3ac6a6319f8a2f80`. |
| v3 | Đủ điều kiện, phương án A | Final-fit toàn DEV đa mốc, Logistic Regression C=10 balanced, lbfgs, 2000 iteration, seed 20261028. SHA-256 `fc04ee70693da1a1e16350b99acf80b335705000dac35ba67bde63ef9c5d348b`. |
| Recency-only | Baseline mô tả | Hệ số chuẩn hóa −0,46545; score tăng khi recency giảm. Không là giả thuyết. |
| Frequency-only | Baseline mô tả | Hệ số chuẩn hóa +0,42799; score tăng khi frequency tăng. Không là giả thuyết. |

Chiều của hai baseline được xác định theo dấu hệ số từ Logistic Regression đơn biến DEV đã đăng ký, không theo kết quả HO2. S3 và v3 sử dụng cùng phương án A như đã đăng ký; không dùng metric in-sample của các final-fit để đánh giá tổng quát. D-005 vẫn là mô hình chính. R5 không tạo metric HO2 và không mở Phase C.
