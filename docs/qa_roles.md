# Phân vai hỏi đáp

Hai thành viên đều phải nắm toàn bộ dự án. Phân vai để câu trả lời gọn, người còn lại bổ sung khi cần.

| Chủ đề | Trả lời chính | Bổ sung |
|---|---|---|
| Bài toán, kiến trúc 5 tầng, Star Schema, DuckDB/Spark | Thành viên A | Thành viên B nêu schema và quy mô |
| Snapshot, ETL, DQ, HMAC, bảo mật | Thành viên B | Thành viên A nêu mốc lọc và hash |
| Status 3, công thức tiền, `price_adjustment`, amendment 03 | Thành viên A | Thành viên B nêu độ nhạy A/B |
| Phân khúc quy tắc/K-Means, khách doanh nghiệp proxy | Thành viên B | Thành viên A nêu rõ proxy không xác minh pháp nhân, RFM chỉ mô tả lịch sử trước T |
| Mua lại DEV/test, CI, tín hiệu và không dừng | Thành viên A | Thành viên B nhắc không chọn lại sau test |
| Luật kết hợp, gift line, mùa vụ, combo | Thành viên B | Thành viên A nhấn mạnh đồng xuất hiện, không nhân quả |
| Cổng hủy/hoàn, nhật ký amendment, khóa test | Thành viên A | Thành viên B giải thích `test_opened.lock.json` |
| Hạn chế, cách chạy, bàn giao | Thành viên B | Thành viên A chạy lệnh an toàn |

## Quy tắc trao đổi

Ở phần mua lại, tên vai trò dùng thống nhất: **Logistic Regression C=10 — mô hình chính theo D-005**; **Logistic Regression feature-v2 C=0,1 — khảo sát bổ sung theo Amendment 04; không thay mô hình chính**. Cấu hình ghi >T, evaluator dùng [T,end) (gồm ngày T); ảnh hưởng chưa xác định; đây là kết quả số liệu của lần chạy thực tế, không phải khẳng định tuân thủ đầy đủ giao thức, không gọi là 'đạt cổng ghi trước'.

- Người trả lời chính mở đầu bằng câu trực tiếp, sau đó nêu một số liệu và một giới hạn.
- Người còn lại chỉ bổ sung khi có câu hỏi phụ hoặc cần chỉ đúng file/hash.
- Nếu không nhớ số liệu, mở `docs/qa.md` hoặc metric tương ứng; không ước lượng.
- Không khẳng định lợi nhuận, nhân quả, khách doanh nghiệp đã xác minh, hay khả năng tổng quát hóa từ một cửa sổ test.
- Hạn nộp là 2026-10-27; thời lượng và rubric chính thức chưa có trong hồ sơ. Mỗi người tập trả lời ít nhất 10 câu thuộc phần của người kia.
