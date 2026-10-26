"""Build a 14-slide print PDF from frozen aggregate project outputs."""
from __future__ import annotations

import argparse
import json
import os
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager, image as mpimg
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "slides" / "xoaif_print.pdf"
COLORS = {
    "green": "#183D36", "teal": "#176B87", "leaf": "#73A98F",
    "gold": "#E3A64B", "red": "#A14633", "ink": "#24332F",
    "muted": "#61736D", "line": "#CAD8D2", "pale": "#E7F0EC",
    "paper": "#F7FAF8", "warning": "#FFF1D6",
}


def configure_font(font_override: str | None = None) -> str:
    configured = font_override or os.environ.get("XOAIF_REPORT_FONT")
    if configured:
        font_path = Path(configured).expanduser()
        if not font_path.is_file():
            raise FileNotFoundError(f"Configured font does not exist: {font_path}")
        font_manager.fontManager.addfont(str(font_path))
        family = font_manager.FontProperties(fname=str(font_path)).get_name()
    else:
        family = None
        for name in ("Arial", "Liberation Sans", "DejaVu Sans"):
            try:
                font_path = Path(font_manager.findfont(name, fallback_to_default=False))
            except (ValueError, OSError):
                continue
            if font_path.is_file():
                font_manager.fontManager.addfont(str(font_path))
                family = font_manager.FontProperties(fname=str(font_path)).get_name()
                break
        if family is None:
            raise RuntimeError("No installed font suitable for Vietnamese slide PDF was found")
    matplotlib.rcParams.update({"font.family": family, "pdf.fonttype": 42, "axes.unicode_minus": False})
    return family


def read_json(name: str) -> dict:
    return json.loads((ROOT / "outputs" / "metrics" / name).read_text(encoding="utf-8"))


def fnum(value: float, digits: int = 3) -> str:
    return f"{value:.{digits}f}".replace(".", ",")


def fsigned(value: float, digits: int = 4) -> str:
    return f"{value:+.{digits}f}".replace(".", ",")


def fint(value: int) -> str:
    return f"{int(value):,}".replace(",", ".")


def slide(pdf: PdfPages, number: int, title: str, subtitle: str = ""):
    fig = plt.figure(figsize=(13.333, 7.5), facecolor=COLORS["paper"])
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off()
    ax.add_patch(Rectangle((0, .91), 1, .09, transform=ax.transAxes, color=COLORS["green"]))
    ax.text(.055, .958, title, fontsize=22, weight="bold", color="white", va="center", transform=ax.transAxes)
    if subtitle:
        ax.text(.06, .875, subtitle, fontsize=10, color=COLORS["muted"], va="top", transform=ax.transAxes)
    ax.plot([.055, .945], [.075, .075], color=COLORS["line"], lw=.8, transform=ax.transAxes)
    ax.text(.06, .043, "Xoaif Garden · Kho & Khai phá dữ liệu", fontsize=8, color=COLORS["muted"], transform=ax.transAxes)
    ax.text(.94, .043, f"{number:02d} / 14", fontsize=8, color=COLORS["muted"], ha="right", transform=ax.transAxes)
    return fig, ax


def card(ax, x: float, y: float, w: float, h: float, label: str, value: str, detail: str = "", fill: str | None = None):
    patch = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.012,rounding_size=0.015",
                           transform=ax.transAxes, fc=fill or "white", ec=COLORS["line"], lw=.8)
    ax.add_patch(patch)
    ax.text(x+.04, y+h*.78, label, fontsize=9, color=COLORS["muted"], va="top", transform=ax.transAxes)
    ax.text(x+.04, y+h*.50, value, fontsize=22, weight="bold", color=COLORS["green"], va="top", transform=ax.transAxes)
    if detail:
        ax.text(x+.04, y+h*.12, detail, fontsize=8.3, color=COLORS["ink"], va="bottom", wrap=True, transform=ax.transAxes)


def body(ax, x: float, y: float, text: str, *, size: float = 11, color: str | None = None, width: float = .85, weight: str = "normal"):
    text = text.replace("`", "")
    chars = max(24, int(width * 13.333 * 72 / (0.54 * size) * .92))
    wrapped = "\n".join(textwrap.fill(paragraph, width=chars) if paragraph else "" for paragraph in text.splitlines())
    return ax.text(x, y, wrapped, fontsize=size, color=color or COLORS["ink"], weight=weight,
                   va="top", wrap=True, linespacing=1.35, transform=ax.transAxes)


def heading(ax, x: float, y: float, text: str, size: float = 13):
    ax.text(x, y, text, fontsize=size, weight="bold", color=COLORS["green"], va="top", transform=ax.transAxes)


def add_table(ax, bbox, rows, headers, widths=None, fontsize=8.6):
    rows = [[str(value).replace("`", "") for value in row] for row in rows]
    headers = [str(value).replace("`", "") for value in headers]
    table = ax.table(cellText=rows, colLabels=headers, colWidths=widths, cellLoc="left", colLoc="left", bbox=bbox)
    table.auto_set_font_size(False); table.set_fontsize(fontsize)
    for (row, _col), cell in table.get_celld().items():
        cell.set_edgecolor(COLORS["line"]); cell.set_linewidth(.45)
        if row == 0:
            cell.set_facecolor(COLORS["green"]); cell.set_text_props(weight="bold", color="white")
        else:
            cell.set_facecolor("white" if row % 2 else "#F0F5F2"); cell.set_text_props(color=COLORS["ink"])
    return table


def image_panel(ax, filename: str, bounds):
    image_path = ROOT / filename
    if not image_path.is_file():
        raise FileNotFoundError(image_path)
    image_ax = ax.figure.add_axes(bounds)
    image_ax.imshow(mpimg.imread(image_path)); image_ax.axis("off")
    return image_ax


def build(output_path: Path | None = None, font_override: str | None = None) -> None:
    configure_font(font_override)
    output_path = output_path or OUT
    test = read_json("test_eval.json")
    dev = read_json("dev_final_models_v2.json")
    dev_primary = read_json("dev_final_model.json")
    money = read_json("day2_money_audit.json")
    seg = read_json("day2_segmentation.json")
    combo_dev = read_json("day3_combo_prereg.json")
    eda = read_json("eda_dev_summary.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with PdfPages(output_path, metadata={
        "Title": "Xoaif Garden — Kho dữ liệu và khai phá dữ liệu bán hàng",
        "Author": "Nhóm dự án Xoaif Garden",
        "Subject": "Bộ slide PDF tiếng Việt, dữ liệu aggregate đã khóa",
    }) as pdf:
        # 1. Cover
        fig = plt.figure(figsize=(13.333, 7.5), facecolor=COLORS["green"])
        ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off()
        ax.add_patch(Rectangle((0, .12), 1, .15, transform=ax.transAxes, color="#245B4C"))
        ax.text(.08, .82, "XOAIF GARDEN", fontsize=15, weight="bold", color="#CDE2D8", transform=ax.transAxes)
        ax.text(.08, .70, "Kho dữ liệu và\nkhai phá dữ liệu bán hàng", fontsize=32, weight="bold", color="white", va="top", transform=ax.transAxes)
        ax.text(.08, .44, "Pancake POS  ·  DuckDB  ·  Phân tích theo thời gian", fontsize=14, color="#E4F0EB", transform=ax.transAxes)
        ax.text(.08, .20, "Báo cáo dự án / bảo vệ cuối kỳ  ·  26/10/2026", fontsize=11, color="white", transform=ax.transAxes)
        ax.text(.08, .055, "Kết quả được trình bày cùng giới hạn provenance, cohort và dữ liệu.", fontsize=9, color="#CDE2D8", transform=ax.transAxes)
        pdf.savefig(fig); plt.close(fig)

        # 2. Questions and scope
        fig, ax = slide(pdf, 2, "Câu hỏi dự án và phạm vi", "Dữ liệu snapshot được kiểm tra theo thời gian và quy tắc nghiệp vụ")
        card(ax, .06, .62, .20, .20, "Snapshot khóa", "12.011", "đơn trên 601 trang")
        card(ax, .28, .62, .20, .20, "Kho DEV", "6.517", "đơn từ 01/04/2024 đến trước T")
        card(ax, .50, .62, .20, .20, "Cohort scoring đã freeze", "5.169", "khách; aggregate pre-open")
        card(ax, .72, .62, .20, .20, "Mở test", "01 lần", "không đánh giá lại")
        heading(ax, .07, .52, "Ba câu hỏi")
        body(ax, .07, .46, "1. Hành vi mua hàng và chất lượng dữ liệu mô tả được thế nào?\n2. Có tín hiệu xếp hạng khả năng mua lại trong 180 ngày không?\n3. Những sản phẩm nào thường đồng xuất hiện trong giỏ đủ điều kiện?", size=12, width=.78)
        ax.text(.07, .20, "Phân tích không kết luận lợi nhuận, hiệu quả can thiệp hay quan hệ nhân quả.", fontsize=11, color=COLORS["red"], weight="bold", transform=ax.transAxes)
        pdf.savefig(fig); plt.close(fig)

        # 3. Architecture
        fig, ax = slide(pdf, 3, "Kiến trúc dữ liệu: năm tầng", "Luồng API đọc-only đến sản phẩm phân tích offline")
        items = [
            ("1 · Thu nhận", "Pancake POS\nrequests · GET"),
            ("2 · Snapshot", "JSON · manifest\nSHA-256"),
            ("3 · Bảo vệ / ETL", "timezone · HMAC\nkiểm tra schema"),
            ("4 · Kho / khai phá", "DuckDB · Pandas\nscikit-learn · mlxtend"),
            ("5 · Trình bày", "Streamlit · PDF\naggregate outputs"),
        ]
        for i, (name, detail) in enumerate(items):
            x = .055 + i*.18
            patch = FancyBboxPatch((x, .43), .155, .25, boxstyle="round,pad=.012,rounding_size=.015",
                                   transform=ax.transAxes, fc=COLORS["pale"] if i % 2 == 0 else "white", ec=COLORS["line"])
            ax.add_patch(patch)
            ax.text(x+.012, .62, name, fontsize=10, weight="bold", color=COLORS["green"], transform=ax.transAxes)
            ax.text(x+.012, .55, detail, fontsize=9, color=COLORS["ink"], va="top", linespacing=1.5, transform=ax.transAxes)
            if i < len(items)-1:
                ax.add_patch(FancyArrowPatch((x+.158, .55), (x+.177, .55), transform=ax.transAxes,
                                             arrowstyle="-|>", mutation_scale=12, color=COLORS["teal"]))
        body(ax, .07, .32, "Dashboard đọc CSV/JSON aggregate cục bộ, không gọi Pancake API. Kho DEV có fact đơn, fact dòng hàng và các dimension khách/ngày/trạng thái/sản phẩm.", size=11, width=.82)
        body(ax, .07, .20, "DBSCAN địa lý được cân nhắc nhưng không chạy vì không có tọa độ hoặc mã vùng đủ chi tiết.", size=10, color=COLORS["muted"], width=.82)
        pdf.savefig(fig); plt.close(fig)

        # 4. Time and cohorts
        fig, ax = slide(pdf, 4, "Mốc thời gian và các cohort", "Mỗi số đếm có đơn vị và điều kiện riêng")
        x0, x1, x2, x3 = .08, .27, .69, .92
        ax.plot([x0, x3], [.68, .68], color=COLORS["line"], lw=7, solid_capstyle="round", transform=ax.transAxes)
        ax.plot([x0, x1], [.68, .68], color=COLORS["gold"], lw=7, solid_capstyle="round", transform=ax.transAxes)
        ax.plot([x1, x2], [.68, .68], color=COLORS["leaf"], lw=7, solid_capstyle="round", transform=ax.transAxes)
        ax.plot([x2, x3], [.68, .68], color=COLORS["teal"], lw=7, solid_capstyle="round", transform=ax.transAxes)
        for x in [x0, x1, x2, x3]: ax.scatter([x], [.68], s=55, color=COLORS["green"], zorder=5, transform=ax.transAxes)
        ax.text(x0, .75, "2022–2023", fontsize=9, ha="center", color=COLORS["muted"], transform=ax.transAxes)
        ax.text(x1, .75, "2024-04-01", fontsize=9, ha="center", color=COLORS["muted"], transform=ax.transAxes)
        ax.text(x2, .75, "T = 2025-10-22", fontsize=9, ha="center", color=COLORS["muted"], transform=ax.transAxes)
        ax.text(x3, .75, "2026-04-20", fontsize=9, ha="center", color=COLORS["muted"], transform=ax.transAxes)
        ax.text(.10, .57, "476 đơn pre-analysis\nđược giữ trong raw", fontsize=9, ha="center", transform=ax.transAxes)
        ax.text(.46, .57, "DEV [analysis_start, T)\n6.517 đơn · 6.400 status 3", fontsize=9, ha="center", transform=ax.transAxes)
        ax.text(.80, .57, "Test [T, end) theo lần chạy\nđã khóa một lần", fontsize=9, ha="center", transform=ax.transAxes)
        rows = [
            ["Eligibility preflight N=180", "5.499 khách"],
            ["Khách có đơn status 3 DEV", "5.174 khách"],
            ["Cohort scoring đã freeze", "5.169 khách"],
            ["Nhãn DEV", "3.508 mẫu · 260 dương"],
        ]
        add_table(ax, [.12, .17, .76, .27], rows, ["Cohort", "Quy mô"], widths=[.65, .35], fontsize=10)
        ax.text(.12, .11, "5.499 / 5.174 / 5.169 chưa có phân rã được xác minh; không coi là chuỗi giảm đã đối soát.", fontsize=9.2, color=COLORS["red"], weight="bold", transform=ax.transAxes)
        pdf.savefig(fig); plt.close(fig)

        # 5. Data quality / money
        fig, ax = slide(pdf, 5, "Chất lượng dữ liệu và quy tắc tiền", "Status hiện tại dùng làm quy ước nghiệp vụ; không có lịch sử chuyển trạng thái")
        card(ax, .07, .58, .19, .22, "Đơn status 3 DEV", "6.400", "đơn mua hợp lệ theo D-013")
        card(ax, .28, .58, .19, .22, "Thiếu mã khách", "286", "đơn status 3 không nối lịch sử")
        card(ax, .49, .58, .19, .22, "Đơn quà cấp đơn", "22", "bị loại khỏi hành vi/giỏ")
        card(ax, .70, .58, .22, .22, "Doanh thu âm", "2 / 6.400", "0,03%, dưới cổng dừng 1%")
        heading(ax, .08, .46, "Diễn giải doanh thu")
        body(ax, .08, .40, "Doanh thu ghi nhận theo công thức đã xác nhận và Amendment 03. `price_adjustment` có thể phản ánh phí hoặc ưu đãi. Không gọi doanh thu này là lợi nhuận hay đối soát ngân hàng.", size=11, width=.82)
        body(ax, .08, .24, "Độ nhạy công thức A/B được báo riêng. Chênh lệch ròng giữa hai cách là 52.016.532 VND (2,02% tổng A); chưa có sổ kế toán độc lập để xác minh.", size=11, width=.82)
        pdf.savefig(fig); plt.close(fig)

        # 6. DEV EDA figures
        fig, ax = slide(pdf, 6, "EDA trên DEV: giao dịch biến động, khách mua lặp ít", "Mô tả đơn status 3 trước T; không kiểm định nguyên nhân mùa vụ")
        image_panel(ax, "outputs/figures/eda_dev_monthly_orders.png", [.06, .25, .54, .52])
        image_panel(ax, "outputs/figures/eda_dev_customer_frequency.png", [.62, .35, .30, .42])
        body(ax, .08, .20, f"Tháng cao nhất có {fint(max(eda['monthly_valid_orders'], key=lambda row: row['orders'])['orders'])} đơn; 2025-10 chỉ có dữ liệu đến ngày 21. Trong {fint(eda['valid_order_count'])} đơn, median giỏ là {fnum(eda['basket']['median_distinct_products'],0)} sản phẩm phân biệt. 4.526/5.174 khách DEV status 3 (87,5%) có một đơn.", size=10, width=.84)
        pdf.savefig(fig); plt.close(fig)

        # 7. Gift lines
        fig, ax = slide(pdf, 7, "Quà được phân loại theo dòng hàng", "Cờ API không bật; suy luận subset sum được giữ ở độ tin cậy thấp")
        card(ax, .08, .58, .24, .22, "Dòng DEV khảo sát", "30.049", "theo Amendment 05")
        card(ax, .38, .58, .24, .22, "Quà direct zero-price", "4", "theo quy tắc đã đăng ký")
        card(ax, .68, .58, .24, .22, "Subset sum suy luận", "903", "có thể gán nhầm")
        ax.add_patch(FancyArrowPatch((.32, .68), (.38, .68), transform=ax.transAxes, arrowstyle="-|>", mutation_scale=13, color=COLORS["teal"]))
        ax.add_patch(FancyArrowPatch((.62, .68), (.68, .68), transform=ax.transAxes, arrowstyle="-|>", mutation_scale=13, color=COLORS["teal"]))
        heading(ax, .09, .46, "Hệ quả cho khai phá giỏ")
        body(ax, .09, .40, f"Quà cấp đơn và dòng quà bị loại theo quy tắc đã khóa. Có {combo_dev['main_combo_count']} cặp chính ổn định ở ít nhất 4/6 ô và có mặt tại ô chính; tên sản phẩm hoặc support không được dùng để xác định quà.", size=11, width=.82)
        body(ax, .09, .25, "Chủ cửa hàng xác nhận nhân viên nhập giảm giá thủ công. Phần suy luận 903 dòng dựa trên subset sum tối đa 6 dòng, không phải nhãn được xác minh thủ công từng dòng.", size=10.5, color=COLORS["muted"], width=.82)
        pdf.savefig(fig); plt.close(fig)

        # 8. Supervised method
        fig, ax = slide(pdf, 8, "Mô hình mua lại: cách đánh giá", "Nhãn nhị phân theo N=180; feature phải có local_date < T")
        card(ax, .08, .58, .23, .22, "Mẫu nhãn DEV", "3.508", "260 dương · 7,41%")
        card(ax, .36, .58, .23, .22, "Validation", "5 folds", "temporal expanding, khách tách biệt")
        card(ax, .64, .58, .28, .22, "Ngưỡng", "0,5", "được đăng ký trước test")
        heading(ax, .09, .46, "Metric phù hợp")
        body(ax, .09, .40, "ROC-AUC đo xếp hạng qua nhiều ngưỡng. Average Precision / PR-AUC xem precision–recall cho lớp dương hiếm; baseline xấp xỉ prevalence. Precision, recall, F1 và confusion matrix mô tả quyết định tại ngưỡng cố định.", size=11, width=.83)
        body(ax, .09, .22, "RMSE / MAE / R² là metric hồi quy. Accuracy không đủ khi 92,6% nhãn DEV là âm.", size=11, color=COLORS["red"], weight="bold", width=.83)
        pdf.savefig(fig); plt.close(fig)

        # 9. Model roles
        fig, ax = slide(pdf, 9, "Vai trò mô hình được giữ rõ ràng", "Kết quả DEV bổ sung không thay quyết định mô hình đã đăng ký")
        card(ax, .09, .55, .35, .27, "Mô hình chính theo D-005", "Logistic C=10", "Logistic Regression C=10 — mô hình chính theo D-005")
        card(ax, .56, .55, .35, .27, "Khảo sát bổ sung · Amendment 04", "feature-v2 · C=0,1", "không thay mô hình chính")
        v2 = dev["repurchase_features_v2"]["selected_oof_metrics"]
        primary = dev_primary["best_model_oof_metrics"]
        body(ax, .10, .42, f"DEV OOF C=10: ROC-AUC {fnum(primary['roc_auc'])}, gần mức ngẫu nhiên; feature-v2: {fnum(v2['roc_auc'])}. Development chưa xác nhận tín hiệu xếp hạng rõ.", size=12, width=.80)
        body(ax, .10, .23, "Test đạt ROC-AUC khoảng 0,70 nhưng đây chỉ là tín hiệu yếu chưa được DEV xác nhận, không đủ để kết luận mô hình hoạt động tốt. Test đã mở; không dùng nó để tinh chỉnh mô hình.", size=11, color=COLORS["muted"], width=.80)
        pdf.savefig(fig); plt.close(fig)

        # 10. One-time test
        fig, ax = slide(pdf, 10, "Đánh giá test một lần", "Point estimate và CI mô tả lần chạy thực tế; không chọn lại mô hình")
        models = test["models"]
        row_specs = [
            ("majority_baseline", "Baseline majority"),
            ("amendment_03_logistic_regression", "C=10 — mô hình chính"),
            ("repurchase_features_v2_logistic_regression", "feature-v2 C=0,1 — bổ sung"),
        ]
        rows = []
        for key, label in row_specs:
            m = models[key]
            matrix = m["confusion_matrix_tn_fp_fn_tp"]
            cm = " / ".join(fint(value) for row in matrix for value in row)
            rows.append([label, fnum(m["precision"]), fnum(m["recall"]), fnum(m["f1"]), fnum(m["roc_auc"]), fnum(m["average_precision"]), cm])
        add_table(ax, [.055, .55, .89, .26], rows,
                  ["Mô hình", "Prec.", "Recall", "F1", "ROC-AUC", "AP", "TN / FP / FN / TP"],
                  widths=[.31, .09, .09, .08, .11, .08, .24], fontsize=9)
        cohort = test["cohort"]
        c10 = models["amendment_03_logistic_regression"]
        c10_ci = test["bootstrap_95_ci"]["amendment_03_logistic_regression"]["metrics_95_ci"]
        c10_delta = test["bootstrap_95_ci"]["paired_average_precision_delta_vs_baseline_95_ci"]["amendment_03_logistic_regression"]
        v2 = models["repurchase_features_v2_logistic_regression"]
        v2_ci = test["bootstrap_95_ci"]["repurchase_features_v2_logistic_regression"]["metrics_95_ci"]
        v2_delta = test["bootstrap_95_ci"]["paired_average_precision_delta_vs_baseline_95_ci"]["repurchase_features_v2_logistic_regression"]
        body(ax, .07, .49, f"Cohort {fint(cohort['eligible_customers_with_pre_T_purchase'])} khách; {fint(cohort['test_positive_customers'])} dương ({fnum(100*cohort['test_positive_rate'],2)}%); ngưỡng 0,5. Logistic Regression C=10 — mô hình chính theo D-005: ROC {fnum(c10['roc_auc'])} (CI {fnum(c10_ci['roc_auc']['lower'])}–{fnum(c10_ci['roc_auc']['upper'])}), AP {fnum(c10['average_precision'])}, ΔAP {fsigned(c10['average_precision']-models['majority_baseline']['average_precision'])} (CI {fsigned(c10_delta['lower'])}–{fsigned(c10_delta['upper'])}).", size=9.1, width=.86)
        body(ax, .07, .40, f"Logistic Regression feature-v2 C=0,1 — khảo sát bổ sung theo Amendment 04; không thay mô hình chính: ROC {fnum(v2['roc_auc'])} (CI {fnum(v2_ci['roc_auc']['lower'])}–{fnum(v2_ci['roc_auc']['upper'])}), AP {fnum(v2['average_precision'])}, ΔAP {fsigned(v2['average_precision']-models['majority_baseline']['average_precision'])} (CI {fsigned(v2_delta['lower'])}–{fsigned(v2_delta['upper'])}).", size=9.1, width=.86)
        ax.add_patch(FancyBboxPatch((.06, .13), .88, .20, boxstyle="round,pad=.012,rounding_size=.01", transform=ax.transAxes,
                                   fc=COLORS["warning"], ec="#E8C980", lw=.8))
        ax.text(.08, .305, "ROC-AUC test khoảng 0,70 là tín hiệu yếu trên một tập test đã mở; DEV C=10 gần ngẫu nhiên (0,5096) và chưa xác nhận tín hiệu này. Không kết luận mô hình tốt; không tinh chỉnh trên test.", fontsize=8.5, color=COLORS["ink"], va="top", wrap=True, transform=ax.transAxes)
        ax.text(.08, .255, "Cấu hình ghi >T, evaluator dùng [T,end) (gồm ngày T); ảnh hưởng chưa xác định; đây là kết quả số liệu của lần chạy thực tế, không phải khẳng định tuân thủ đầy đủ giao thức, không gọi là 'đạt cổng ghi trước'.",
                fontsize=8.2, color=COLORS["red"], va="top", wrap=True, transform=ax.transAxes)
        pdf.savefig(fig); plt.close(fig)

        # 11. Segmentation
        fig, ax = slide(pdf, 11, "Phân khúc RFM: mô tả, không gắn nhãn nguy cơ rời bỏ", "Gán nhóm bằng mô hình đã khóa và quy tắc nghiệp vụ song song")
        card(ax, .08, .57, .24, .23, "K được giữ", f"K = {seg['chosen_k']}", f"silhouette {fnum(seg['chosen_silhouette'])}")
        card(ax, .38, .57, .24, .23, "Khách một đơn · scoring", "4.530 / 5.169", "87,6%; DEV: 4.526 / 5.174 = 87,5%")
        card(ax, .68, .57, .24, .23, "Proxy giá trị lớn", str(seg["business_like_proxy"]["customers"]), "không phải xác minh pháp nhân")
        heading(ax, .09, .45, "Cách diễn giải")
        body(ax, .09, .39, "K-Means K=2 chủ yếu tách khách mua một lần với khách mua lặp lại. Điều này chưa chứng minh các nhóm có ý nghĩa kinh doanh hay hỗ trợ quyết định tốt hơn; K=3/4 chỉ là độ nhạy. RFM mô tả lịch sử trước T, không chứng minh nguy cơ rời bỏ.", size=11, width=.83)
        body(ax, .09, .22, "Không fit lại trên test. Metric phân phối bằng 0 trong một số so sánh phát sinh do dùng cùng profile trước T, không phải bằng chứng hành vi tương lai ổn định.", size=10.5, color=COLORS["muted"], width=.83)
        pdf.savefig(fig); plt.close(fig)

        # 12. Association
        fig, ax = slide(pdf, 12, "Luật kết hợp và combo", "Chỉ chấm các cặp đã freeze; không tìm luật mới trên test")
        test_assoc = test["association_rules"]
        card(ax, .10, .57, .23, .23, "Cặp đã freeze", str(test_assoc["frozen_combo_count"]), "trước khi mở test")
        card(ax, .39, .57, .23, .23, "Lift test > 1", f"{test_assoc['test_lift_gt_1_count']} / {test_assoc['frozen_combo_count']}", "mô tả đồng xuất hiện")
        card(ax, .68, .57, .23, .23, "Giỏ đủ điều kiện", fint(test_assoc["test_eligible_basket_count"]), "sau loại dòng quà")
        heading(ax, .10, .45, "Ý nghĩa kinh doanh và giới hạn")
        body(ax, .10, .39, "Support, confidence và lift mô tả tần suất hai sản phẩm cùng có mặt trong giỏ. Kết quả có thể gợi ý thử nghiệm trưng bày hoặc bundle.", size=11, width=.80)
        body(ax, .10, .22, "Không có giá vốn, không phân bổ chiết khấu theo sản phẩm. Lift > 1 không chứng minh lợi nhuận hay quan hệ nhân quả.", size=11, color=COLORS["red"], weight="bold", width=.80)
        pdf.savefig(fig); plt.close(fig)

        # 13. Dashboard
        fig, ax = slide(pdf, 13, "Dashboard offline và demo", "Năm tab, dữ liệu aggregate cục bộ, không cần API key")
        heading(ax, .08, .80, "Năm tab")
        body(ax, .08, .73, "1. Tổng quan doanh số\n2. Phân khúc khách\n3. Combo gợi ý\n4. Chất lượng & kiểm toán\n5. Mô hình mua lại", size=13, width=.37)
        heading(ax, .53, .80, "Giới hạn luôn hiển thị")
        body(ax, .53, .73, "Không so sánh doanh thu tỉnh/thành vì 91,92% là UNKNOWN.\n\nBài phân loại phản hồi bị bỏ qua vì thiếu dữ liệu có nhãn.\n\nTest ROC-AUC khoảng 0,70 là tín hiệu yếu mà DEV (~0,51) chưa xác nhận; không tinh chỉnh theo test đã mở.\n\nK=2 chủ yếu phân biệt khách mua một lần và mua lặp lại, chưa chứng minh ý nghĩa kinh doanh.", size=10.5, color=COLORS["ink"], width=.37)
        body(ax, .08, .30, "Smoke xác nhận 5 tab, 10 aggregate CSV và 6 aggregate JSON. Không hiển thị khách hoặc đơn hàng từng dòng; dashboard chỉ đọc dữ liệu cục bộ.", size=10.5, color=COLORS["muted"], width=.82)
        pdf.savefig(fig); plt.close(fig)

        # 14. Limits and preparation
        fig, ax = slide(pdf, 14, "Giới hạn và việc cần chuẩn bị trước bảo vệ", "Chốt cách giải thích, giữ nguyên ranh giới dữ liệu đã khóa")
        heading(ax, .07, .80, "Thành viên A")
        body(ax, .07, .75, "Trình bày câu hỏi, validation theo thời gian, metric và vai trò mô hình C=10/v2. Giải thích `>T` so với `[T,end)` và vì sao ảnh hưởng chưa xác định.", size=9.5, width=.39)
        heading(ax, .53, .80, "Thành viên B")
        body(ax, .53, .75, "Trình bày Star Schema, status/tiền, phân loại quà, phân khúc và giới hạn association. Nhấn mạnh proxy không xác minh doanh nghiệp.", size=9.5, width=.39)
        heading(ax, .07, .52, "Cả hai")
        body(ax, .07, .47, "Tập demo 4 phút bằng dashboard/ảnh/PDF; kiểm tra máy trình chiếu và thống nhất câu trả lời về cohort chưa đối soát, một cửa sổ test, thiếu giá vốn và kết luận không nhân quả.", size=9.5, width=.39)
        heading(ax, .53, .52, "Giới hạn cần nói rõ")
        body(ax, .53, .47, "Một Tết trọn vẹn trong DEV; 91,92% doanh thu tỉnh là UNKNOWN; thiếu dữ liệu phản hồi có nhãn; 903 inferred_subset có thể gán nhầm; status hiện tại không phải status history; không chạy evaluator/notebook lại.", size=9.5, width=.39)
        ax.text(.07, .20, "Hạn nộp: 2026-10-27. Thời lượng chính thức và rubric chưa có trong hồ sơ. Mỗi người cần tập trả lời ít nhất 10 câu thuộc phần của người kia.", fontsize=9.1, color=COLORS["muted"], transform=ax.transAxes)
        pdf.savefig(fig); plt.close(fig)

    print(f"Wrote {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUT, help="Destination print PDF path")
    parser.add_argument("--font", help="Optional font file path; otherwise auto-discover an installed font")
    args = parser.parse_args()
    build(output_path=args.output, font_override=args.font)
