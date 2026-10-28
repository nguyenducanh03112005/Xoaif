"""Build the concise project-facing Vietnamese final report."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch, Rectangle

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "report" / "xoaif_report.pdf"
GREEN, TEAL, INK, MUTED, PALE, LINE = "#183D36", "#176B87", "#24332F", "#61736D", "#E7F0EC", "#CAD8D2"


def configure_font():
    chosen = os.environ.get("XOAIF_REPORT_FONT")
    if chosen:
        font_manager.fontManager.addfont(chosen)
        family = font_manager.FontProperties(fname=chosen).get_name()
    else:
        family = next((font_manager.FontProperties(fname=font_manager.findfont(n)).get_name()
                       for n in ("Arial", "Liberation Sans", "DejaVu Sans")), "DejaVu Sans")
    plt.rcParams.update({"font.family": family, "pdf.fonttype": 42, "axes.unicode_minus": False})


def page(pdf, n, title, subtitle=""):
    fig = plt.figure(figsize=(8.27, 11.69), facecolor="#F7FAF8")
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off()
    ax.add_patch(Rectangle((0, .91), 1, .09, transform=ax.transAxes, color=GREEN))
    ax.text(.07, .955, title, fontsize=21, weight="bold", color="white", va="center", transform=ax.transAxes)
    if subtitle: ax.text(.08, .875, subtitle, fontsize=10, color=MUTED, va="top", transform=ax.transAxes)
    ax.plot([.07,.93],[.06,.06],color=LINE,lw=.8,transform=ax.transAxes)
    ax.text(.08,.035,"Xoaif Garden · Kho và khai phá dữ liệu bán hàng",fontsize=8,color=MUTED,transform=ax.transAxes)
    ax.text(.92,.035,f"{n:02d} / 09",fontsize=8,color=MUTED,ha="right",transform=ax.transAxes)
    return fig, ax


def block(ax, y, title, text, size=12):
    ax.text(.09,y,title,fontsize=14,weight="bold",color=GREEN,va="top",transform=ax.transAxes)
    chars=max(40,int(91*12/size))
    wrapped="\n".join(textwrap.fill(p,chars) for p in text.split("\n"))
    ax.text(.09,y-.045,wrapped,fontsize=size,color=INK,va="top",linespacing=1.5,transform=ax.transAxes)


def card(ax,x,y,w,h,title,detail):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=.015,rounding_size=.015",transform=ax.transAxes,fc="white",ec=LINE,lw=.8))
    ax.text(x+.025,y+h-.04,title,fontsize=12,weight="bold",color=GREEN,va="top",transform=ax.transAxes)
    ax.text(x+.025,y+h-.10,detail,fontsize=10,color=INK,va="top",wrap=True,transform=ax.transAxes)


def build(output=OUT):
    configure_font(); output.parent.mkdir(parents=True,exist_ok=True)
    with PdfPages(output,metadata={"Title":"Xoaif Garden — Báo cáo dự án","Author":"Nhóm dự án Xoaif Garden"}) as pdf:
        # 1 cover
        fig=plt.figure(figsize=(8.27,11.69),facecolor=GREEN); ax=fig.add_axes([0,0,1,1]);ax.set_axis_off()
        ax.add_patch(Rectangle((0,.15),1,.16,transform=ax.transAxes,color="#245B4C"))
        ax.text(.08,.84,"BÁO CÁO DỰ ÁN",fontsize=14,weight="bold",color="#CAE1D6",transform=ax.transAxes)
        ax.text(.08,.75,"Kho dữ liệu và\nkhai phá dữ liệu bán hàng",fontsize=28,weight="bold",color="white",va="top",linespacing=1.3,transform=ax.transAxes)
        ax.text(.08,.56,"Xoaif Garden · Pancake POS",fontsize=15,color="#E4F0EB",transform=ax.transAxes)
        ax.text(.08,.39,"Từ giao dịch bán hàng đến phân tích khách hàng,\ngiỏ sản phẩm và dashboard kết quả.",fontsize=13,color="white",linespacing=1.5,transform=ax.transAxes)
        ax.text(.08,.08,"Báo cáo tổng kết",fontsize=10,color="#CAE1D6",transform=ax.transAxes);pdf.savefig(fig);plt.close(fig)
        # 2 problem and plan
        fig,ax=page(pdf,2,"Bài toán và hướng giải quyết","Tổ chức dữ liệu để trả lời các câu hỏi bán hàng")
        card(ax,.09,.67,.25,.15,"Doanh số","Xu hướng theo thời gian")
        card(ax,.38,.67,.25,.15,"Khách hàng","Hành vi mua và quay lại")
        card(ax,.67,.67,.25,.15,"Sản phẩm","Mặt hàng thường cùng giỏ")
        block(ax,.56,"Cách tiếp cận","Lấy dữ liệu giao dịch, thống nhất quy tắc ngày, trạng thái và doanh thu; tạo kho phân tích; tính đặc trưng; áp dụng thống kê và ML; trình bày kết quả bằng dashboard và báo cáo.")
        block(ax,.33,"Sản phẩm hoàn thiện","Kho dữ liệu DuckDB, các bảng tổng hợp, phân tích khách hàng và giỏ hàng, mô hình thử nghiệm, dashboard tương tác, báo cáo PDF và slide trình bày.")
        pdf.savefig(fig);plt.close(fig)
        # 3 data
        fig,ax=page(pdf,3,"Dữ liệu và quy trình xử lý","Nguồn giao dịch chính: Pancake POS")
        steps=[("Nguồn","Đơn hàng · dòng hàng\nkhách · sản phẩm"),("Chuẩn hóa","Ngày · trạng thái\nquy tắc doanh thu"),("Lưu trữ","DuckDB\nbảng fact và dimension"),("Khai phá","RFM · Logistic\nFP-Growth"),("Kết quả","Bảng tổng hợp\nDashboard · PDF")]
        for i,(t,d) in enumerate(steps):
            x=.08+i*.18
            ax.add_patch(FancyBboxPatch((x,.63),.15,.18,boxstyle="round,pad=.01",transform=ax.transAxes,fc=PALE if i%2==0 else "white",ec=LINE))
            ax.text(x+.012,.77,t,fontsize=10,weight="bold",color=GREEN,transform=ax.transAxes)
            ax.text(x+.012,.72,d,fontsize=8.5,color=INK,va="top",transform=ax.transAxes)
        block(ax,.53,"Xử lý dữ liệu","Các bảng được nối theo khóa giao dịch/khách/sản phẩm. Thời gian được chuẩn hóa theo múi giờ nghiệp vụ. Doanh thu ghi nhận theo quy tắc đã thống nhất; đây không phải lợi nhuận.")
        block(ax,.31,"Lưu trữ","Snapshot nguồn được lưu cục bộ; dữ liệu phân tích được nạp vào DuckDB; đầu ra cho dashboard là bảng tổng hợp. CSV mẫu là dữ liệu giả lập để minh họa cấu trúc.")
        pdf.savefig(fig);plt.close(fig)
        # 4 tools
        fig,ax=page(pdf,4,"Công nghệ sử dụng","Mỗi công cụ đảm nhiệm một phần cụ thể")
        for i,(t,d) in enumerate([("Python","Điều phối xử lý và phân tích"),("Pandas","Làm sạch và tạo bảng đặc trưng"),("DuckDB","Lưu trữ và truy vấn dữ liệu"),("scikit-learn","K-Means và Logistic Regression"),("mlxtend","FP-Growth và luật kết hợp"),("Streamlit / Plotly","Dashboard tương tác")]):
            col=i%2;row=i//2;x=.09+col*.43;y=.70-row*.19
            card(ax,x,y,.38,.13,t,d)
        block(ax,.20,"Luồng tổng quát","Dữ liệu giao dịch → chuẩn hóa → kho phân tích → đặc trưng → phân tích/ML → dashboard và báo cáo.")
        pdf.savefig(fig);plt.close(fig)
        # 5 customer
        fig,ax=page(pdf,5,"Phân tích khách hàng","Đo lường giá trị lịch sử và nhóm hành vi")
        block(ax,.77,"Retention","Tỷ lệ khách có giao dịch quay lại trong cửa sổ theo dõi 180 ngày, theo định nghĩa ngày mua của dự án.")
        block(ax,.57,"CLV mô tả","Doanh thu ghi nhận trong 180 ngày đầu của khách. Đây là thống kê lịch sử, không phải dự báo giá trị tương lai hay lợi nhuận.")
        block(ax,.37,"RFM và K-Means","Recency là độ gần lần mua; Frequency là tần suất; Monetary là doanh thu. K-Means nhóm khách theo khoảng cách giữa các đặc trưng đã chuẩn hóa. Kết quả chủ yếu mô tả nhóm mua một lần và mua lặp lại.")
        block(ax,.22,"Cách dùng kết quả","Nhóm mô tả hành vi để khám phá và đặt câu hỏi.",11)
        pdf.savefig(fig);plt.close(fig)
        # 6 supervised
        fig,ax=page(pdf,6,"Mô hình mua lại","Bài toán phân loại theo một mốc thời gian")
        block(ax,.77,"Đặc trưng","Lịch sử trước mốc T: Recency, Frequency, Monetary/doanh thu, giá trị đơn, số và độ đa dạng sản phẩm, khoảng cách giữa các lần mua và đặc trưng thời gian.")
        block(ax,.55,"Nhãn","1 nếu khách có giao dịch hợp lệ trong 180 ngày sau T; 0 nếu không. Nhãn suy ra từ giao dịch, không gán thủ công. Khoảng chờ giúp cửa sổ nhãn trưởng thành.")
        block(ax,.32,"Logistic Regression","Mô hình học trọng số cho đặc trưng và chuyển tổng trọng số thành xác suất. Điểm xác suất hỗ trợ xếp hạng; hệ số thể hiện liên hệ trong mô hình, không chứng minh nguyên nhân.")
        block(ax,.22,"Đánh giá","Chia theo thời gian để mô phỏng dự đoán tương lai. Cây quyết định và Random Forest được dùng đối chiếu; cây tạo luật if/else dễ giải thích nhưng cây sâu dễ overfit. Kết quả không phải quyết định tự động cho khách.",11)
        pdf.savefig(fig);plt.close(fig)
        # 7 basket
        fig,ax=page(pdf,7,"Phân tích giỏ hàng","Tìm sản phẩm thường xuất hiện cùng nhau")
        block(ax,.77,"FP-Growth","Tìm các tập sản phẩm phổ biến trong giỏ hàng. Thuật toán dùng cấu trúc FP-tree để khai thác tập phổ biến mà không cần liệt kê mọi tổ hợp ứng viên.")
        block(ax,.55,"Ba thước đo","Support: tỷ lệ giỏ có cặp sản phẩm. Confidence: tỷ lệ giỏ có B trong các giỏ có A. Lift: confidence so với mức nền của B.")
        block(ax,.34,"Diễn giải","Các cặp thường cùng xuất hiện có thể gợi ý cách trưng bày hoặc bundle. Lift cao không chứng minh quan hệ nhân quả hay lợi nhuận.")
        block(ax,.22,"Kết quả","Các cặp ổn định được trình bày trong dashboard để người dùng xem xét.",11)
        pdf.savefig(fig);plt.close(fig)
        # 8 demo/results
        fig,ax=page(pdf,8,"Kết quả và demo","Các kết quả được trình bày trong dashboard")
        block(ax,.78,"Kết quả","Xu hướng doanh số; retention và CLV lịch sử; phân khúc RFM; điểm mua lại; các cặp sản phẩm thường cùng giỏ.")
        block(ax,.56,"Demo","1. Chọn khoảng thời gian ở tổng quan doanh số.\n2. So sánh nhóm khách theo RFM.\n3. Xem cặp sản phẩm cùng giỏ và support, confidence, lift.\n4. Mở phần mô hình khi cần giải thích ML.")
        block(ax,.27,"Cách đọc","Doanh thu là doanh thu ghi nhận theo quy tắc nghiệp vụ. Phân khúc và combo giúp khám phá mẫu; hiệu quả kinh doanh cần được kiểm chứng riêng.")
        pdf.savefig(fig);plt.close(fig)
        # 9 wrap
        fig,ax=page(pdf,9,"Tổng kết","Dự án từ dữ liệu giao dịch đến công cụ phân tích")
        block(ax,.77,"Đã giải quyết","Tổ chức dữ liệu bán hàng vào kho phân tích; tạo quy trình xử lý thống nhất; phân tích hành vi khách hàng và giỏ hàng; xây dựng dashboard và tài liệu trình bày.")
        block(ax,.53,"Giá trị sử dụng","Người xem có thể theo dõi xu hướng, hiểu các nhóm hành vi, tìm sản phẩm thường mua cùng nhau và xem cách mô hình tạo dự đoán.")
        block(ax,.30,"Giới hạn diễn giải","Mô hình và các liên hệ trong giỏ là kết quả phân tích dữ liệu hiện có. Chúng hỗ trợ đặt giả thuyết; không thay thế đánh giá nghiệp vụ hoặc thử nghiệm tác động.")
        ax.text(.09,.12,"Cảm ơn. Mời thầy/cô đặt câu hỏi.",fontsize=15,weight="bold",color=GREEN,transform=ax.transAxes)
        pdf.savefig(fig);plt.close(fig)
    print(f"Wrote {output}")


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--output",type=Path,default=OUT);args=parser.parse_args();build(args.output)
