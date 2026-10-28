# F1 — thống nhất định nghĩa mua lại (DEV-only)

**Nhãn:** khám phá, chưa xác nhận ngoài mẫu. Kế hoạch được đăng ký trước ở `docs/analysis_plan_f1.md`, SHA-256 `9854ad2f25adb400a43cf86b5b646b1b18bf7770342a1b4b0fd13644fec16518`. Nguồn là `load_dev_orders()` và script mới `scripts/analyze_repeat_definition_f1.py`; chỉ đơn hợp lệ status 3, không quà, local date < 2025-10-22. Không đọc dữ liệu test.

## Định nghĩa thống nhất

Khách được tính mua lại khi có đơn status 3 không quà ở **ngày địa phương sau ngày đơn hợp lệ đầu tiên**. Hai hay nhiều đơn được tách trong cùng ngày không tạo sự kiện mua lại. Phân tích trước ghi 397 khách có đơn thứ hai trong 180 ngày; trong cohort trưởng thành 180 ngày có 34/397 khách với đơn thứ hai cùng ngày. Theo định nghĩa mới, 365 khách có ngày mua sau trong cùng cohort 3.508 khách. Trong toàn DEV, 53 khách có đơn thứ hai cùng ngày ở bất kỳ thời điểm nào; đây là mẫu số rộng hơn cohort 180 ngày trưởng thành.

## Vì sao Kaplan–Meier ngày 30 là 6,64% nhưng retention 5,64%?

Hai khác biệt được tách riêng:

1. **Định nghĩa sự kiện:** Kaplan–Meier cũ tính 34 đơn thứ hai cùng ngày như sự kiện ngày 0. Trên cùng 3.508 khách trưởng thành 180 ngày, KM 30 ngày cũ là 6,64%; bỏ cùng-ngày giảm còn 5,67% (chênh −0,97 điểm phần trăm). Khoảng tin cậy bootstrap theo khách cho bản cũ 5,84–7,50%, bản sau ngày 5,67% 4,90–6,47%.
2. **Mẫu số/cohort:** retention 30 ngày cũ gộp tất cả cohort tháng đủ 30 ngày, 4.524 khách, trong khi KM/CLV dùng tập cohort tháng đủ 180 ngày, 3.508 khách. Trên đúng tập 3.508 khách, retention 30 ngày với cùng định nghĩa ngày sau là 5,67% (199/3.508), khớp KM sau ngày tới sai số làm tròn. Retention tổng 5,64% (255/4.524) vẫn được giữ làm số lịch sử; không ghi đè.

| Kỳ hạn | KM cũ gồm cùng-ngày | KM mới chỉ ngày sau (95% CI) | Retention cùng cohort 3.508 khách | Retention A1 cũ đủ kỳ hạn |
|---:|---:|---:|---:|---:|
| 30 ngày | 6,64% | 5,67% (4,90–6,47%) | 5,67% (199/3.508) | 5,64% (255/4.524) |
| 60 ngày | 8,24% | 7,27% (6,44–8,12%) | 7,27% (255/3.508) | 7,19% (313/4.351) |
| 90 ngày | 9,44% | 8,49% (7,58–9,38%) | 8,49% (298/3.508) | 8,43% (350/4.154) |
| 180 ngày | 11,32% | 10,40% (9,38–11,49%) | 10,40% (365/3.508) | 10,40% (365/3.508) |

CI bootstrap KM dùng seed 20261028, 2.000 lần, resample khách. Retention cùng cohort ở bảng là tỷ lệ trực tiếp để minh họa tính tương thích; không thêm CI thứ hai vì CI KM cùng cohort đã thể hiện bất định.

## Đối chiếu A2 và WP5

A2 first-basket analysis có 3.635 khách trưởng thành theo thiết kế 180 ngày và 378 khách mua lại ở ngày sau, tỷ lệ thô 10,40%; mẫu khác với 3.508 khách của A1 do điều kiện dựng giỏ/sản phẩm và khóa cohort. Con số này không thay định nghĩa, nhưng nêu rằng cùng định nghĩa ngày địa phương sau đã áp dụng cho hành trình giỏ đầu. WP5 snapshot OOF là 14.394 snapshot/3.508 khách, 600 nhãn dương (4,17%); đây là nhãn theo từng mốc T và cửa sổ tương lai 180 ngày, không cùng đơn vị quan sát với retention một lần theo khách. Không so sánh tỷ lệ như thể cùng cohort.

## Kết luận

Chênh lệch A1 KM cũ–retention ngày 30 giải thích được bằng hai yếu tố quan sát trực tiếp: KM cũ tính cùng-ngày (khoảng −0,97 điểm khi loại) và KM dùng cohort đủ 180 ngày thay vì đủ 30 ngày. Với định nghĩa thống nhất và cùng cohort, retention/KM trùng nhau. Số cũ vẫn được lưu để truy vết; từ báo cáo F1 trở đi, “mua lại” nghĩa là ngày địa phương sau ngày mua đầu.
