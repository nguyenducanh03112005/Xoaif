"""Build a 15-slide print PDF from frozen aggregate project outputs."""
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
    ax.text(.94, .043, f"{number:02d} / 15", fontsize=8, color=COLORS["muted"], ha="right", transform=ax.transAxes)
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
    seg = read_json("day2_segmentation.json")
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
        ax.text(.08, .44, "Nhiều bảng Pancake POS  ·  Lịch ngày lễ công khai", fontsize=14, color="#E4F0EB", transform=ax.transAxes)
        ax.text(.08, .20, "Báo cáo dự án / bảo vệ cuối kỳ  ·  26/10/2026", fontsize=11, color="white", transform=ax.transAxes)
        ax.text(.08, .055, "Kết quả được trình bày cùng giới hạn provenance, cohort và dữ liệu.", fontsize=9, color="#CDE2D8", transform=ax.transAxes)
        pdf.savefig(fig); plt.close(fig)

        # 2. Questions and scope
        fig, ax = slide(pdf, 2, "Từ dữ liệu bán hàng đến câu trả lời kinh doanh", "Phân tích tập trung vào giao dịch, khách hàng và giỏ sản phẩm")
        card(ax, .08, .62, .24, .20, "Xu hướng", "Doanh số", "theo thời gian")
        card(ax, .38, .62, .24, .20, "Hành vi", "Khách hàng", "mua một lần hay quay lại")
        card(ax, .68, .62, .24, .20, "Sản phẩm", "Giỏ hàng", "món thường xuất hiện cùng nhau")
        heading(ax, .09, .49, "Mục tiêu")
        body(ax, .09, .42, "Tổ chức dữ liệu theo quy tắc thống nhất, phân tích các câu hỏi và trình bày kết quả để hỗ trợ tìm hiểu hoạt động bán hàng.", size=13, width=.80)
        pdf.savefig(fig); plt.close(fig)

        # 3. Architecture
        fig, ax = slide(pdf, 3, "Quy trình phân tích dữ liệu", "Một quy trình từ dữ liệu nguồn đến thông tin dễ đọc")
        items = [
            ("1 · Dữ liệu", "Pancake POS\nđơn · sản phẩm · khách"),
            ("2 · Chuẩn hóa", "ngày · tiền\nquy tắc nghiệp vụ"),
            ("3 · Kho", "DuckDB\nPandas"),
            ("4 · Phân tích", "scikit-learn\nmlxtend"),
            ("5 · Kết quả", "Streamlit\nbáo cáo · slide"),
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
        body(ax, .07, .32, "Các bảng giao dịch được chuẩn hóa và kết hợp để tạo chỉ số khách hàng, đặc trưng cho mô hình và giỏ sản phẩm.", size=12, width=.82)
        body(ax, .07, .20, "Công cụ chính: Python, Pandas, DuckDB, scikit-learn, mlxtend và Streamlit.", size=11, color=COLORS["muted"], width=.82)
        pdf.savefig(fig); plt.close(fig)

        # 4. Data scope
        fig, ax = slide(pdf, 4, "Phạm vi dữ liệu phân tích", "Nguồn Pancake POS · giao dịch trong giai đoạn hoạt động của cửa hàng")
        card(ax, .08, .56, .36, .27, "Snapshot dữ liệu", "12.011", "đơn hàng")
        card(ax, .56, .56, .36, .27, "Tập DEV", "6.517", "đơn hàng · 01/04/2024 đến trước 22/10/2025")
        heading(ax, .09, .43, "Quy tắc sử dụng")
        body(ax, .09, .36, "Phân tích dùng đơn hợp lệ theo quy tắc nghiệp vụ. 6.400 đơn status 3 thuộc tập DEV được xem là đơn mua đã ghi nhận.", size=12, width=.82)
        pdf.savefig(fig); plt.close(fig)

        # 5. Data pipeline and storage
        fig, ax = slide(pdf, 5, "Từ dữ liệu nguồn đến kết quả phân tích", "Lưu trữ và trình bày theo từng lớp xử lý")
        columns=[("Dữ liệu nguồn","Pancake POS\nĐơn · khách · sản phẩm"),("Kho phân tích","DuckDB\nPython · Pandas"),("Kết quả","Chỉ số tổng hợp\nDashboard · PDF")]
        for i,(title,detail) in enumerate(columns):
            x=.08+i*.30
            patch=FancyBboxPatch((x,.47),.25,.26,boxstyle="round,pad=.012,rounding_size=.015",transform=ax.transAxes,fc=COLORS["pale"] if i%2==0 else "white",ec=COLORS["line"],lw=.8)
            ax.add_patch(patch);ax.text(x+.02,.66,title,fontsize=12,weight="bold",color=COLORS["green"],transform=ax.transAxes)
            ax.text(x+.02,.58,detail,fontsize=10,color=COLORS["ink"],va="top",linespacing=1.5,transform=ax.transAxes)
        heading(ax,.09,.38,"Luồng dữ liệu")
        body(ax,.09,.31,"Giao dịch được chuẩn hóa, nối theo khóa nghiệp vụ và nạp vào kho. Định danh khách được giả danh hóa; dashboard đọc bảng tổng hợp.",size=11,width=.82)
        pdf.savefig(fig);plt.close(fig)

        # 6. Customer retention and CLV
        fig, ax = slide(pdf, 6, "Giá trị khách hàng trong 180 ngày", "Retention và CLV mô tả lịch sử mua")
        card(ax,.08,.58,.25,.24,"Retention 180 ngày","10,40%","365 / 3.508 khách đủ theo dõi")
        card(ax,.38,.58,.25,.24,"Doanh thu 180 ngày","512.934₫","trên mỗi khách")
        card(ax,.68,.58,.24,.24,"Cửa sổ","180 ngày","từ lần mua đầu")
        heading(ax,.09,.45,"Cách đọc")
        body(ax,.09,.38,"Retention đo tỷ lệ có giao dịch mua lại theo định nghĩa dự án. CLV ở đây là doanh thu lịch sử, không phải dự báo hay lợi nhuận.",size=12,width=.82)
        pdf.savefig(fig);plt.close(fig)

        # 7. RFM segmentation
        fig, ax = slide(pdf, 7, "Phân khúc khách hàng theo RFM", "Recency · Frequency · Monetary")
        card(ax,.08,.57,.24,.23,"Thuật toán","K-Means","học nhóm từ đặc trưng chuẩn hóa")
        card(ax,.38,.57,.24,.23,"Số nhóm","K = 2","mô tả hành vi mua")
        card(ax,.68,.57,.24,.23,"Hành vi phổ biến","Mua một lần","so với mua lặp lại")
        heading(ax,.09,.44,"Kết quả")
        body(ax,.09,.38,"Trong DEV, 87,5% khách có một đơn. K=2 chủ yếu tách khách mua một lần và mua lặp lại.",size=12,width=.82)
        body(ax,.09,.21,"Cụm giúp mô tả dữ liệu; nhãn nhóm không phải kết luận về giá trị hoặc nguy cơ rời bỏ.",size=11,color=COLORS["muted"],width=.82)
        pdf.savefig(fig);plt.close(fig)

        # 8. Supervised method
        fig, ax = slide(pdf, 8, "Xếp hạng khả năng mua lại", "Mô hình học từ lịch sử mua trước thời điểm dự đoán")
        card(ax, .08, .58, .24, .22, "Bài toán", "Phân loại", "có mua lại / chưa ghi nhận mua lại")
        card(ax, .38, .58, .24, .22, "Mô hình", "Logistic", "Regression cho điểm xác suất")
        card(ax, .68, .58, .24, .22, "Chân trời", "180 ngày", "sau mốc dự đoán")
        heading(ax, .09, .45, "Đầu vào chính")
        body(ax, .09, .39, "Recency, Frequency, Monetary, giá trị đơn, số sản phẩm và nhịp mua. Các đặc trưng được tính từ dữ liệu trước mốc T.", size=12, width=.82)
        body(ax, .09, .22, "Kết quả là điểm xếp hạng để phân tích hành vi; không tự động quyết định cách phục vụ khách.", size=11, color=COLORS["muted"], width=.82)
        pdf.savefig(fig); plt.close(fig)

        # 9. Model roles
        fig, ax = slide(pdf, 9, "Tạo đặc trưng và nhãn mua lại", "Mỗi mẫu mô tả một khách tại một mốc thời gian")
        card(ax, .08, .57, .25, .23, "Đặc trưng", "RFM + giỏ", "tính từ giao dịch lịch sử")
        card(ax, .38, .57, .25, .23, "Nhãn", "Mua lại", "giao dịch hợp lệ sau mốc T")
        card(ax, .68, .57, .24, .23, "Cửa sổ", "180 ngày", "cùng quy tắc cho mọi mẫu")
        heading(ax, .09, .44, "Vì sao chia theo thời gian?")
        body(ax, .09, .38, "Mô hình học từ các mốc cũ rồi được đánh giá trên mốc mới hơn. Như vậy cách đánh giá gần với việc dự đoán khách trong tương lai.", size=12, width=.82)
        body(ax, .09, .21, "Nhãn được tạo từ kết quả giao dịch quan sát được, không gán thủ công.", size=11, color=COLORS["muted"], width=.82)
        pdf.savefig(fig); plt.close(fig)

        # 10. Basket method
        fig, ax = slide(pdf, 10, "Tìm sản phẩm thường xuất hiện cùng giỏ", "FP-Growth tìm tập phổ biến; các thước đo giúp xếp hạng cặp")
        card(ax, .08, .57, .24, .23, "Support", "Tần suất", "tỷ lệ giỏ có cặp")
        card(ax, .38, .57, .24, .23, "Confidence", "Điều kiện", "A có thì B xuất hiện bao nhiêu")
        card(ax, .68, .57, .24, .23, "Lift", "So sánh", "với mức đồng xuất hiện nền")
        heading(ax, .09, .44, "Ứng dụng")
        body(ax, .09, .38, "Các cặp sản phẩm có thể gợi ý cách trưng bày hoặc bundle để cửa hàng cân nhắc thử nghiệm.", size=12, width=.82)
        body(ax, .09, .21, "Đồng xuất hiện không chứng minh nguyên nhân hay lợi nhuận.", size=11, color=COLORS["muted"], width=.82)
        pdf.savefig(fig); plt.close(fig)

        # 11. Basket results
        fig, ax = slide(pdf, 11, "Các cặp sản phẩm gợi ý cách kết hợp", "Các cặp được xếp hạng từ giỏ hàng hợp lệ")
        heading(ax, .08, .80, "Đầu vào")
        body(ax, .08, .73, "Đơn hàng và dòng sản phẩm\nGiỏ hàng hợp lệ\nThuật toán FP-Growth\nSupport, confidence và lift", size=12, width=.37)
        heading(ax, .53, .80, "Kết quả")
        body(ax, .53, .73, "Các cặp sản phẩm được xếp hạng theo tần suất và mức độ đồng xuất hiện trong giỏ.", size=12, width=.37)
        heading(ax, .53, .48, "Ứng dụng")
        body(ax, .53, .41, "Có thể hình thành giả thuyết bundle hoặc cách trưng bày sản phẩm.", size=11, width=.37)
        pdf.savefig(fig); plt.close(fig)

        # 12. Dashboard
        fig, ax = slide(pdf, 12, "Dashboard kết quả phân tích", "Các trang giúp chuyển từ tổng quan sang hành vi chi tiết")
        heading(ax, .08, .80, "Tổng quan và khách hàng")
        body(ax, .08, .73, "Doanh số theo thời gian\nPhân khúc theo RFM\nGiá trị và nhịp mua lại", size=13, width=.37)
        heading(ax, .53, .80, "Sản phẩm và mô hình")
        body(ax, .53, .73, "Sản phẩm thường cùng giỏ\nChất lượng dữ liệu\nKhả năng mua lại", size=13, width=.37)
        body(ax, .08, .30, "Demo: tổng quan doanh số → phân khúc khách → combo. Tab mô hình có thể mở khi được hỏi về ML.", size=12, color=COLORS["muted"], width=.82)
        pdf.savefig(fig); plt.close(fig)

        # 13. Project products
        fig, ax = slide(pdf, 13, "Sản phẩm dự án", "Từ dữ liệu đến phân tích và cách trình bày")
        rows = [["Dữ liệu", "Giao dịch, khách hàng và sản phẩm"],
                ["Phân tích", "Xu hướng bán hàng, retention, CLV và RFM"],
                ["Mua lại và giỏ hàng", "Logistic Regression và FP-Growth"],
                ["Trình bày", "Dashboard, báo cáo và slide thuyết trình"]]
        add_table(ax, [.08, .34, .84, .46], rows, ["Phần", "Đầu ra"], widths=[.30, .70], fontsize=11)
        body(ax, .08, .25, "Kết quả giúp hiểu hoạt động bán hàng và hình thành giả thuyết tiếp theo.", size=12, color=COLORS["teal"], weight="bold", width=.82)
        pdf.savefig(fig); plt.close(fig)

        # 14. Limits and preparation
        fig, ax = slide(pdf, 14, "Demo dashboard", "Đi từ kết quả tổng quan đến ví dụ cụ thể")
        heading(ax, .08, .80, "01 · Tổng quan")
        body(ax, .08, .73, "Chọn khoảng thời gian và đọc doanh thu ghi nhận, số đơn, xu hướng.", size=12, width=.36)
        heading(ax, .53, .80, "02 · Phân khúc")
        body(ax, .53, .73, "So sánh nhóm khách theo Recency, Frequency, Monetary.", size=12, width=.36)
        heading(ax, .08, .48, "03 · Combo")
        body(ax, .08, .41, "Xem cặp sản phẩm cùng giỏ và các thước đo support, confidence, lift.", size=12, width=.36)
        heading(ax, .53, .48, "04 · Hỏi đáp")
        body(ax, .53, .41, "Mở phần mô hình để giải thích đặc trưng, nhãn và cách đánh giá.", size=12, width=.36)
        pdf.savefig(fig); plt.close(fig)

        # 15. Operations and refresh
        fig, ax = slide(pdf, 15, "Kết luận", "Dữ liệu bán hàng được chuyển thành kết quả dễ khám phá")
        heading(ax, .08, .80, "Đã thực hiện")
        body(ax, .08, .73, "Chuẩn hóa giao dịch, phân tích doanh số và hành vi khách, tạo phân khúc RFM, thử mô hình mua lại và khai phá giỏ hàng.", size=12, width=.37)
        heading(ax, .53, .80, "Đầu ra")
        body(ax, .53, .73, "Dashboard tương tác, báo cáo và bộ slide giúp trình bày kết quả và cách làm.", size=12, width=.37)
        body(ax, .08, .43, "Các kết quả hỗ trợ hiểu dữ liệu và hình thành giả thuyết để cửa hàng cân nhắc kiểm chứng.", size=13, color=COLORS["green"], weight="bold", width=.82)
        ax.text(.08, .20, "Cảm ơn. Mời thầy/cô đặt câu hỏi.", fontsize=13, color=COLORS["muted"], transform=ax.transAxes)
        pdf.savefig(fig); plt.close(fig)

    print(f"Wrote {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUT, help="Destination print PDF path")
    parser.add_argument("--font", help="Optional font file path; otherwise auto-discover an installed font")
    args = parser.parse_args()
    build(output_path=args.output, font_override=args.font)
