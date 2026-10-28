# Kênh nguồn đơn theo tháng — DEV only

Phạm vi: 6.400 đơn status 3 có `local_date` trong `[2024-04-01, 2025-10-22)`, tổng hợp bằng DuckDB trong bộ nhớ từ snapshot khóa. Không dùng ngày test. Giá trị `order_sources_name` được ánh xạ sang nhãn kênh phổ biến; tên nguồn thô và các nhóm chưa nhận diện không được xuất. Ô có số lượng dưới 10 bị ẩn cùng tỷ lệ tương ứng.

Tổng thể: Facebook 3.722/6.400 (58,16%); thiếu trường 2.404/6.400 (37,56%); Instagram gộp với nguồn hiếm thành 274/6.400 (4,28%). Gộp bổ sung để không suy ngược ô nguồn hiếm dưới 10 từ tổng. Không tìm thấy nhãn Shopee/sàn tường minh trong giá trị `order_sources_name`; đây không phải bằng chứng rằng shop không có giao dịch trên sàn, vì tên nguồn khác/nhỏ đã được gộp.

| Tháng | Đơn status 3 | Facebook — số (tỷ lệ) | Thiếu — số (tỷ lệ) | Instagram + nguồn hiếm — số (tỷ lệ) |
|---|---:|---:|---:|---:|
| 2024-04 | 253 | ẩn bổ sung | 118 (46,64%) | <10 (ẩn) |
| 2024-05 | 370 | ẩn bổ sung | 126 (34,05%) | <10 (ẩn) |
| 2024-06 | 298 | ẩn bổ sung | 95 (31,88%) | <10 (ẩn) |
| 2024-07 | 261 | ẩn bổ sung | 96 (36,78%) | <10 (ẩn) |
| 2024-08 | 265 | ẩn bổ sung | 90 (33,96%) | <10 (ẩn) |
| 2024-09 | 274 | ẩn bổ sung | 98 (35,77%) | <10 (ẩn) |
| 2024-10 | 619 | 347 (56,06%) | 256 (41,36%) | 16 (2,58%) |
| 2024-11 | 504 | 288 (57,14%) | 201 (39,88%) | 15 (2,98%) |
| 2024-12 | 337 | 202 (59,94%) | 121 (35,91%) | 14 (4,15%) |
| 2025-01 | 317 | 236 (74,45%) | 69 (21,77%) | 12 (3,79%) |
| 2025-02 | 248 | 154 (62,10%) | 83 (33,47%) | 11 (4,44%) |
| 2025-03 | 571 | 268 (46,94%) | 276 (48,34%) | 27 (4,73%) |
| 2025-04 | 217 | 107 (49,31%) | 97 (44,70%) | 13 (5,99%) |
| 2025-05 | 272 | 133 (48,90%) | 120 (44,12%) | 19 (6,99%) |
| 2025-06 | 324 | 181 (55,86%) | 119 (36,73%) | 24 (7,41%) |
| 2025-07 | 249 | 152 (61,04%) | 85 (34,14%) | 12 (4,82%) |
| 2025-08 | 217 | 119 (54,84%) | 81 (37,33%) | 17 (7,83%) |
| 2025-09 | 261 | 140 (53,64%) | 98 (37,55%) | 23 (8,81%) |
| 2025-10 | 543 | 333 (61,33%) | 175 (32,23%) | 35 (6,45%) |

Tỷ lệ tháng dùng tổng số đơn status 3 của chính tháng làm mẫu số. Ở tháng có ô gộp dưới ngưỡng, ẩn thêm Facebook theo nguyên tắc complementary suppression để không suy ngược ô nhỏ bằng phép trừ. Nhãn kênh là nhóm phân loại tên nguồn trong bộ nhớ; không dùng như bằng chứng nguồn gây ra hành vi hay doanh thu.
