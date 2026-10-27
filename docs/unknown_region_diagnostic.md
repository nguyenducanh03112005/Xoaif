# Chẩn đoán UNKNOWN theo tỉnh và nguồn (DEV only)

Phạm vi: đơn status 3 có local_date trong [2024-04-01, 2025-10-22), n=6.400. Đã dùng local_day, canonical_province, normalize_product_name và assess_order_money của dự án. Không in địa chỉ, giá trị nguồn/kênh, ID hay văn bản tự do; nhóm kênh được đặt nhãn số. Mọi ô dưới 5 được gộp/ẩn.

## Trường có mặt trong các đơn status 3 trước T

Tên trường/path được thấy: ads_source, customer.shop_customer_addresses, order_sources, order_sources_name, p_utm_source, shipping_address, shipping_address.address, shipping_address.district_id, shipping_address.district_name, shipping_address.full_address, shipping_address.marketplace_address, shipping_address.new_full_address, shipping_address.new_province_id, shipping_address.province_id, shipping_address.province_name.

Trường tỉnh dùng bởi pipeline là shipping_address.province_name. UNKNOWN trong feature mapping là province rỗng sau canonical_province; kết quả này mô tả đúng thiếu trường, không suy ra nguyên nhân nghiệp vụ.

| Trường nguồn/kênh | Giá trị không rỗng (đơn) | Thiếu/rỗng (đơn) |
|---|---:|---:|
| order_sources_name | 3.996 | 2.404 |
| order_sources | 3.996 | 2.404 |
| ads_source | 970 | 5.430 |
| p_utm_source | <5 (gộp/ẩn) | 6.400 |

## Tỷ lệ rỗng tỉnh/thành và doanh thu ghi nhận

- Đơn status 3 thiếu province_name: 5.860/6.400 = 91.56%.
- Tổng doanh thu ghi nhận DEV tính được: 2.628.354.091 VND qua 6.400 đơn; thiếu số tiền ghi nhận ở 0 đơn.
- Doanh thu nhóm thiếu province_name: 2.384.693.718 VND = 90.73% doanh thu DEV.
- Tỷ lệ 91,92% trong dashboard là phạm vi DEV+test. Số ở đây chỉ DEV, khác phạm vi và mẫu số; không coi là mâu thuẫn.

## Doanh thu theo nhóm nguồn/kênh (nhãn nhóm đã ẩn)

| Trường | Nhóm | Đơn | Tỷ trọng doanh thu DEV |
|---|---|---:|---:|
| order_sources_name | khác | <5 (gộp/ẩn) | ẩn |
| order_sources_name | nhóm 1 | 3.722 | 66.89% |
| order_sources_name | nhóm 2 | 273 | 3.33% |
| order_sources_name | thiếu trường | 2.404 | 29.78% |
| order_sources | khác | <5 (gộp/ẩn) | ẩn |
| order_sources | nhóm 1 | 273 | 3.33% |
| order_sources | nhóm 2 | 3.721 | 66.88% |
| order_sources | thiếu trường | 2.404 | 29.78% |
| ads_source | nhóm 1 | 927 | 15.91% |
| ads_source | nhóm 2 | 43 | 0.39% |
| ads_source | thiếu trường | 5.430 | 83.69% |
| p_utm_source | thiếu trường | 6.400 | 100.00% |

## Giao ô tỉnh rỗng × nguồn/kênh

| Trường nguồn/kênh | Tỉnh/thành | Nhóm ẩn danh | Đơn | Tỷ trọng doanh thu DEV |
|---|---|---|---:|---:|
| order_sources_name | missing | nhóm 1 | 3.232 | 58.80% |
| order_sources_name | missing | nhóm 2 | 244 | 2.87% |
| order_sources_name | missing | thiếu trường | 2.384 | 29.06% |
| order_sources_name | present | other | <5 (gộp/ẩn) | ẩn |
| order_sources_name | present | nhóm 1 | 490 | 8.10% |
| order_sources_name | present | nhóm 2 | 29 | 0.45% |
| order_sources_name | present | thiếu trường | 20 | 0.72% |
| order_sources | missing | other | <5 (gộp/ẩn) | ẩn |
| order_sources | missing | nhóm 1 | 244 | 2.87% |
| order_sources | missing | nhóm 2 | 3.231 | 58.79% |
| order_sources | missing | thiếu trường | 2.384 | 29.06% |
| order_sources | present | other | <5 (gộp/ẩn) | ẩn |
| order_sources | present | nhóm 1 | 29 | 0.45% |
| order_sources | present | nhóm 2 | 490 | 8.10% |
| order_sources | present | thiếu trường | 20 | 0.72% |
| ads_source | missing | nhóm 1 | 852 | 14.50% |
| ads_source | missing | nhóm 2 | 42 | 0.38% |
| ads_source | missing | thiếu trường | 4.966 | 75.85% |
| ads_source | present | other | <5 (gộp/ẩn) | ẩn |
| ads_source | present | nhóm 1 | 75 | 1.42% |
| ads_source | present | thiếu trường | 464 | 7.85% |
| p_utm_source | missing | thiếu trường | 5.860 | 90.73% |
| p_utm_source | present | thiếu trường | 540 | 9.27% |

Kết luận: [Chắc chắn] UNKNOWN tương ứng trường tỉnh/thành rỗng theo mapping hiện hành; trong DEV tỷ lệ đơn thiếu tỉnh là 91.56% và doanh thu ghi nhận của nhóm này chiếm 90.73%. [Chắc chắn] Các trường nguồn/kênh hiện diện được tổng hợp theo nhóm ẩn danh ở trên. Chưa kết luận nguồn/kênh nào gây thiếu tỉnh hoặc vì sao; không suy diễn nguyên nhân kinh doanh.
