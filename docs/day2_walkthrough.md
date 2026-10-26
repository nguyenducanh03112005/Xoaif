# Hướng dẫn đi lại Ngày 2

**[LỊCH SỬ — hướng dẫn trước khi mở test]** Các lệnh notebook dưới đây mô tả quy trình lịch sử, không chạy lại sau khi có khóa test. Trạng thái hiện hành và các bước an toàn nằm trong `docs/PROGRESS.md`.

Quy trình chỉ dùng status 3 thuộc `[2024-04-01,2025-10-22)`. Notebook không truy vấn API; dữ liệu đọc từ snapshot đã khóa. Trước khi bắt đầu, xác nhận amendment và split:

```powershell
.\.venv\Scripts\python.exe scripts/verify_split_lock.py
```

1. **Kiểm toán tiền.** Làm gì: `scripts/audit_money.py` áp dụng amendment 03 và viết JSON/CSV/báo cáo. Vì sao: xác nhận doanh thu ghi nhận, ngoại lệ, điều chỉnh và cổng dừng 1% trước khi tạo đặc trưng. Tự kiểm tra: `status3_orders=6400`, `negative_revenue.stop=false`, gifts=22, negative=2 trong `outputs/metrics/day2_money_audit.json`.
2. **Đặc trưng và nhãn.** Làm gì: Restart & Run All `notebooks/02_preprocess.ipynb`. Vì sao: dựng snapshot tại T và nhãn dev sau khi chặn dữ liệu tương lai. Tự kiểm tra: `3508` khách, `260` dương; `max_label_asof < test_start`; hai cờ test trong `outputs/metrics/day2_label_audit.json` là `false`.
3. **Phân khúc.** Làm gì: chạy `notebooks/04_unsupervised.ipynb`, xem `segments_elbow.png`, `segments_silhouette.png`, `segment_profiles.csv`, `segments.csv`. Vì sao: chọn K có số liệu và kiểm tra khách giá trị cao không bị gán nhãn rời bỏ. Tự kiểm tra: `chosen_k=2` và xem A/B trong `outputs/metrics/day2_segmentation.json`.
4. **Phân loại.** Làm gì: chạy `notebooks/03_supervised.ipynb`. Vì sao: đo khả năng tổng quát theo thời gian, không trộn khách và chỉ fit tiền xử lý trong train. Tự kiểm tra: 5 fold, OOF coverage=1,558, xem PR-AUC/ma trận nhầm lẫn, `tree_depth_diagnostics` và SHA trong `outputs/metrics/dev_final_model.json`; cờ test phải `false`.
5. **Combo.** Làm gì: chạy `notebooks/05_combo.ipynb`. Vì sao: tìm đồng xuất hiện trong đơn đủ sản phẩm, không diễn giải nhân quả hay lợi nhuận. Tự kiểm tra: `6031` giỏ, support=0.05, `68` luật trong `outputs/metrics/day2_baskets.json` và `outputs/tables/rules.csv`/`combos.csv`.
6. **Kiểm tra cuối.** Làm gì: chạy `scripts/verify_pii.py` và pipeline tổng thể bằng:

```powershell
.\.venv\Scripts\python.exe scripts/run_all.py
```

**[LỊCH SỬ — trước lần mở test duy nhất]** Khi viết đoạn này, test chưa mở; bước mở test đã được chủ dự án duyệt sau đó. Diễn giải kết quả hiện hành và sai khác ngày T nằm tại `docs/test_provenance_note.md`.

## Tự kiểm tra Ngày 2B

`run_all.py` thực hiện vòng này đúng một lần theo `config/amendment_04_followup.yaml`. Khi trạng thái trong `outputs/logs/day2b_experiment_state.json` là `complete`, lần chạy sau chỉ kiểm tra đầu ra, không lặp thí nghiệm.

```powershell
.\.venv\Scripts\python.exe scripts/run_all.py
.\.venv\Scripts\python.exe scripts/verify_pii.py
```

Đối chiếu `day2b_baskets.json`: 6031 giỏ trước, 5684 sau lọc giá 0, support 0.05. Đối chiếu `day2b_segmentation.json`: K=2 được giữ; K=3/4 có 5 seed và ARI chính/B. Đối chiếu `dev_final_models_v2.json`: mô hình gốc SHA `0ac767d24c641f50bdc19634e590dc45a92d9e4cd5513d02871fac50b109cd4a`, không bị thay; xem CI và signal flag của bộ đặc trưng mới. Đối chiếu `day2b_cancel_model.json`: dương từng fold `F1: 30 / 1330, F2: 13 / 801, F3: 6 / 920, F4: 1 / 726, F5: 18 / 1007`, gate không đạt.

**[LỊCH SỬ — trạng thái trước lần mở test]** Test sau đó được mở một lần theo lock. Hiện không chạy lại thí nghiệm; xem `docs/test_provenance_note.md` để biết protocol thực tế và giới hạn kết luận.
