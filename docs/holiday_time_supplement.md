# Khảo sát bổ sung: lịch lễ/Tết/sale và đặc trưng thời gian

## Mục tiêu và ranh giới

Đây là **khảo sát bổ sung** cho mô hình mua lại, không thay thế mô hình chính và không làm thay đổi lựa chọn/đánh giá đã báo cáo. Chương trình chỉ nạp `outputs/tables/day2_label_samples_primary.csv`, bảng nhãn DEV đã chuẩn bị; không đọc dữ liệu thô, vùng restricted, dữ liệu test, split/config/lock hay kết quả test. Mọi đánh giá là expanding rolling-origin trên DEV, không chọn siêu tham số hoặc đặc trưng.

Lệnh chạy từ thư mục gốc:

```powershell
.\.venv\Scripts\python.exe scripts\evaluate_holiday_time_dev.py
.\.venv\Scripts\python.exe -m pytest tests\test_holiday_time_supplement.py -q
```

Kết quả aggregate được ghi riêng tại `outputs/metrics/holiday_time_supplement_dev.json`; không ghi điểm theo khách hay pseudonymous key.

## Lịch thủ công

CSV `data/reference/vietnam_holiday_sale_calendar_2024-04_to_2026-10.csv` liệt kê các mốc trong khoảng **2024-04-01 đến 2026-10-31**. Các ngày Tết được đánh dấu bằng ngày mùng 1: 2025-01-29 và 2026-02-17. Ngày lễ cố định được neo theo Điều 112 Bộ luật Lao động 45/2019/QH14. Giỗ Tổ Hùng Vương sử dụng ngày được công bố trong lịch năm tương ứng. Mỗi dòng có URL nguồn và ghi rõ giả định.

Sale chỉ có các mốc proxy 11/11 và 12/12 cho 2024–2025. Nguồn Online Friday công bố marathon bán hàng 2026 từ 11/11 đến hết 12/12 và cao điểm Ngày Thương mại điện tử Việt Nam 12/12. Việc lùi các ngày cố định này cho 2024–2025 là **giả định lịch**, không xác nhận rằng cửa hàng hoặc một nền tảng cụ thể có chiến dịch bán hàng ngày đó. Không tạo mốc sau tháng 10/2026.

Nguồn công khai được tham chiếu:

- [Bộ luật Lao động 45/2019/QH14 trên Cổng văn bản Chính phủ](https://vanban.chinhphu.vn/?pageid=27160&docid=198540), Điều 112.
- [Lịch nghỉ lễ Việt Nam 2024](https://www.officeholidays.com/countries/vietnam/2024), [2025](https://www.officeholidays.com/countries/vietnam/2025), [2026](https://www.officeholidays.com/countries/vietnam/2026) — nguồn lịch công khai thứ cấp, dùng cho ngày lễ âm lịch và ngày mùng 1 Tết 2026.
- [Thông tin bắn pháo hoa Tết Giáp Thìn 2024](https://xaydungchinhsach.chinhphu.vn/danh-sach-cac-diem-ban-phao-hoa-tai-tp-hcm-dip-tet-nguyen-dan-giap-thin-2024-119240125193656008.htm) và [Tết Ất Tỵ 2025](https://xaydungchinhsach.chinhphu.vn/danh-sach-cac-diem-ban-phao-hoa-dip-tet-duong-lich-2025-va-tet-nguyen-dan-at-ty-tai-ha-noi-119241230172030261.htm) — nguồn để đối chiếu ngày bắt đầu năm âm lịch.
- [Online Friday 2026](https://www.onlinefriday.vn/) — nguồn về ngày thương mại điện tử 12/12 và lịch marathon 11/11–12/12/2026.

Ngày được lưu thủ công, không tải lịch từ API hay sinh ngày lễ bằng thuật toán lịch âm. Các nguồn được đối chiếu ngày 2026-10-28.

## Đặc trưng và đánh giá

Với ngày neo `as_of` và `last_purchase_date`, script tạo cờ trùng ngày lễ/Tết/sale proxy, khoảng cách tuyệt đối tới mốc gần nhất theo từng nhóm, và chu kỳ tháng, thứ trong tuần, ngày trong năm (sin/cos). `last_purchase_date` phải đứng trước `as_of`. Những trường ngày thô chỉ dùng để dựng đặc trưng, không đưa trực tiếp vào estimator.

Hai bộ đặc trưng (gốc và bổ sung thời gian) dùng cùng một logistic regression cố định (`C=1`, class-weight balanced); imputer, scaler và encoder chỉ fit trong train của mỗi fold. Fold validation dùng từng anchor DEV sau warm-up; train chỉ gồm mẫu có `train_as_of + 187 ngày < validation_as_of`, tương ứng nhãn 180 ngày và gap 7 ngày theo quy tắc hiện hành. Khách giữa train/validation phải rời nhau.

Lần chạy hậu kiểm ngày 2026-10-28 ghi aggregate tại `outputs/metrics/holiday_time_supplement_dev.json`. Đầu vào có 3.508 mẫu DEV, năm fold rolling-origin có 1.558 dự đoán OOF gộp. Với feature set gốc, pooled ROC-AUC/AP lần lượt là **0,5279/0,0800**; thêm đặc trưng thời gian là **0,5181/0,0767**. ROC-AUC trung bình theo fold lần lượt là **0,5556/0,5261**, AP trung bình theo fold **0,1044/0,1038**. Bổ sung thời gian không cải thiện các metric đã báo cáo; đây chỉ là khảo sát bổ sung, không thay mô hình chính.

| Anchor validation | Train mẫu | Validation mẫu |
|---|---:|---:|
| 2024-12-01 | 227 | 392 |
| 2025-01-01 | 552 | 269 |
| 2025-02-01 | 807 | 256 |
| 2025-03-01 | 1.021 | 199 |
| 2025-04-01 | 1.232 | 442 |

## Giới hạn

- Chỉ có năm anchor rolling-origin có thể đánh giá sau khi đáp ứng độ trưởng thành nhãn và hỗ trợ hai lớp; mỗi fold có số mẫu dương khác nhau, nên metric có bất định cao.
- Lịch chỉ là đặc trưng theo ngày, không chứng minh nguyên nhân hay chương trình khuyến mại thực tế của cửa hàng. Đặc biệt, sale proxy 2024–2025 chưa được xác minh như sự kiện riêng của shop.
- Lịch trong CSV kết thúc 2026-10-31; mục đích là phạm vi mốc thời gian, không mở rộng dữ liệu nhãn/feature sau DEV.
- Không sử dụng kết quả supplement để chọn mô hình chính.
