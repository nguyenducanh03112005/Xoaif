# F3 — sàng lọc combo khuyến nghị (DEV-only)

**Nhãn:** khám phá, chưa xác nhận ngoài mẫu. Kế hoạch đăng ký trước `docs/analysis_plan_f3.md`, SHA-256 `c2ecdd207ecc50c692484c2fe778c6496e44d9045dadbfb3c9c4ce57375b1bc2`.

Giữ nguyên thứ hạng thảo luận 24 combo từ A2. Bộ lọc mới yêu cầu đồng thời DEV lift >1, Kulczynski ≥0,5 và imbalance ratio ≤0,5. Đây là sàng lọc mô वर्णात्मक để loại cặp có lift ≤1 hoặc đồng xuất hiện mất cân bằng; không phải chuẩn phổ quát hay bằng chứng bundle bán thêm. Trong 24 cặp, **1 cặp qua bộ lọc**; combo hạng 1 PORTCARD + CHẬU MOCHI không qua vì lift DEV 0,982 dù các thước đo balance khác đạt điều kiện. Không đổi rank cũ. Bảng từng điều kiện: `outputs/tables/combo_recommendation_screen_f3.csv`.

PORTCARD xuất hiện trong 2.472/3.635 giỏ đầu (68,01%) theo A2. Đây là sản phẩm phổ biến trong giỏ đầu, không chứng minh vai trò kéo khách hay tác động mua lại.

Phân tích 77 sản phẩm giỏ đầu là 77 phép so sánh mô tả. Nếu tiến hành 77 kiểm định độc lập với mức 5% trong trường hợp không có liên hệ thật, kỳ vọng xấp xỉ 3,85 (khoảng 4) kết quả dương giả. Phân tích A2 không đăng ký p-value/kiểm định cho các so sánh này; **không hiệu chỉnh Benjamini–Hochberg**, không gọi khác biệt là có ý nghĩa thống kê, và không diễn giải CI như kiểm soát family-wise error.

Nguồn số: script `scripts/build_combo_recommendation_f3.py` áp bộ lọc vào aggregate đã duyệt `outputs/tables/frozen_combo_supplement_dev.csv`; không đọc raw/test, không phát sinh xếp hạng mới.

