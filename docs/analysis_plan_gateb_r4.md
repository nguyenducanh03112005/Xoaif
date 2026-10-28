# Đăng ký trước Gate B R4 — tiêu chí H1–H5 và thứ hạng tie-aware

- **Ngày đăng ký:** 2026-10-28. Commit của kế hoạch phải đứng trước commit kết quả H4/H5. Giao thức không mở hoặc đọc nhãn HO2.
- **Phạm vi:** 06-HO2 theo revision 2; mọi số hiệu chuẩn ở đây chỉ DEV. H1/H2 là hai kiểm định chính theo kết quả R2; Holm step-down, một phía, family-wise α=0,05: p nhỏ nhất so với .025, p còn lại so với .05. H3/H4 phụ; H5 chỉ là mô tả nếu `k_DEV<4`; H6 không kiểm định.

## H1–H3

- **H1:** D-005 ROC-AUC >0,55; giữ CI bootstrap khách 95%. Câu diễn giải bắt buộc: “Đạt H1 không có nghĩa là lặp lại ROC-AUC test 0,70”. Báo `AUC_HO2 − 0,70` và CI bootstrap như chênh lệch mô tả, không phải giả thuyết.
- **H2:** RR tỷ lệ mua lại 180 ngày frequency≥2 / frequency=1 >1,5; RR DEV/công suất quyết định H2 là giả thuyết chính. Kiểm định HO2 nằm trong họ Holm hai giả thuyết.
- **Thứ hạng tie-aware:** với N khách và K=`ceil(0,10*N)`, sắp điểm giảm dần. Gọi `n_above` và `pos_above` là số khách/dương có điểm lớn hơn điểm cắt; `n_tie` và `pos_tie` là số khách/dương bằng điểm cắt; `q=(K-n_above)/n_tie`. `precision@10=(pos_above+q*pos_tie)/K`; không bốc thăm khách đồng điểm. Lift top-decile=`precision@10 / prevalence`. Dùng cùng phép tính trong mỗi bootstrap draw.
- **H3:** đúng 6 so sánh: S1/S3/S6 × {precision@10%, lift top-decile}. Cận dưới bootstrap khách 95% của precision@10 phải lớn hơn prevalence; cận dưới lift phải lớn hơn 1. Không hiệu chỉnh nhiều phép so sánh; chỉ hỗ trợ phụ, không gọi xác nhận. S1 là điểm nhị phân 0/1, tỷ lệ điểm 1 DEV cần ghi trong kết quả; S3/S6 có ít mức điểm nên ROC-AUC/decile chỉ mô tả, không dùng cho H3.

## H4 — độ ổn định thứ hạng

- S6 giữ 12 ô đã đăng ký WP5c: frequency `{1,2,>=3}` × recency `{<=30,31–90,91–180,>180}`. RFM dùng đúng hàm `rfm_action_group` của A1 với `high_value_cut=830000 VND`, không tái ước lượng cutoff. Một quan sát DEV là snapshot của một khách tại T; rate theo snapshot.
- Chia 12 T DEV theo thứ tự thành nửa đầu (6 T đầu) và nửa sau (6 T cuối). Chỉ giữ các ô/nhóm có n≥30 ở cả hai nửa, bằng tiêu chí n độc lập với nhãn. Tính Spearman giữa thứ hạng tỷ lệ mua lại của hai nửa riêng cho S6 và RFM; đây là ngưỡng tham chiếu `rho_dev_half` tương ứng.
- H4 có thể đánh giá cho một hệ nhóm khi có ít nhất 4 mức n≥30 ở cả hai nửa và `rho_dev_half≥0,50`. Nếu không, hệ đó chỉ mô tả. Khi mở HO2, chỉ xét các mức cố định nói trên có số khách feature-side n≥30; không chọn theo nhãn. Tính Spearman DEV-pooled so với HO2 trên giao các mức. Hệ nhóm đạt nếu `rho_HO2 >= rho_dev_half`; H4 tổng đạt khi cả S6 và RFM đều testable và đạt. Ngưỡng rho cụ thể được tính/ghi trong Gate B trước mở.

## H5 — combo đóng băng

- `k_DEV` là số trong 24 combo đóng băng vượt đồng thời `lift>1`, `Kulczynski>=0,5`, `IR<=0,5`; IR dùng công thức đã dùng trong F3: `abs(support_A-support_B)/(support_A+support_B-support_AB)`.
- Giỏ HO2 là một đơn địa phương trong `(2026-04-20, 2026-10-17]`, status 3, không phải đơn quà cấp đơn; loại dòng quà theo Amendment 05, gộp biến thể theo product ID, cần ≥2 product ID hàng hóa khác nhau. Chỉ đánh giá đúng các combo qua bộ lọc DEV; không khai phá combo mới.
- Nếu `k_DEV>=4`, H5 đạt khi ít nhất `ceil(k_DEV/2)` trong đúng tập đó cũng thỏa ba bộ lọc ở HO2. Nếu `k_DEV<4`, H5 chỉ mô tả và không là giả thuyết xác nhận. Combo có số đồng xuất hiện HO2<30 bị suppression và không được tính là qua bộ lọc; không in số đếm hoặc tên/pair riêng của ô bị ẩn.

## Bất định, an toàn và số phép so sánh

- Metric H1/H2/H3 và chênh lệch D-005–baseline: percentile bootstrap 2.000 cụm khách, seed 20261028; cùng khách được lấy lại cùng nhau. H1/H2 p-value bootstrap một phía được kiểm Holm theo family đã đăng ký.
- Không thêm subgroup, threshold search, model hay combo. H6 không test; prevalence và calibration-in-the-large chỉ mô tả. Mọi kết quả HO2 chỉ sau mở được duyệt riêng.
