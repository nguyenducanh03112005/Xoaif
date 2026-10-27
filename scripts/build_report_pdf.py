"""Build the Vietnamese Day 3 report from frozen, aggregate project outputs."""

from __future__ import annotations

import argparse
import json
import os
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "report" / "xoaif_report.pdf"


def configure_font(font_override: str | None = None) -> str:
    configured = font_override or os.environ.get("XOAIF_REPORT_FONT")
    if configured:
        font_path = Path(configured).expanduser()
        if not font_path.is_file():
            raise FileNotFoundError(f"Configured report font does not exist: {font_path}")
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
            raise RuntimeError("No installed font suitable for PDF output was found")
    matplotlib.rcParams.update({
        "font.family": family,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "axes.unicode_minus": False,
    })
    return family


def load_json(name: str) -> dict:
    return json.loads((ROOT / "outputs" / "metrics" / name).read_text(encoding="utf-8"))


def fnum(v: float, digits: int = 3) -> str:
    return f"{v:.{digits}f}".replace(".", ",")


def fsigned(v: float, digits: int = 4) -> str:
    return f"{v:+.{digits}f}".replace(".", ",")


def fpct(v: float, digits: int = 1) -> str:
    return f"{100*v:.{digits}f}%".replace(".", ",")


def fint(v: int | float) -> str:
    return f"{int(v):,}".replace(",", ".")


def fvnd(v: float) -> str:
    return f"{int(round(v)):,}".replace(",", ".") + " đ"


def plot_text(ax, *args, **kwargs):
    if args:
        args = (str(args[0]).replace("`", ""), *args[1:])
    return ax.text(*args, **kwargs)


def fresh_page(pdf: PdfPages, page_no: int, title: str, subtitle: str = ""):
    fig = plt.figure(figsize=(8.27, 11.69), facecolor="#FFFFFF")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_axis_off()
    fig.text(0.075, 0.956, title, fontsize=19, weight="bold", color="#183D36", va="top")
    if subtitle:
        fig.text(0.075, 0.925, subtitle, fontsize=9, color="#5B6E68", va="top")
    ax.plot([0.075, 0.925], [0.905, 0.905], color="#9CB5AB", lw=0.9, transform=ax.transAxes)
    ax.text(0.075, 0.035, "Xoaif Garden · Kho & Khai phá dữ liệu", fontsize=8, color="#61736D")
    ax.text(0.925, 0.035, f"{page_no:02d}", fontsize=8, color="#61736D", ha="right")
    return fig, ax


def text_block(ax, x: float, y: float, content: str, width: int = 100, fontsize: float = 10.3,
               color: str = "#24332F", leading: float = 1.35, bullet: bool = False):
    content = content.replace("`", "")
    line_height = fontsize / 72 / 11.69 * leading
    cursor = y
    for raw in content.split("\n"):
        if not raw.strip():
            cursor -= line_height * 0.55
            continue
        prefix = "• " if bullet else ""
        lines = textwrap.wrap(raw, width=width, subsequent_indent="  " if bullet else "",
                              break_long_words=False, break_on_hyphens=False)
        if bullet and lines:
            lines[0] = prefix + lines[0]
        for line in lines:
            ax.text(x, cursor, line, fontsize=fontsize, color=color, va="top", transform=ax.transAxes)
            cursor -= line_height
    return cursor


def section_label(ax, x: float, y: float, text: str, size: float = 12):
    ax.text(x, y, text, fontsize=size, weight="bold", color="#1B5C4F", va="top", transform=ax.transAxes)


def add_table(ax, bbox, cell_text, col_labels, col_widths=None, fontsize=8.4, row_height=1.3):
    cell_text = [[str(value).replace("`", "") for value in row] for row in cell_text]
    col_labels = [str(value).replace("`", "") for value in col_labels]
    table = ax.table(cellText=cell_text, colLabels=col_labels, colWidths=col_widths,
                     cellLoc="left", colLoc="left", bbox=bbox)
    table.auto_set_font_size(False)
    table.set_fontsize(fontsize)
    table.scale(1, row_height)
    for (r, c), cell in table.get_celld().items():
        cell.set_edgecolor("#CAD8D2")
        cell.set_linewidth(0.45)
        if r == 0:
            cell.set_facecolor("#E7F0EC")
            cell.set_text_props(weight="bold", color="#183D36")
        else:
            cell.set_facecolor("#FFFFFF" if r % 2 else "#F7FAF8")
            cell.set_text_props(color="#24332F")
    return table


def box(ax, x, y, w, h, label, detail, fill="#EEF5F1", label_size=10, detail_size=8.2):
    patch = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.012,rounding_size=0.012",
                           transform=ax.transAxes, fc=fill, ec="#A9C0B6", lw=0.8)
    ax.add_patch(patch)
    ax.text(x + w/2, y + h*0.67, label, ha="center", va="center", fontsize=label_size,
            weight="bold", color="#183D36", transform=ax.transAxes)
    ax.text(x + w/2, y + h*0.31, detail, ha="center", va="center", fontsize=detail_size,
            color="#465C55", wrap=True, transform=ax.transAxes)


def main(output_path: Path | None = None, font_override: str | None = None) -> None:
    configure_font(font_override)
    output_path = output_path or OUT
    test = load_json("test_eval.json")
    dev = load_json("dev_final_models_v2.json")
    dev_primary = load_json("dev_final_model.json")
    seg = load_json("day2_segmentation.json")
    money = load_json("day2_money_audit.json")
    combo = load_json("day3_combo_prereg.json")
    cohort_bridge = json.loads((ROOT / "outputs/tables/cohort_bridge_verified.json").read_text(encoding="utf-8"))
    monthly = pd.read_csv(ROOT / "outputs" / "tables" / "dashboard_sales_monthly.csv")
    provinces = pd.read_csv(ROOT / "outputs" / "tables" / "dashboard_sales_province.csv")
    products = pd.read_csv(ROOT / "outputs" / "tables" / "dashboard_product_orders.csv")
    test_segments = pd.read_csv(ROOT / "outputs" / "tables" / "test_segment_profiles.csv")
    combos = pd.read_csv(ROOT / "outputs" / "tables" / "test_combos_frozen.csv")
    profile = pd.read_csv(ROOT / "outputs" / "tables" / "product_profile.csv")
    dates = test["test_interval"]
    dev_lr = dev["repurchase_features_v2"]["selected_oof_metrics"]
    test_v2 = test["models"]["repurchase_features_v2_logistic_regression"]
    test_ci = test["bootstrap_95_ci"]["repurchase_features_v2_logistic_regression"]["metrics_95_ci"]
    delta_ci = test["bootstrap_95_ci"]["paired_average_precision_delta_vs_baseline_95_ci"]["repurchase_features_v2_logistic_regression"]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with PdfPages(output_path, metadata={
        "Title": "Xoaif Garden - Kho & Khai phá dữ liệu",
        "Author": "Nhóm dự án Xoaif Garden",
        "Subject": "Báo cáo cuối kỳ tiếng Việt",
    }) as pdf:
        # 1. Cover
        fig = plt.figure(figsize=(8.27, 11.69), facecolor="#F7FAF8")
        ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off()
        ax.add_patch(Rectangle((0, .71), 1, .29, transform=ax.transAxes, color="#183D36"))
        ax.text(.08, .92, "BÁO CÁO CUỐI KỲ", fontsize=12, color="#CAE1D6", weight="bold", transform=ax.transAxes)
        ax.text(.08, .845, "Kho dữ liệu và\nkhai phá dữ liệu bán hàng", fontsize=27, color="#FFFFFF",
                weight="bold", va="top", transform=ax.transAxes)
        ax.text(.08, .655, "Xoaif Garden · Pancake POS · DuckDB", fontsize=14, color="#183D36", weight="bold", transform=ax.transAxes)
        ax.text(.08, .595, "Tổ chức dữ liệu theo thời gian; kiểm toán quy tắc tiền;\nđánh giá mô hình, phân khúc và luật kết hợp.",
                fontsize=12, color="#3C514A", va="top", linespacing=1.5, transform=ax.transAxes)
        cards = [
            ("DEV", "6.400 đơn status 3"),
            ("TEST", f"{test['cohort']['eligible_customers_with_pre_T_purchase']:,} khách đủ điều kiện".replace(",", ".")),
            ("COMBO", f"{combo['main_combo_count']} luật đóng băng trước test"),
        ]
        for i, (head, value) in enumerate(cards):
            x = .08 + i*.29
            box(ax, x, .37, .25, .12, head, value, fill="#E7F0EC", label_size=10, detail_size=8.6)
        ax.text(.08, .23, f"Cửa sổ test: [{dates['start_inclusive']}, {dates['end_exclusive']}) · mở đúng một lần",
                fontsize=10, color="#3C514A", transform=ax.transAxes)
        ax.text(.08, .065, "26/10/2026", fontsize=9, color="#61736D", transform=ax.transAxes)
        pdf.savefig(fig); plt.close(fig)

        # 2. Contents
        fig, ax = fresh_page(pdf, 2, "Mục lục", "Cấu trúc theo bài toán, kho dữ liệu và ba hướng khai phá")
        toc = [
            "03  Giới thiệu, bối cảnh và câu hỏi kinh doanh",
            "04  Kiến trúc tổng quan 5 tầng và công cụ",
            "05  Dữ liệu, ETL và Star Schema",
            "06  Chất lượng dữ liệu và kiểm toán tiền",
            "07  EDA và hệ quả cho tiền xử lý",
            "08  Tiền xử lý, quà tặng theo dòng và chống rò rỉ",
            "09  Học có giám sát trên DEV",
            "10  Đánh giá test đã khóa một lần",
            "11  Phân khúc khách hàng",
            "12  Luật kết hợp, combo và mùa vụ",
            "13  Kết luận và giới hạn",
            "14  Hướng dẫn chạy lại, file bàn giao và thuật ngữ",
            "15  Nhật ký quyết định và phụ lục",
        ]
        text_block(ax, .09, .86, "\n\n".join(toc), width=95, fontsize=12, leading=1.45)
        pdf.savefig(fig); plt.close(fig)

        # 3. Introduction
        fig, ax = fresh_page(pdf, 3, "1. Giới thiệu", "Cửa hàng mở 04/2024; dữ liệu trước đó được giữ trong raw như giai đoạn bán thử")
        section_label(ax, .09, .86, "Bối cảnh")
        y = text_block(ax, .09, .825,
            "Dự án khai thác dữ liệu bán hàng từ Pancake POS nhằm phục vụ học phần Kho và Khai phá dữ liệu. Chủ dự án xác nhận cửa hàng bắt đầu hoạt động ngày 2024-04-01. Snapshot có 476 đơn bán thử từ 2022-06-04 đến 2022-09-21; các đơn này không tham gia doanh thu phân tích, hành vi khách, nhãn hay giỏ hàng.", width=102)
        section_label(ax, .09, y-.025, "Ba câu hỏi kinh doanh")
        y = text_block(ax, .09, y-.06,
            "1. Khách hàng nào có hành vi giá trị hoặc mua lặp lại theo lịch sử quan sát?\n2. Có đủ bằng chứng để xếp hạng khả năng mua lại trong cửa sổ thời gian kế tiếp không?\n3. Những sản phẩm nào đồng xuất hiện trong một giỏ đủ điều kiện, sau khi xử lý quà theo từng dòng?",
            width=100, fontsize=10.4)
        section_label(ax, .09, y-.03, "Phạm vi và ngôn ngữ báo cáo")
        text_block(ax, .09, y-.065,
            "Khoảng phát triển hiệu dụng bắt đầu 2024-04-01 và kết thúc trước mốc T = 2025-10-22. Dùng thuật ngữ “doanh thu ghi nhận” theo quy tắc nghiệp vụ status 3; không gọi là lợi nhuận hoặc đối soát ngân hàng. Luật kết hợp chỉ mô tả đồng xuất hiện, không khẳng định quan hệ nhân quả.", width=100)
        pdf.savefig(fig); plt.close(fig)

        # 4. Architecture
        fig, ax = fresh_page(pdf, 4, "2. Kiến trúc tổng quan", "Hình 1. Luồng 5 tầng từ nguồn tới sản phẩm phân tích")
        layers = [
            ("1 · Nguồn", "Pancake POS API · GET allowlist"),
            ("2 · Snapshot", "Raw JSON · checksum · mốc dữ liệu"),
            ("3 · ETL / chất lượng", "Chuẩn hóa thời gian · HMAC · kiểm tra tiền"),
            ("4 · Kho", "DuckDB · fact và dimension"),
            ("5 · Khai phá / trình bày", "Python · metrics · dashboard · báo cáo"),
        ]
        for i, (a, b) in enumerate(layers):
            y = .80 - i*.13
            box(ax, .14, y, .72, .09, a, b, fill="#EAF3EF" if i%2==0 else "#F5F8F6", label_size=10.3, detail_size=8.7)
            if i < len(layers)-1:
                ax.add_patch(FancyArrowPatch((.5, y-.006), (.5, y-.032), transform=ax.transAxes,
                                             arrowstyle="-|>", mutation_scale=10, color="#6F9183", lw=1))
        ax.text(.14, .125, "Luồng truy vấn nguồn chỉ GET. Dashboard đọc snapshot tổng hợp cục bộ và không có thao tác ghi API.",
                fontsize=9, color="#465C55", transform=ax.transAxes)
        ax.text(.14, .085, "Vai trò: API lấy dữ liệu · checksum chứng minh bản chụp · ETL chuẩn hóa · DuckDB truy vấn · Python/Streamlit trình bày.",
                fontsize=8.5, color="#465C55", wrap=True, transform=ax.transAxes)
        pdf.savefig(fig); plt.close(fig)

        # 5. Warehouse
        fig, ax = fresh_page(pdf, 5, "3. Dữ liệu và kho Star Schema", "Hình 2. Mô hình logic: sự kiện ở fact, ngữ cảnh ở dimension")
        box(ax, .36, .60, .28, .18, "fact_orders", "order_key · date_key · customer_key\nstatus_key · chỉ tiêu đơn", fill="#DCECE4", label_size=10, detail_size=8.2)
        box(ax, .36, .36, .28, .18, "fact_order_items", "order_key · product_key\nquantity · retail price · line flags", fill="#DCECE4", label_size=10, detail_size=8.2)
        box(ax, .06, .68, .22, .12, "dim_customer", "customer_key HMAC", label_size=9.2)
        box(ax, .72, .68, .22, .12, "dim_date", "date_key · ngày địa phương", label_size=9.2)
        box(ax, .06, .39, .22, .12, "dim_order_status", "status_key · mã trạng thái", label_size=9.2)
        box(ax, .72, .39, .22, .12, "dim_product", "product_key HMAC · nhóm", label_size=9.2)
        for a, b in [((.28,.74),(.36,.70)),((.64,.70),(.72,.74)),((.28,.45),(.36,.67)),((.64,.67),(.72,.45)),((.50,.60),(.50,.54))]:
            ax.add_patch(FancyArrowPatch(a,b,transform=ax.transAxes,arrowstyle="-|>",mutation_scale=9,color="#77978A",lw=.9))
        text_block(ax,.09,.27,
            "Kho phát triển gồm `fact_orders`, `fact_order_items`, `dim_customer`, `dim_date`, `dim_order_status` và `dim_product`. Khóa khách và sản phẩm được HMAC; kho không chứa địa chỉ, văn bản tự do, lịch sử trạng thái hay trường tiền. Chỉ tiêu tiền được giữ trong các đầu ra tổng hợp kiểm toán riêng.",width=105,fontsize=9.4)
        ax.text(.09,.14,"ETL giữ grain đơn hàng và dòng hàng tách biệt; khóa ngày dùng ngày địa phương Asia/Ho_Chi_Minh.",fontsize=9,color="#465C55",transform=ax.transAxes)
        pdf.savefig(fig); plt.close(fig)

        # 6. Data quality / money
        fig, ax = fresh_page(pdf, 6, "4. Chất lượng dữ liệu và kiểm toán tiền", "Bảng 1. Kiểm tra trên DEV status 3 theo quy tắc tiền Amendment 03")
        adj = money["price_adjustment"]
        vals = [
            ["Đơn status 3 DEV", f"{money['scope']['status3_orders']:,}".replace(",", ".")],
            ["Đơn quà cấp đơn loại", f"{money['gifts']['count']:,}".replace(",", ".")],
            ["Đơn doanh thu âm", f"{money['negative_revenue']['count']} ({fpct(money['negative_revenue']['rate'],2)})"],
            ["price_adjustment dương / âm", f"{adj['positive_count']} / {adj['negative_count']}"],
            ["Tổng price_adjustment ròng", fvnd(float(adj['net_sum']))],
            ["Ròng / doanh thu ghi nhận", fpct(adj['net_sum_as_percent_of_recognized_revenue']/100,2)],
            ["Lệch không giải thích hết", f"{money['adj_unexplained']['count']} ({fpct(money['adj_unexplained']['rate'],2)})"],
        ]
        add_table(ax, [.10,.57,.80,.27], vals, ["Chỉ tiêu", "Giá trị"], col_widths=[.53,.47], fontsize=9.2)
        section_label(ax,.10,.51,"Định nghĩa và diễn giải")
        text_block(ax,.10,.475,
            "Doanh thu ghi nhận dùng `total_price_after_sub_discount - shipping_fee`; khi trường sau giảm bằng `total_price - total_discount` và phí giao hàng dương, giữ giá sau giảm để tránh trừ phí hai lần. `price_adjustment = doanh thu ghi nhận - (total_price - total_discount)`. Điều chỉnh có thể phản ánh phí hoặc ưu đãi; không được hiểu là lợi nhuận.",width=99,fontsize=9.5)
        section_label(ax,.10,.335,"Độ nhạy A/B")
        text_block(ax,.10,.30,
            "Công thức A làm tổng doanh thu lệch 52.016.532 đ, bằng 2,02% tổng A; 642/6.378 đơn lệch trên 1%. Tương quan Spearman giữa Monetary theo khách là 0,9953. Độ nhạy cho biết kết quả phân khúc bền với phép đo này; không chứng minh công thức A hay B đúng.",width=98,fontsize=9.5)
        pdf.savefig(fig); plt.close(fig)

        # 7. EDA
        fig, ax = fresh_page(pdf, 7, "5. EDA và hệ quả cho xử lý", "Hình 3. Doanh thu ghi nhận theo tháng từ bảng tổng hợp; không phân bổ xuống sản phẩm")
        chart = fig.add_axes([.13,.59,.75,.25])
        chart.plot(range(len(monthly)), monthly["recognized_revenue_vnd"]/1_000_000, color="#24735F", lw=1.8, marker="o", ms=3)
        chart.axvline(18, color="#B46F45", ls="--", lw=1.2)
        chart.set_ylabel("Triệu VND")
        chart.set_xticks(range(0,len(monthly),2)); chart.set_xticklabels(monthly["month"].iloc[::2], rotation=45, ha="right", fontsize=7)
        chart.grid(axis="y", color="#DDE7E2", lw=.6)
        chart.spines[["top","right"]].set_visible(False)
        ax.text(.13,.50,"Đường gạch là mốc bắt đầu test; tháng cuối chưa trọn tháng.",fontsize=8,color="#61736D",transform=ax.transAxes)
        unknown = provinces.loc[provinces["province"] == "UNKNOWN"].iloc[0]
        province_total = float(provinces["recognized_revenue_vnd"].sum())
        t2 = cohort_bridge["t2"]
        text_block(ax,.10,.44,
            f"Không so sánh doanh thu theo tỉnh/thành: UNKNOWN chiếm {fpct(unknown['recognized_revenue_vnd']/province_total,2)} trên dashboard DEV+test ({fint(unknown['orders'])} đơn). Riêng DEV, tỉnh rỗng ở {fpct(t2['province_missing_rate_percent']/100,2)} đơn và chiếm {fpct(t2['missing_province_revenue_share_percent']/100,2)} doanh thu; chưa suy ra nguyên nhân nghiệp vụ.",width=102,fontsize=8.6)
        text_block(ax,.10,.32,
            "Snapshot có 247 tên mặt hàng quan sát ở bảng sản phẩm; `product_profile.csv` mô tả support, quà theo dòng, ngày đầu/cuối và tháng bán. Tên sản phẩm không được dùng để xác định quà. 476 đơn bán thử 2022 được giữ riêng. Do chiết khấu và điều chỉnh ở cấp đơn, báo cáo chỉ nêu số đơn/dòng theo sản phẩm, không gán doanh thu ghi nhận cho sản phẩm.",width=102,fontsize=9.2)
        ax.text(.10,.09,"Nguồn số liệu: outputs/tables/dashboard_sales_monthly.csv, dashboard_sales_province.csv, dashboard_product_orders.csv.",fontsize=7.8,color="#61736D",transform=ax.transAxes)
        pdf.savefig(fig); plt.close(fig)

        # 8. Preprocessing and gift rules
        fig, ax = fresh_page(pdf, 8, "6. Tiền xử lý và chống rò rỉ", "Bảng 2. Nhận diện gift line theo dữ liệu, không theo danh sách tên")
        line = combo["gift_line_audit"]
        src = line["line_count_by_source"]
        rows = [["Nguồn phân loại", "Số dòng DEV"], ["flag API đã xác minh", str(src["flag"])],
                ["Giá thực bằng 0 / giảm 100%", str(src["zero_price"])],
                ["Suy luận subset sum duy nhất", f"{src['inferred_subset']} · độ tin cậy thấp"],
                ["Không phải quà", str(src["not_gift"])], ["Tổng", str(line["line_count"])]]
        add_table(ax,[.10,.59,.80,.26],rows[1:],["Nguồn phân loại","Số dòng DEV"],col_widths=[.56,.44],fontsize=8.7)
        text_block(ax,.10,.53,
            f"Trường `is_bonus_product` có mặt ở toàn bộ {fint(line['line_count'])} dòng nhưng không bật; vì vậy không sinh nhãn `flag`. Quy tắc 0-price/giảm 100% được áp trước subset sum. Suy luận subset xét tối đa 6 dòng và chỉ nhận khi có đúng một tập con khớp total_discount. Không dùng tên, giá thấp hay support.",width=100,fontsize=9.2)
        y=text_block(ax,.10,.40,
            f"Quy mô: {fint(combo['status3_dev_orders'])} đơn status 3; {fint(combo['status3_order_gifts_excluded_from_baskets'])} đơn quà cấp đơn bị loại; {fint(combo['eligible_baskets_before_gift_line_removal'])} giỏ trước và {fint(combo['eligible_baskets_after_all_gift_line_removal'])} sau loại dòng quà; {fint(combo['missing_product_id_line_count'])} dòng thiếu product_id. Ngưỡng đơn lớn là phân vị 90 DEV = {fvnd(combo['order_value_thresholds_vnd']['p90'])}.",width=100,fontsize=9.2)
        text_block(ax,.10,y-.03,
            f"Split thời gian: DEV trước T={dates['start_inclusive']}; test [{dates['start_inclusive']}, {dates['end_exclusive']}). Hash split/config được lưu ở config/split.lock.json và amendment 05. Nhật ký tiền kiểm ghi 2 lần eligibility_count, không có truy vấn đọc nhãn hay hành vi test trước khi khóa mở. Huỷ/hoàn không fit: fold dương 30/13/6/1/18, có fold dưới 20 mẫu.",width=100,fontsize=9.2)
        pdf.savefig(fig); plt.close(fig)

        # 9. Supervised dev
        fig, ax = fresh_page(pdf, 9, "7. Học có giám sát trên DEV", "Bảng 3. So sánh OOF theo 5 fold thời gian; ngưỡng 0,5")
        models=dev["repurchase_features_v2"]["models"]
        model_rows=[]
        for key,label,param in [
            ("majority_baseline","Baseline","—"),
            ("logistic_regression","Logistic Regression feature-v2",f"C={fnum(models['logistic_regression']['selected_parameters']['C'],1)}"),
            ("decision_tree","Decision Tree",f"max_depth={models['decision_tree']['selected_parameters']['max_depth']}"),
            ("random_forest","Random Forest",f"depth={models['random_forest']['selected_parameters']['max_depth']}; leaf={models['random_forest']['selected_parameters']['min_samples_leaf']}"),
        ]:
            m=models[key]["out_of_fold_metrics"]
            model_rows.append([label,param,fnum(m["roc_auc"]),fnum(m["pr_auc"]),fnum(m["f1"])])
        primary_oof=dev_primary["best_model_oof_metrics"]
        model_rows.insert(1,["Logistic Regression C=10 (chính, D-005)","C=10",fnum(primary_oof["roc_auc"]),fnum(primary_oof["pr_auc"]),fnum(primary_oof["f1"])])
        add_table(ax,[.09,.54,.82,.29],model_rows,["Mô hình","Cấu hình khóa","ROC-AUC","AP/PR-AUC","F1"],col_widths=[.37,.18,.15,.15,.12],fontsize=7.5)
        y=text_block(ax,.10,.49,
            f"Vòng DEV feature-v2 bổ sung có {fint(dev['repurchase_features_v2']['sample_count'])} mẫu nhãn qua nhiều mốc T, {fint(dev['repurchase_features_v2']['positive_count'])} dương ({fpct(dev['repurchase_features_v2']['positive_rate'])}). Ứng viên Logistic Regression feature-v2 có C={fnum(models['logistic_regression']['selected_parameters']['C'],1)} được chọn trong vòng bổ sung theo PR-AUC trung bình 5 fold. OOF pooled: ROC-AUC {fnum(dev_lr['roc_auc'],4)}, AP {fnum(dev_lr['pr_auc'],4)}; CI 95% ROC [{fnum(dev['repurchase_features_v2']['selected_model_bootstrap_ci']['roc_auc_95_ci'][0],4)}; {fnum(dev['repurchase_features_v2']['selected_model_bootstrap_ci']['roc_auc_95_ci'][1],4)}], CI AP [{fnum(dev['repurchase_features_v2']['selected_model_bootstrap_ci']['pr_auc_95_ci'][0],4)}; {fnum(dev['repurchase_features_v2']['selected_model_bootstrap_ci']['pr_auc_95_ci'][1],4)}].",
            width=102,fontsize=9.2)
        text_block(ax,.10,y-.025,
            f"Mô hình chính vẫn là Logistic Regression C=10 theo D-005; v2 C=0,1 là khảo sát bổ sung, không thay vai trò mô hình chính. DEV OOF ROC-AUC C=10 là {fnum(primary_oof['roc_auc'],4)}, gần mức ngẫu nhiên; feature-v2 là {fnum(dev_lr['roc_auc'],4)}. DEV chưa xác nhận tín hiệu xếp hạng rõ. Mọi preprocessing chỉ fit trong train fold; test không dùng để chọn cấu hình.",width=100,fontsize=9.2)
        pdf.savefig(fig); plt.close(fig)

        # 10. Test
        fig, ax = fresh_page(pdf, 10, "8. Đánh giá test một lần", "Bảng 4. Mô hình và ngưỡng đã đóng băng; không fit hoặc chọn lại")
        test_rows=[]
        for key,label in [("majority_baseline","Baseline"),("amendment_03_logistic_regression","C=10 — mô hình chính"),("repurchase_features_v2_logistic_regression","feature-v2 C=0,1 — bổ sung")]:
            m=test["models"][key]
            ci=test["bootstrap_95_ci"][key]["metrics_95_ci"]
            matrix=m["confusion_matrix_tn_fp_fn_tp"]
            cm="/".join(f"{int(value):,}".replace(",", ".") for row in matrix for value in row)
            test_rows.append([label,fnum(m["precision"]),fnum(m["recall"]),fnum(m["f1"]),fnum(m["roc_auc"]),fnum(m["average_precision"]),cm])
        add_table(ax,[.08,.64,.84,.22],test_rows,["Mô hình","Prec","Recall","F1","ROC","AP","TN/FP/FN/TP"],col_widths=[.34,.08,.08,.08,.08,.08,.26],fontsize=6.7)
        c10=test["models"]["amendment_03_logistic_regression"]
        c10_ci=test["bootstrap_95_ci"]["amendment_03_logistic_regression"]["metrics_95_ci"]
        c10_delta=test["bootstrap_95_ci"]["paired_average_precision_delta_vs_baseline_95_ci"]["amendment_03_logistic_regression"]
        v2_delta=test["bootstrap_95_ci"]["paired_average_precision_delta_vs_baseline_95_ci"]["repurchase_features_v2_logistic_regression"]
        text_block(ax,.09,.545,
            f"Cohort {fint(test['cohort']['eligible_customers_with_pre_T_purchase'])} khách, {fint(test['cohort']['test_positive_customers'])} dương; prevalence DEV/test {fpct(test['cohort']['development_positive_rate'])}/{fpct(test['cohort']['test_positive_rate'])}. Logistic Regression C=10 — mô hình chính theo D-005: ROC-AUC {fnum(c10['roc_auc'],4)} (CI {fnum(c10_ci['roc_auc']['lower'],4)}–{fnum(c10_ci['roc_auc']['upper'],4)}), AP {fnum(c10['average_precision'],4)} (CI {fnum(c10_ci['average_precision']['lower'],4)}–{fnum(c10_ci['average_precision']['upper'],4)}), ΔAP {fsigned(c10['average_precision']-test['models']['majority_baseline']['average_precision'])} (CI {fsigned(c10_delta['lower'])}–{fsigned(c10_delta['upper'])}).",
            width=104,fontsize=8.4)
        text_block(ax,.09,.455,
            f"Logistic Regression feature-v2 C=0,1 — khảo sát bổ sung theo Amendment 04; không thay mô hình chính: ROC-AUC {fnum(test_v2['roc_auc'],4)} (CI {fnum(test_ci['roc_auc']['lower'],4)}–{fnum(test_ci['roc_auc']['upper'],4)}), AP {fnum(test_v2['average_precision'],4)} (CI {fnum(test_ci['average_precision']['lower'],4)}–{fnum(test_ci['average_precision']['upper'],4)}), ΔAP {fsigned(test_v2['average_precision']-test['models']['majority_baseline']['average_precision'])} (CI {fsigned(v2_delta['lower'])}–{fsigned(v2_delta['upper'])}). Bootstrap paired theo khách, 2.000 lượt; ngưỡng phân loại 0,5.",width=104,fontsize=8.4)
        text_block(ax,.09,.335,
            "Ngưỡng tín hiệu được ghi cho các classifier trong Amendment 05: cận dưới CI ROC-AUC > 0,55 và cận dưới CI ΔAP > 0; các CI aggregate của cả hai cấu hình thỏa các cận trong lần chạy thực tế. Vượt ngưỡng về mặt số liệu không xác nhận tuân thủ giao thức do sai khác ngày T.",width=104,fontsize=8.4)
        text_block(ax,.09,.225,
            f"DEV OOF ROC-AUC C=10 là {fnum(primary_oof['roc_auc'],4)}, gần mức ngẫu nhiên; ROC-AUC test {fnum(c10['roc_auc'],4)} chỉ là tín hiệu yếu chưa được DEV xác nhận. Không kết luận mô hình hoạt động tốt. Test đã mở; không dùng kết quả này để tinh chỉnh hoặc chọn lại mô hình. Cấu hình ghi >T, evaluator dùng [T,end) (gồm ngày T); ảnh hưởng chưa xác định; đây là kết quả số liệu của lần chạy thực tế, không phải khẳng định tuân thủ đầy đủ giao thức, không gọi là 'đạt cổng ghi trước'.",width=104,fontsize=8.3)
        pdf.savefig(fig); plt.close(fig)

        # 11. Segmentation
        fig, ax = fresh_page(pdf, 11, "9. Học không giám sát: phân khúc", "Bảng 5. K-Means và quy tắc nghiệp vụ được đọc song song")
        k=seg["chosen_k"]
        krows=test_segments[(test_segments["scheme"]==f"K={k}") & (test_segments["cohort"].isin(["development","test_pre_T"]))]
        group_rows=[]
        for group in sorted(krows["segment"].astype(str).unique()):
            devrow=krows[(krows["segment"].astype(str)==group)&(krows["cohort"]=="development")].iloc[0]
            testrow=krows[(krows["segment"].astype(str)==group)&(krows["cohort"]=="test_pre_T")].iloc[0]
            group_rows.append([group,str(int(devrow["customers"])),fpct(devrow["customer_share"]),fvnd(devrow["pre_T_recognized_revenue_vnd"]),
                               fvnd(testrow["test_window_recognized_revenue_vnd"]),fnum(devrow["mean_frequency"],2),fvnd(devrow["mean_monetary_vnd"])])
        add_table(ax,[.07,.57,.86,.25],group_rows,["K-means","Khách scoring (5.169)","Tỷ trọng","Doanh thu trước T","Doanh thu test","F TB","Monetary TB"],col_widths=[.11,.15,.11,.18,.16,.10,.19],fontsize=7.2)
        text_block(ax,.09,.51,
            f"Bảng dùng cohort scoring: 4.530/5.169 khách (87,6%) có một đơn; DEV status 3 là 4.526/5.174 (87,5%). K={k} được chọn, silhouette={fnum(seg['chosen_silhouette'])}. Quy tắc nghiệp vụ có {fint(sum(seg['rule_segment_counts'].values()))} khách; proxy giá trị lớn có {fint(seg['business_like_proxy']['customers'])} khách theo ngưỡng p99, không xác minh pháp nhân.",width=100,fontsize=9.1)
        text_block(ax,.09,.38,
            "K=2 là phân đoạn mô tả theo tần suất mua (một lần / lặp lại); chưa chứng minh hai nhóm có ý nghĩa kinh doanh hay giúp ra quyết định tốt hơn. Không fit lại trên test: frozen segmenter được áp lên cùng hồ sơ trước T. Khoảng cách phân phối bằng 0 vì vậy không chứng minh hành vi tương lai ổn định. Doanh thu test chỉ báo riêng, không cập nhật tâm cụm.",width=100,fontsize=9.1)
        pdf.savefig(fig); plt.close(fig)

        # 12. Association
        fig, ax = fresh_page(pdf, 12, "10. Luật kết hợp và combo", "Bảng 6. Chỉ giữ luật đã đóng băng trước test")
        top=combos.sort_values("support",ascending=False).head(8)
        rows=[]
        for r in top.itertuples():
            short=(str(r.combo_name)[:42]+"…") if len(str(r.combo_name))>43 else str(r.combo_name)
            rows.append([short,fpct(r.dev_support),fpct(r.support),fnum(r.dev_lift,2),fnum(r.lift,2)])
        add_table(ax,[.06,.57,.88,.27],rows,["Cặp sản phẩm","Support DEV","Support test","Lift DEV","Lift test"],col_widths=[.50,.13,.13,.12,.12],fontsize=7.4)
        text_block(ax,.08,.50,
            f"Phân tích giỏ: {fint(combo['eligible_baskets_before_gift_line_removal'])} trước và {fint(combo['eligible_baskets_after_all_gift_line_removal'])} sau loại quà. So sánh nhạy cảm gồm mọi dòng; chỉ loại flag/zero_price; và loại mọi nguồn quà, tại min_support 0,01 và 0,05. {fint(combo['main_combo_count'])} cặp chính ổn định ở ít nhất 4/6 ô; {fint(test['association_rules']['test_lift_gt_1_count'])}/{fint(test['association_rules']['frozen_combo_count'])} cặp frozen có lift > 1 trong test. Test có {fint(test['association_rules']['test_eligible_basket_count'])} giỏ đủ điều kiện; không chọn luật mới.",width=100,fontsize=9.0)
        text_block(ax,.08,.355,
            "Support mùa vụ tính trong tháng chồng lấp của mỗi cặp; nhãn mùa chỉ gắn khi quan sát tập trung quanh ngày lễ theo cửa sổ đã đăng ký. DEV có một mùa Tết trọn vẹn, chưa đủ để suy ra chu kỳ năm. Giá niêm yết gộp là mô tả; không có giá vốn, không phân bổ chiết khấu, không suy ra hiệu quả lợi nhuận. Association = đồng xuất hiện, không phải nhân quả.",width=100,fontsize=9.0)
        ax.text(.08,.20,"Nguồn đầy đủ: outputs/tables/combos_v2.csv, seasonal_pair_metrics.csv, test_combos_frozen.csv.",fontsize=8,color="#61736D",transform=ax.transAxes)
        pdf.savefig(fig); plt.close(fig)

        # 13. Conclusions
        fig, ax = fresh_page(pdf, 13, "11. Kết luận và giới hạn", "Kết quả học thuật cần được đọc cùng điều kiện dữ liệu")
        section_label(ax,.09,.86,"Kết luận")
        y=text_block(ax,.09,.825,
            f"Quy trình tạo kho Star Schema và kiểm toán nghiệp vụ có split thời gian, hash và nhật ký amendment. K=2 là phân đoạn mô tả theo tần suất mua (một lần / lặp lại), chưa chứng minh ý nghĩa kinh doanh. 24 combo chính được khóa theo quy tắc ít nhất 4/6 ô. ROC-AUC DEV OOF C=10 là {fnum(primary_oof['roc_auc'],4)}, gần ngẫu nhiên; ROC-AUC test {fnum(c10['roc_auc'],4)} là tín hiệu yếu chưa được DEV xác nhận, không đủ để kết luận mô hình hoạt động tốt. Test đã mở; không tinh chỉnh theo kết quả test. Cấu hình ghi >T, evaluator dùng [T,end) (gồm ngày T); ảnh hưởng chưa xác định. Xem docs/test_provenance_note.md.",width=102,fontsize=9.0)
        section_label(ax,.09,y-.025,"Hạn chế")
        text_block(ax,.09,y-.06,
            f"• Khoảng hiệu dụng khoảng 18 tháng và chỉ có một Tết trọn vẹn trong DEV.\n• 91,92% doanh thu theo tỉnh/thành mang nhãn UNKNOWN; không so sánh địa lý.\n• Thiếu dữ liệu phản hồi có nhãn; không thực hiện bài phân loại phản hồi.\n• 903 dòng inferred_subset là suy luận có thể gán nhầm; cờ API không bật.\n• Không có giá vốn nên không thể kết luận lợi nhuận combo.\n• Status hiện tại không phải lịch sử trạng thái; doanh thu ghi nhận theo xác nhận nghiệp vụ.\n• Một cửa sổ test không chứng minh khả năng tổng quát qua nhiều mùa.",width=100,fontsize=9.4)
        pdf.savefig(fig); plt.close(fig)

        # 14. Reproducibility / glossary
        fig, ax = fresh_page(pdf, 14, "Phụ lục A. Chạy lại và chú giải", "Các đầu ra quan trọng nằm trong repo; test lock cấm đánh giá lần hai")
        section_label(ax,.09,.86,"Lệnh chuẩn trên Windows")
        ax.text(.10,.82,r".venv\Scripts\python scripts\run_all.py",fontsize=11,color="#183D36",family="monospace",transform=ax.transAxes)
        text_block(ax,.09,.775,
            "Sau khi có test_opened.lock.json, runner chỉ xác minh hash/split, pytest và PII; không fit hoặc chạy evaluator test. Không chạy scripts/evaluate_test_once.py lần nữa. Dashboard: .venv\\Scripts\\python -m streamlit run src/app/streamlit_app.py; chạy offline từ outputs/.",width=104,fontsize=9.1)
        section_label(ax,.09,.655,"File bàn giao")
        text_block(ax,.09,.62,
            "README.md · config/split.yaml và split.lock.json · config/amendment_05_test_open.yaml · outputs/metrics/test_eval.json · docs/test_report.md · outputs/tables/product_profile.csv · docs/product_profile_top20.md · src/app/streamlit_app.py · docs/qa.md · docs/handover.md · docs/demo_script.md.",width=101,fontsize=8.9)
        section_label(ax,.09,.485,"Thuật ngữ")
        text_block(ax,.09,.45,
            "Snapshot: bản dữ liệu có checksum. ETL: trích xuất, biến đổi, nạp. Star Schema: fact giao dịch nối dimension. Grain: mức chi tiết của một dòng dữ liệu. HMAC: băm có khóa để giả danh ID. RFM: Recency, Frequency, Monetary. Support: tỷ lệ giỏ chứa cặp. Confidence: tỷ lệ giỏ có B trong các giỏ có A. Lift: mức đồng xuất hiện so với độc lập thống kê; lift lớn hơn 1 không chứng minh nhân quả. ROC-AUC: xếp hạng dương/âm theo ngưỡng. PR-AUC: precision-recall, nhạy với lớp hiếm. Không dừng: phân phối/quan hệ thay đổi theo thời gian.",width=103,fontsize=8.9)
        pdf.savefig(fig); plt.close(fig)

        # 15. Decision log
        fig, ax = fresh_page(pdf, 15, "Phụ lục B. Nhật ký quyết định", "Mốc và file nguồn để giải thích lựa chọn trước hội đồng")
        decisions=[
            ["D-005","Giữ Logistic Regression C=10 làm mô hình chính; v2 là khảo sát bổ sung."],
            ["Amendment 01","Mốc mở cửa 2024-04-01; loại bán thử 2022 khỏi hành vi."],
            ["Amendment 03","Định nghĩa doanh thu ghi nhận/status 3; giữ price_adjustment; audit độ nhạy A/B."],
            ["Amendment 04","Một vòng feature v2 trên DEV; không chọn lại sau kết quả."],
            ["Amendment 05","Quà theo dòng; subset sum low-confidence; 24 combo đóng băng trước test."],
            ["D-010","Ghi rõ `>T` so với `[T,end)` thực tế; ảnh hưởng chưa xác định."],
            ["D-019/020","Cầu 5.499 → 5.174 → 5.169 đã đếm trực tiếp, dư 0; EDA DEV only, notebook fit đóng băng."],
            ["D-021/022","Diễn giải test có caveat thống nhất; chưa chạy chẩn đoán anchor trên DEV."],
            ["Cancel/refund","Không fit vì một số fold có dưới 20 dương; không thử lại."],
        ]
        add_table(ax,[.08,.58,.84,.25],decisions,["Quyết định","Nội dung"],col_widths=[.24,.76],fontsize=8.2)
        text_block(ax,.09,.50,
            "Lần chạy evaluator đầu dừng trước khi tạo khóa do cấu hình ngày YAML; không đọc nhãn/hành vi test và không tiêu thụ lần mở. Lần thành công là lần duy nhất, khóa test_open_count=1. Log hậu mở có đúng hai loại đọc cần thiết: nhãn và hành vi; không ghi giá trị thô hoặc ID khách ra kết quả.",width=102,fontsize=9.1)
        text_block(ax,.09,.365,
            "Tài liệu theo dõi: docs/decisions.md, docs/PROGRESS.md, docs/test_report.md, outputs/logs/test_eval_access.jsonl, config/amendment_05_test_open.yaml và config/amendment_05_test_open.lock.json. File đối chiếu tiền đã chuyển vào data/restricted/quarantine/.",width=101,fontsize=9.1)
        ax.text(.09,.20,"Hạn nộp 2026-10-27; thời lượng chính thức và rubric chưa có trong hồ sơ.",fontsize=8.5,color="#61736D",transform=ax.transAxes)
        pdf.savefig(fig); plt.close(fig)

    print(f"Wrote {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUT, help="Destination PDF path")
    parser.add_argument("--font", help="Optional font file path; otherwise auto-discover an installed font")
    args = parser.parse_args()
    main(output_path=args.output, font_override=args.font)
