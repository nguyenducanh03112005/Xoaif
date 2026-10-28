# Nhật ký amendment hậu mở test

Ngày cập nhật: 2026-10-28. Các mục dưới đây được chủ dự án phê duyệt theo D-024, sau D-022. Chúng bổ sung kiểm tra và tài liệu; không thay đổi kết quả test đã mở.

| Amendment | Ngày | Lý do và phạm vi được duyệt | Ảnh hưởng / ranh giới |
|---|---|---|---|
| 06 — Probe metadata Pancake | 2026-10-28 | Khảo sát 5 endpoint GET allowlist, tối đa 500 bản ghi mẫu/endpoint chỉ trong RAM; chỉ xuất metadata và aggregate HMAC-match. | Không ingest, không đổi field allowlist, không dùng endpoint có chi tiết khách/ghi chú/point logs; không ghi giá trị bản ghi, API key hay header xác thực. |
| 07 — Đối soát cohort và chất lượng DEV | 2026-10-28 | Giải thích cầu nối cohort; điều tra UNKNOWN tỉnh/thành; tổng hợp kênh đơn; đo cận nhạy ngày T chỉ trên DEV. | Không sửa split/lock/evaluator test; không nạp lại test. Không khôi phục biểu đồ tỉnh khi chưa có mapping đã xác minh. |
| 08 — Khảo sát phân cụm và lịch thời gian DEV | 2026-10-28 | Bổ sung RFM K=3..5 và lịch lễ/Tết/sale thủ công; đánh giá đặc trưng thời gian bằng rolling-origin DEV. | Không thay mô hình chính hoặc kết luận test. Lịch sale 2024–2025 là proxy giả định; silhouette không xác nhận ý nghĩa kinh doanh. |
| 09 — Refresh an toàn và trạng thái dashboard | 2026-10-28 | Thêm replay cục bộ có manifest/hash; mặc định chặn live refresh vì chưa xác minh hợp đồng `updated_at`; dashboard nêu snapshot khóa và tình trạng refresh. | Không chạy replay, không gọi API, không ghi vào `data/raw`; dashboard chỉ đọc aggregate local. Nút reload không tạo dữ liệu mới. |
| 10 — Đồng bộ hồ sơ bàn giao | 2026-10-28 | Đồng bộ số chuẩn, QA, speaker notes, tài liệu ôn vấn đáp và PDF từ các nguồn aggregate đã có. | Chỉ tài liệu/đầu ra aggregate; không PPTX, không dữ liệu cá nhân, không mở lại test. Bản PDF được dựng lại ở bước bàn giao cuối. |

## Giới hạn phê duyệt

- D-022 vẫn ghi đúng lịch sử: chẩn đoán anchor ban đầu chưa được duyệt và không được chạy. D-024 phê duyệt riêng khảo sát lịch thời gian rolling-origin chỉ trên DEV; đây không phải đánh giá trên test.
- `config/split.yaml`, split/test locks, Amendment 01–05 và các artifact test đóng băng tiếp tục bất biến.
- Không ingest dữ liệu Pancake ngoài đơn trước khi Claude duyệt endpoint và field allowlist.
