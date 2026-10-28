# Xoaif Garden — phân tích bán hàng

Đọc theo thứ tự này để nắm dự án:

1. [Hướng dẫn dự án](docs/PROJECT_GUIDE.md) — chức năng, kiến trúc, dữ liệu, công nghệ, kết quả, cách cài/chạy và các quyết định còn mở.
2. [Cẩm nang bảo vệ và demo](docs/DEFENSE_GUIDE.md) — dàn ý nói, demo offline và hỏi đáp.
3. [Kế hoạch phạm vi](docs/PROJECT_PLAN.md) — yêu cầu và mục tiêu gốc.

## Bàn giao

- Dashboard offline: `src/app/streamlit_app.py`
- Báo cáo: `report/xoaif_report.pdf`
- Slide chỉnh sửa được: `slides/Xoaif_Final.pptx`
- Slide PDF và ghi chú: `slides/xoaif_print.pdf`, `slides/speaker_notes.md`
- [Mục lục tài liệu kỹ thuật](docs/INDEX.md)

## Cài và chạy trên Windows

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[analysis,dashboard,dev]"
.venv\Scripts\streamlit.exe run src/app/streamlit_app.py
```

Dashboard chỉ đọc aggregate cục bộ, không gọi API và không cần raw/DuckDB. Mẫu trong `data/sample/` là dữ liệu giả lập.

Sau khi cài dependency, hậu kiểm repo bằng `.venv\Scripts\python.exe scripts/run_all.py`. Holdout đã mở; runner không chạy evaluator hay fit lại. Không gọi `scripts/evaluate_test_once.py` lần nữa.

## Dữ liệu nhạy cảm

`data/raw/`, `data/restricted/`, khóa API, khóa HMAC và bảng từng khách/đơn chỉ lưu cục bộ; không commit hoặc chia sẻ. Xem [quản trị dữ liệu](docs/data_governance.md) và [API/giới hạn](docs/api_notes.md).
