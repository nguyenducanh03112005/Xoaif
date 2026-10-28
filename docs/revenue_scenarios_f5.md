# F5 — cây động lực doanh thu và kịch bản độ nhạy (DEV-only)

**Nhãn:** khám phá, chưa xác nhận ngoài mẫu. Kế hoạch đăng ký trước `docs/analysis_plan_f5.md`, SHA-256 `ad318e2814a126aa897d67ee1bd334f3a851d06371420fdb75e517cd6106c4c5`. Nguồn DEV-only; chỉ cohort tháng đủ theo dõi 180 ngày; bootstrap theo khách 2.000 lượt, seed 20261028. Tất cả kịch bản ghi rõ **giả định minh họa, không phải dự báo, không phải lợi nhuận**.

## Cây số học mô tả

Trong 3.508 khách đủ 180 ngày thuộc 12 cohort tháng trưởng thành, doanh thu ghi nhận 180 ngày là 1.799.372.687₫ (95% bootstrap theo khách 1.657.307.798–1.963.634.118₫), tương ứng **512.934₫/khách** (472.437–559.759₫). Phân rã đồng nhất từ giao dịch: AOV 444.619₫ (410.812–484.816₫) × 1,154 đơn/khách (1,135–1,174) = 512.934₫. Đây là lịch sử mô tả, không dự báo CLV tương lai.

Đơn giao dịch đầu đóng góp 84,42% doanh thu 180 ngày (95% CI 78,42–88,50%); 87% nằm trong CI nhưng không phải điểm ước lượng. Revenue 180 ngày giữ các giao dịch tách trong cùng ngày; repeat rate chỉ tính phát sinh đơn ở ngày địa phương sau. Vì vậy tỷ lệ “đơn đầu” là theo giao dịch đầu, còn số đơn/khách và AOV trong identity gồm giao dịch tách cùng ngày. Hệ thức doanh thu vẫn khớp theo số giao dịch, nhưng không xem số đơn/khách là số lần mua lặp lại.

`outputs/tables/revenue_drivers_month_f5.csv` có từng cohort tháng: số khách, doanh thu phân bổ 180 ngày, CLV/khách, AOV, đơn/khách, tỷ lệ mua lại cùng CI bootstrap theo khách. Các cohort từ 2025-04 đến 2025-10 bị loại vì chưa đủ 180 ngày theo dõi.

## Kịch bản độ nhạy

| Thay đổi giả định | Thay đổi doanh thu 180 ngày cơ học | 95% CI bootstrap |
|---|---:|---:|
| Số khách mới +10% | +179,9 triệu ₫ | 165,7–196,4 triệu ₫ |
| AOV +5% | +90,0 triệu ₫ | 82,9–98,2 triệu ₫ |
| Repeat rate +1 điểm % | +15,6 triệu ₫ | 14,4–17,0 triệu ₫ |
| Repeat rate +3 điểm % | +46,8 triệu ₫ | 43,2–51,0 triệu ₫ |
| Repeat rate +5 điểm % | +78,0 triệu ₫ | 72,1–85,0 triệu ₫ |
| Giữ thêm 5 điểm % khách high-value | +41,5 triệu ₫ | 34,0–49,7 triệu ₫ |

Các phép tính giữ mọi yếu tố khác cố định. Repeat scenario giả định mỗi khách mua lại tăng thêm tạo đúng một đơn tại AOV DEV; high-value giữ thêm 5 điểm phần trăm khách theo nhóm high-value A1 (monetary DEV ≥830.000₫), dùng CLV180 trung bình quan sát 1.969.156₫ trong n=421 khách cohort trưởng thành. Không có dữ liệu chi phí, giá vốn, độ co giãn hay tính khả thi. CI chỉ phản ánh bất định lấy mẫu DEV quanh các đầu vào, không bao gồm bất định giả định hay nhân quả.

Theo các mức giả định đã chọn, +10% khách mới là đòn bẩy số học lớn nhất; +1 điểm phần trăm repeat là nhỏ nhất. Đây không phải ưu tiên thực thi đã được xác nhận. Hướng hành động thận trọng: đo nguồn khách mới trước khi tăng thu hút; kiểm tra AOV theo ngành hàng trước khi thử gợi ý bổ trợ; với repeat, thử nhắc chăm sóc có holdout và kiểm tra chi phí/liên hệ được đồng ý. Không diễn giải giá trị doanh thu tăng như lãi hay ROI.

## Kênh thu hút khách (chỉ phần có nguồn)

Aggregate A3 có nguồn kênh cho 3.996/6.378 đơn (62,64%). Theo nhóm khách first-order channel đã lưu: Facebook n=2.254, AOV 475.919₫ (CI 438.707–522.095₫), retention 180 ngày 11,67% (10,29–13,04%); Instagram + nguồn hiếm n=130, AOV 344.875₫ (286.625–419.281₫), retention 6,92% (3,08–11,54%); thiếu kênh n=1.257, AOV 361.998₫ (324.305–407.457₫), retention 8,51% (7,00–10,02%). Các giá trị lấy trực tiếp từ `outputs/tables/channel_behavior_dev.csv`; n<30 không có ở bảng. Đây là association quan sát; không đủ căn cứ kết luận kênh gây khác biệt hay hiệu quả chi phí.

## Nguồn và giới hạn

Script: `scripts/analyze_revenue_scenarios_f5.py`; outputs aggregate `outputs/metrics/revenue_scenarios_f5.json`, `outputs/tables/revenue_drivers_month_f5.csv`, `revenue_sensitivity_f5.csv`, `revenue_channel_f5.csv`. Chỉ một cửa hàng và một cửa sổ DEV; các cohort tháng cuối bị kiểm duyệt phải; không có giá vốn, chi phí thu hút, chi phí liên hệ hay dữ liệu chiến dịch. Không kết luận lợi nhuận, nhân quả hoặc hiệu quả.
