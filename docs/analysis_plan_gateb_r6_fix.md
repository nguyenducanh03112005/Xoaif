# Đăng ký trước R6 — sửa độ bền số của H4

Ngày đăng ký: 2026-10-29. Gate B 06-HO2 vẫn đóng; không đọc nhãn, đơn hay hành vi HO2 và không chạy evaluator/dry-run.

## Mục tiêu và hiện trạng

Trong `scripts/evaluate_holdout2_once.py`, `_h4_eval` gọi `scipy.stats.spearmanr(...).statistic`, sau đó so sánh trực tiếp `rho >= thresholds[name]`. Chưa có dung sai số. Ngưỡng vẫn là S6 `0.9761904761904763` và RFM `1.0`, lấy từ kết quả tham chiếu DEV đã khóa. Điều kiện testable hiện yêu cầu ít nhất 4 nhóm chung.

Kiểm tra tổng hợp trước khi sửa dùng đúng `scipy.stats.spearmanr`: n=8 với một swap liền kề cho rho `0.9761904761904763` trong môi trường này; hai swap liền kề cho rho `0.9047619047619048`. n=6 identity cho rho `1.0`; một swap liền kề cho rho `0.942857142857143`. Công thức đóng `1 - 12/504` có thể được biểu diễn thành `0.9761904761904762` do cách làm tròn phép tính, nên ngưỡng so trực tiếp dễ phụ thuộc cách tạo số.

## Quy tắc đã đăng ký trước khi sửa mã

1. Dùng một dung sai tuyệt đối cố định `1e-9`: đạt nếu và chỉ nếu `rho >= threshold - 1e-9`.
2. Giữ nguyên hai ngưỡng đã khóa (`0.9761904761904763`, `1.0`); dung sai chỉ xử lý sai số biểu diễn dấu phẩy động, không đổi tiêu chí thực chất.
3. Giữ nguyên số nhóm tối thiểu 4. Nếu dưới 4 nhóm chung, H4 hệ tương ứng không testable.
4. Giữ nguyên ngưỡng tham chiếu dù HO2 có số nhóm chung khác 8/6; đây là giới hạn đã biết, không đổi trong lượt này.
5. Không đổi H1–H3/H5/H6, tập nhóm, cách tính Spearman, hay kết quả/đầu ra HO2. Không chạy evaluator hoặc dry-run.

## Kiểm thử tổng hợp đã định trước

- n=8, một swap liền kề: qua ngưỡng S6.
- n=8, hai swap liền kề: trượt ngưỡng S6.
- n=6, identity và rho đầu vào `1 - 1e-16`: qua ngưỡng RFM 1.0 nhờ dung sai.
- n=6, một swap liền kề: trượt ngưỡng RFM 1.0.
- Dưới 4 nhóm chung: không testable.

Chỉ dữ liệu tổng hợp được dùng cho các ca này. Các phép thử và kết quả xấu cũng được ghi trong báo cáo Gate B revision 3.
