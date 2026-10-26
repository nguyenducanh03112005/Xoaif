# Nhật ký đóng gói và dọn dẹp

## Bước 0 — baseline trước khi sửa

- Ngày thực hiện: 2026-10-26.
- Lệnh: `.venv\Scripts\python -B scripts/verify_day3_locks.py`, với `PYTHONDONTWRITEBYTECODE=1`.
- Kết quả: đạt — đúng một lần mở test, input đóng băng còn nguyên, kết quả và access audit hiện diện.
- HEAD baseline: `8ea82eb299cc1c919484c1b40b4298ec308e8728` (không có commit restore point riêng được chỉ định).
- Commit restore point của chủ dự án xuất hiện sau ảnh chụp baseline: `9ed7a50a7f1b874032769b558d1f753a0c92de12` (`Package reviewed submission artifacts`); các thay đổi baseline đã được commit nguyên trạng, không phải do agent tạo.
- 17 SHA-256 baseline được bảo vệ:

| Đường dẫn | SHA-256 |
| --- | --- |
| `config/split.yaml` | `38d0e35ee8b34016d1246d111eed0315974390ab255daee8b48002373331553e` |
| `config/split.lock.json` | `cb6d983a9b32f43bfcbb671f7d71af1b012a70b8af999efbed3691ceb3e04440` |
| `config/amendment_01_analysis_start.yaml` | `23da1216cf06c32003d52eb7831ed528dc4a4259d3480a9e3025fcb394100cfd` |
| `config/amendment_01_analysis_start.lock.json` | `27fb532ac0ea1f76e0edd82a0733ba4d0d5f1231eaa057b09ddafaffa0106b21` |
| `config/amendment_02_money_and_gift_rules.yaml` | `668d9b717597bb9131a66c02c4f0ca53003a20374bbbce76e1fc3242413fe66b` |
| `config/amendment_02_money_and_gift_rules.lock.json` | `04ed73fe4f89096d40bd38e37932f412c520cb2c6c73465b89d3a9c1744f7c49` |
| `config/amendment_03_money_adjustment.yaml` | `3d87751451fa17fe71644df7f0743331ee6dae6b34013a4b063e18b6da98eaf1` |
| `config/amendment_03_money_adjustment.lock.json` | `c1a4560aeacac39f2e8234abedb365f6c10f4a950b24040e422e488dfc94c076` |
| `config/amendment_04_followup.yaml` | `e76ee390e227a569a39ab5f4fe7c7489572a06323d6d2f1bc6c8b72fa52ea6f8` |
| `config/amendment_04_followup.lock.json` | `54bcf6166a06a428f7829d9154e94f91622632ab4c3c84b0008500217dd806b6` |
| `config/amendment_05_gift_lines.yaml` | `27bda2f81cfc963921ecb7a0da235777031996b26563d6425fbfa8d525eed720` |
| `config/amendment_05_gift_lines.lock.json` | `5c627f1abde20211356c8cefd956216701142fc6bd247efd822294f8cbdb72f2` |
| `config/amendment_05_test_open.yaml` | `7964367ae28aa10d31e4c573772b7c3bc22b3f8b3d340c3292d0593bf6f30272` |
| `config/amendment_05_test_open.lock.json` | `b8e6dc667f2344dfecb1b19c12bb776fce44a9339e8bab2a7663de03d6cbd25e` |
| `outputs/metrics/day3_pretest_freeze.json` | `be57e7a73fb0844ac46ebd3707e65db5008f0cc23f57c46c93afd40bf975727d` |
| `outputs/metrics/test_opened.lock.json` | `74af2c6ccd61f6c071529115b13ff144b25fa264600cb27e1832f764bde6d874` |
| `outputs/metrics/test_eval.json` | `5b502637d05f4a21cfa803b3f1582c8d507335e2dcac64ee63d84826f123c625` |

## A1 — ảnh chụp trạng thái ban đầu

Các thay đổi sau đã có trước khi đóng gói; giữ nguyên, không hoàn tác, reset, stash hay checkout:

```text
 M README.md
 M docs/PROGRESS.md
 M docs/canonical_numbers.md
 M docs/data_gap_report.md
D  docs/demo_screens/01-overview.png
 M docs/demo_script.md
 M docs/final_consistency_report.md
 M docs/handover.md
 M docs/qa.md
 M docs/test_report.md
 M scripts/build_report_pdf.py
 M scripts/build_slides_pdf.py
 M scripts/dashboard_smoke.py
 M src/app/streamlit_app.py
?? docs/submission_artifacts.md
```

`git diff --stat` baseline:

```text
 README.md                        |  5 +++--
 docs/PROGRESS.md                 |  8 ++++----
 docs/canonical_numbers.md        |  2 +-
 docs/data_gap_report.md          |  4 ++++
 docs/demo_script.md              | 21 ++++++++++-----------
 docs/final_consistency_report.md |  6 +++---
 docs/handover.md                 |  6 ++++--
 docs/qa.md                       |  4 ++++
 docs/test_report.md              |  8 ++++++--
 scripts/build_report_pdf.py      | 19 ++++++++-----------
 scripts/build_slides_pdf.py      | 21 ++++++++++++---------
 scripts/dashboard_smoke.py       |  2 +-
 src/app/streamlit_app.py         | 26 +++++++++++++++++---------
 13 files changed, 70 insertions(+), 62 deletions(-)
```

Staged baseline also contains deletion `docs/demo_screens/01-overview.png` (145,797 bytes); untracked baseline contains `docs/submission_artifacts.md`. Both are preserved as pre-existing state. The nine files named by the project owner are included above; the other baseline changes are preserved too.

Two-level root snapshot (protected directory contents intentionally not traversed): `.codex/day3_build/`; `.pytest_cache/v/`; `docs/demo_screens/` plus 36 Markdown files; `notebooks/` with six notebooks; `scripts/` with 30 Python files and existing `__pycache__/`; `src/` with `app/`, `features/`, `ingest/`, `models/`, `warehouse/`; `tests/` with 14 test files and existing `__pycache__/`; `tmp_artifacts/pdf_build/`. Root files: `.gitignore`, `Ke_hoach_cuoi_cung_Xoaif_Garden.md`, `pyproject.toml`, `README.md`, `requirements.in`, `requirements.txt`, `Xoaif.env`, `xoaif.env.example`. `.git`, `.venv`, `config`, `data`, `outputs`, `report`, and `slides` were not traversed for this tree snapshot.

Initial safe-directory sizes: `.codex` 0.51 MB; `.pytest_cache` 0.01 MB; `docs` 0.76 MB; `notebooks` 0.23 MB; `scripts` 0.84 MB; `src` 0.61 MB; `tests` 0.21 MB; `tmp_artifacts` 6.63 MB. Sizes for `.git`, `.venv`, `config`, `data`, `outputs`, `report`, and `slides` were excluded from recursive measurement.

## A2 — DRY-RUN ứng viên

Quét tham chiếu văn bản bằng `rg` trên README, docs, config, scripts, notebooks, tests, src và `.gitignore`; không quét nội dung raw/restricted, outputs hay `.venv`. Không có tham chiếu tới `tmp_artifacts`, `report_render`, tên trang `page-*.png`, `report-final-*`, `slides-final-*`, `report-check-*` hoặc các ảnh contact render.

| Ứng viên | Lý do và chứng cứ không có tham chiếu |
| --- | --- |
| `.pytest_cache/` | Cache pytest thuần; không có mã/ tài liệu tiêu thụ, chỉ có quy tắc ignore trong `.gitignore`. |
| `scripts/__pycache__/` | Cache bytecode; không được tham chiếu hay tiêu thụ trong source/docs/config/notebooks/tests. |
| `src/app/__pycache__/` | Cache bytecode; không được tham chiếu hay tiêu thụ trong source/docs/config/notebooks/tests. |
| `src/features/__pycache__/` | Cache bytecode; không được tham chiếu hay tiêu thụ trong source/docs/config/notebooks/tests. |
| `src/ingest/__pycache__/` | Cache bytecode; không được tham chiếu hay tiêu thụ trong source/docs/config/notebooks/tests. |
| `src/models/__pycache__/` | Cache bytecode; không được tham chiếu hay tiêu thụ trong source/docs/config/notebooks/tests. |
| `src/warehouse/__pycache__/` | Cache bytecode; không được tham chiếu hay tiêu thụ trong source/docs/config/notebooks/tests. |
| `tests/__pycache__/` | Cache bytecode; không được tham chiếu hay tiêu thụ trong source/docs/config/notebooks/tests. |
| `tmp_artifacts/pdf_build/` | 56 ảnh PNG render trung gian báo cáo/slide để kiểm tra trang, nằm ngoài PDF bàn giao; quét tham chiếu các tên và thư mục cho kết quả rỗng. SHA-256 manifest trước xóa: `49112c757fb8d6372bcc7e3800140408c13a5eaabf89eeaf7148fa37d99980f9`. |
| `.codex/day3_build/report_render/` | 7 ảnh PNG render trang trung gian, không phải ảnh demo bàn giao; quét `report_render` và `page-*.png` cho kết quả rỗng. SHA-256 manifest trước xóa: `9666c4d1b357f576addde00026568a57cbdb263d5ff93ec23ad21dc5c0bb01a0`. |

Không thấy `.ipynb_checkpoints`, `*.tmp`, `*.bak`, `*.orig`, `~$*`, `Thumbs.db`, `.DS_Store`, `Desktop.ini` hoặc helper chụp ảnh khác trong các thư mục dự án được quét. Không có ứng viên rác nào khác chưa rõ tại thời điểm A2.

Baseline chỉ đọc của `.venv` sau lần chạy verifier đầu tiên: 1.456 thư mục `__pycache__`, 10.530 file `.pyc`; SHA-256 manifest đường dẫn là `3d6ae1c8ad1f8ea3774a769e187183cc274488d30acd652706d25738efa1281d`. Mọi lần chạy Python của đóng gói dùng `-B` và `PYTHONDONTWRITEBYTECODE=1`.

## A3 — thực hiện

Đã xóa `.pytest_cache/`, bảy thư mục `__pycache__/` được liệt kê ở A2 (88 file `.pyc`) và `tmp_artifacts/pdf_build/` (56 ảnh PNG). Hash manifest của thư mục PNG được ghi ở A2 trước khi xóa. Kiểm tra lại cho thấy các đường dẫn này không còn tồn tại.

Giữ `.codex/day3_build/report_render/` (7 ảnh): lệnh xóa bị từ chối quyền truy cập tại `.codex/`; không thử vượt quyền. Hash manifest ban đầu đã được ghi ở A2. Không xóa `.codex` hoặc `docs/demo_screens/`.

## A4 — `.gitignore`

Các quy tắc ban đầu đã bỏ qua `__pycache__/`, `.pytest_cache/`, `.venv/`, `data/`, `outputs/`, `.env` và các biến thể `*.env`. Chỉ thêm quy tắc bỏ qua các lockfile môi trường thường dùng (`Pipfile.lock`, `poetry.lock`, `uv.lock`, `pdm.lock`, `conda-lock.yml`, `environment.lock.yml`) và ngoại lệ chỉ cho phép `data/sample/README.md` cùng các CSV trực tiếp trong `data/sample/`; không xóa quy tắc cũ.

`git check-ignore -v` xác nhận `Xoaif.env`, `data/raw`, `data/restricted`, `outputs/models` và `uv.lock` bị bỏ qua. Các file `data/sample/` xuất hiện như file mới trong `git status`; không có file raw/restricted, model hay output mới trong status.

## C3 — kiểm tra liên kết trước khi lập mục lục

Quét liên kết tương đối trong `README.md`, toàn bộ `docs/*.md` và `slides/speaker_notes.md` (bỏ qua khối code, URL ngoài và anchor thuần) cho 0 liên kết hỏng. Không có liên kết cần sửa; vì vậy không có sửa liên kết để liệt kê.

Sau khi thêm `docs/INDEX.md`, kiểm tra lại 40 file Markdown cho 0 liên kết tương đối hỏng. Mục lục có liên kết tới đủ 42/42 file hiện có trong `docs/` (38 Markdown và 4 ảnh). README chỉ được nối thêm hai dòng mục lục và mô tả `data/sample/`.

## B — dữ liệu mẫu tổng hợp

`scripts/make_sample_data.py` chạy hai lần liên tiếp; cả hai lần tự kiểm đạt với 200 đơn, 811 dòng hàng, 23 dòng cờ quà và 19 bucket tháng. Ba CSV giống hệt nhau qua hai lần chạy, theo SHA-256:

- `data/sample/sample_orders.csv`: `2d7f27f711e440933570a73f8e2b3c88292e6549b25e5e350f4ea5d6c6c70867`
- `data/sample/sample_order_items.csv`: `839dd436a3187bcaee744118e94b37d66617326c820e79a562afc3654efdf85f`
- `data/sample/sample_aggregates_monthly.csv`: `869212df0c77a462177f41a081a23ab76e422314417efc1ab73bb4680db957a4`

Script chỉ dùng thư viện chuẩn, seed cố định, không tham chiếu `data/raw/`, `data/restricted/`, DuckDB, API, customer-HMAC hoặc outputs. Dashboard và smoke không tham chiếu `data/sample/`; mẫu ở ngoài `outputs/`.

## Kiểm tra cuối

- `scripts/run_all.py` hậu mở: đạt; split, GET-only, Day 3 locks, 74 pytest và quét PII đạt. Nhánh này không chạy evaluator, notebook hay fit/refit.
- `scripts/dashboard_smoke.py`: đạt theo dashboard đã có trong restore point — 5 tab, 10 aggregate CSV, 6 aggregate JSON, 405 dòng được kiểm tra. Restore point `9ed7a50` và trạng thái hiện hành trong `PROGRESS.md` ghi dashboard sau rà soát dùng 10 CSV; số 11 CSV/427 dòng là số trước cập nhật, giữ trong ghi chép lịch sử.
- `scripts/verify_pii.py` đạt; áp dụng cùng tripwire riêng cho `data/sample/` cũng đạt.
- Pytest chạy riêng với `-p no:cacheprovider`: 74 passed. Không thêm test.
- `scripts/verify_day3_locks.py` đạt; 17/17 SHA-256 khớp baseline; `test_open_count=1`; access log có đúng `label_load`, `behavior_load`.
- `scripts/check_consistency.py` không tồn tại. `git diff --check` đạt.
- `.venv` sau các lệnh kiểm tra: 1.456 thư mục `__pycache__`, 10.530 `.pyc`; manifest hash vẫn `3d6ae1c8ad1f8ea3774a769e187183cc274488d30acd652706d25738efa1281d`.
- `docs/INDEX.md`: 42/42 file được liệt kê; quét 40 Markdown cho 0 liên kết tương đối hỏng. Không có liên kết cần sửa.
- `docs/canonical_numbers.md` không sửa vì không có số kết quả dự án nào thay đổi.

## Giữ lại, cần người quyết định

- `.codex/day3_build/report_render/` — 7 ảnh render trang không có tham chiếu trong tài liệu/source đã quét. Giữ vì sandbox từ chối quyền xóa tại `.codex/`; chủ dự án có thể quyết định xóa thủ công sau này.

