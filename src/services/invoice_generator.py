from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from sqlalchemy.orm import Session
import os

# ✅ Register a Unicode font that supports the ₹ symbol
pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))

def get_invoice_data(order_id: int, db: Session):
    """Fetch order and related data for invoice generation (sample data for now)."""
    return {
        "invoice_no": f"INV-{order_id:05d}",
        "order_id": order_id,
        "invoice_date": "2025-11-04",
        "payment_method": "Credit Card",
        "customer_name": "John Doe",
        "items": [
            {"sr": 1, "product": "Wireless Mouse", "sku": "MSE-001", "qty": 1, "price": 599.00, "subtotal": 599.00},
            {"sr": 2, "product": "Keyboard", "sku": "KEY-002", "qty": 1, "price": 899.00, "subtotal": 899.00},
        ],
        "payment_info": {
            "id": "PMT-123456",
            "status": "Paid",
            "date": "2025-11-04",
            "reference": "TXN123456789",
        },
        "summary": {
            "subtotal": 1498.00,
            "discount": 0.00,
            "tax": 284.62,
            "shipping": 50.00,
            "total": 1832.62,
        },
    }


def generate_pdf(invoice_data: dict, file_path: str):
    """Generate invoice PDF styled for Cartify with visible ₹ sign."""
    rupee = "₹"  # Unicode rupee symbol

    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=30,
        bottomMargin=40,
    )
    elements = []
    styles = getSampleStyleSheet()

    # ✅ Modify existing Normal style instead of re-adding it
    styles["Normal"].fontSize = 10
    styles["Normal"].fontName = "HeiseiKakuGo-W5"

    # --- Custom Styles ---
    styles.add(ParagraphStyle(name="CartifyTitle", fontSize=20, fontName="HeiseiKakuGo-W5", textColor=colors.HexColor("#333333")))
    styles.add(ParagraphStyle(name="RightTitle", fontSize=18, fontName="HeiseiKakuGo-W5", alignment=2))
    styles.add(ParagraphStyle(name="NormalBold", fontSize=10, fontName="HeiseiKakuGo-W5", leading=14))
    styles.add(ParagraphStyle(name="Small", fontSize=9, fontName="HeiseiKakuGo-W5", textColor=colors.grey))

    # --- Header (Cartify logo + INVOICE title) ---
    logo_path = "assets/logo.png"
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=1.0 * inch, height=1.0 * inch)
    else:
        logo = Paragraph("<b>Cartify</b>", styles["CartifyTitle"])

    header_data = [[logo, "", Paragraph("INVOICE", styles["RightTitle"])]]
    header = Table(header_data, colWidths=[80, 350, 100])
    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (2, 0), (2, 0), "RIGHT"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    elements.append(header)
    elements.append(Spacer(1, 12))

    # --- Invoice Info (above customer name) ---
    info_data = [
        ["Invoice No", invoice_data["invoice_no"]],
        ["Order ID", invoice_data["order_id"]],
        ["Invoice Date", invoice_data["invoice_date"]],
        ["Payment Method", invoice_data["payment_method"]],
    ]
    info_table = Table(info_data, colWidths=[100, 200])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "HeiseiKakuGo-W5"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 10))

    # --- Customer Info ---
    elements.append(Paragraph(f"<b>Customer:</b> {invoice_data['customer_name']}", styles["Normal"]))
    elements.append(Spacer(1, 15))

    # --- Product Table ---
    table_data = [["Sr", "Product", "SKU", "Qty", "Price", "Subtotal"]]
    for item in invoice_data["items"]:
        table_data.append([
            item["sr"],
            item["product"],
            item["sku"],
            item["qty"],
            f"{rupee} {item['price']:.2f}",
            f"{rupee} {item['subtotal']:.2f}",
        ])

    item_table = Table(table_data, colWidths=[25, 160, 90, 40, 70, 70])
    item_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("FONTNAME", (0, 0), (-1, -1), "HeiseiKakuGo-W5"),
        ("ALIGN", (3, 1), (-1, -1), "CENTER"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(item_table)
    elements.append(Spacer(1, 15))

    # --- Payment Info & Summary (side by side) ---
    p, s = invoice_data["payment_info"], invoice_data["summary"]

    left_col = [
        [Paragraph("<b>Payment Info</b>", styles["NormalBold"]), ""],
        ["Payment ID:", p["id"]],
        ["Payment Status:", p["status"]],
        ["Payment Date:", p["date"]],
        ["Transaction Reference:", p["reference"]],
    ]
    left_table = Table(left_col, colWidths=[130, 200])
    left_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "HeiseiKakuGo-W5"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    right_col = [
    [Paragraph("Subtotal", styles["Normal"]),
     Paragraph(f"{rupee} {s['subtotal']:.2f}", styles["Normal"])],
    [Paragraph("Discount", styles["Normal"]),
     Paragraph(f"{rupee} {s['discount']:.2f}", styles["Normal"])],
    [Paragraph("Tax (GST 19%)", styles["Normal"]),
     Paragraph(f"{rupee} {s['tax']:.2f}", styles["Normal"])],
    [Paragraph("Shipping", styles["Normal"]),
     Paragraph(f"{rupee} {s['shipping']:.2f}", styles["Normal"])],
    [Paragraph("<b>Total Payable</b>", styles["NormalBold"]),
     Paragraph(f"<b>{rupee} {s['total']:.2f}</b>", styles["NormalBold"])],
]

    right_table = Table(right_col, colWidths=[120, 100])
    right_table.setStyle(TableStyle([
    ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
    ("FONTSIZE", (0, 0), (-1, -1), 10),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ("FONTNAME", (0, -1), (-1, -1), "HeiseiKakuGo-W5"),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))


    payment_summary = Table([[left_table, right_table]], colWidths=[330, 170])
    payment_summary.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    elements.append(payment_summary)
    elements.append(Spacer(1, 15))

    # --- Notes ---
    elements.append(Paragraph("<b>Notes & Policies</b>", styles["NormalBold"]))
    elements.append(Paragraph(
        "Thank you for shopping with <b>Cartify</b>!<br/>"
        "For returns or exchanges, please visit our Returns Center within 7 days of delivery.<br/>"
        "Customer Support: support@cartify.com",
        styles["Small"],
    ))

    doc.build(elements)
