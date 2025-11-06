from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import os

# --- FastAPI dependencies ---
from src.core.database import get_db
from src.models.users import User
from src.utils.auth import get_current_active_user

router = APIRouter(prefix="/invoice", tags=["Invoice"])

RUPEE_PATH = r"C:\e-commerce-backend\uploads\pngegg.png"

# -------------------------------
# Mock function to get invoice data
# -------------------------------
def get_invoice_data(order_id: int, db: Session):
    """Fetch order and related data for invoice generation (mock, unique per order_id)."""
    # Dynamic items using order_id
    items = [
        {
            "sr": 1,
            "product": f"Wireless Mouse {order_id}",
            "sku": f"MSE-{order_id:03d}",
            "qty": 1,
            "price": 500.00 + order_id * 10,
            "subtotal": 500.00 + order_id * 10,
        },
        {
            "sr": 2,
            "product": f"Keyboard {order_id}",
            "sku": f"KEY-{order_id:03d}",
            "qty": 1,
            "price": 900.00 + order_id * 15,
            "subtotal": 900.00 + order_id * 15,
        },
    ]

    subtotal = sum(i["subtotal"] for i in items)
    discount = 100.00 if order_id % 2 == 0 else 50.00  # vary discount
    tax = 0.0
    shipping = 50.0
    total = subtotal - discount + tax + shipping

    # Mock user assignment
    user_id = 65 + (order_id % 5)  # simulate different users

    return {
        "invoice_no": f"INV-{order_id:05d}",
        "order_id": order_id,
        "invoice_date": "2025-11-04",
        "payment_method": "Credit Card",
        "customer_name": f"Customer {order_id}",
        "user_id": user_id,
        "items": items,
        "payment_info": {
            "id": f"PMT-{order_id:06d}",
            "status": "Paid",
            "date": "2025-11-04",
            "reference": f"TXN{order_id:09d}",
        },
        "summary": {
            "subtotal": subtotal,
            "discount": discount,
            "tax": tax,
            "shipping": shipping,
            "total": total,
        },
    }

# -------------------------------
# PDF generator
# -------------------------------
def generate_pdf(invoice_data, file_obj):
    """Generate invoice PDF with ₹ image before amounts (dict or object-safe)."""
    from types import SimpleNamespace
    from reportlab.platypus import Table as InnerTable, TableStyle, Paragraph, Spacer, Image

    if isinstance(invoice_data, dict):
        invoice = SimpleNamespace(**invoice_data)
    else:
        invoice = invoice_data

    doc = SimpleDocTemplate(
        file_obj,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=30,
        bottomMargin=40,
    )

    elements = []
    styles = getSampleStyleSheet()
    styles["Normal"].fontName = "Helvetica"
    styles["Normal"].fontSize = 10
    styles.add(ParagraphStyle(name="CartifyTitle", fontSize=20, fontName="Helvetica", textColor=colors.HexColor("#333333")))
    styles.add(ParagraphStyle(name="RightTitle", fontSize=18, fontName="Helvetica", alignment=2))
    styles.add(ParagraphStyle(name="NormalBold", fontSize=10, fontName="Helvetica-Bold", leading=14))
    styles.add(ParagraphStyle(name="Small", fontSize=9, fontName="Helvetica", textColor=colors.grey))

    def currency_cell(amount):
        rupee_img = Image(RUPEE_PATH, width=6, height=6)
        amt_para = Paragraph(f"{amount:,.2f}", styles["Normal"])
        cell = InnerTable([[rupee_img, amt_para]], colWidths=[8, 45])
        cell.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 1),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        return cell

    # Header
    logo_path = "assets/logo.png"
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=1.0 * inch, height=1.0 * inch)
    else:
        logo = Paragraph("<b>Cartify</b>", styles["CartifyTitle"])
    header_data = [[logo, "", Paragraph("INVOICE", styles["RightTitle"])]]
    header = Table(header_data, colWidths=[80, 350, 100])
    header.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                                ("ALIGN", (2, 0), (2, 0), "RIGHT"),
                                ("BOTTOMPADDING", (0, 0), (-1, -1), 10)]))
    elements.append(header)
    elements.append(Spacer(1, 12))

    # Invoice info
    info_data = [
        ["Invoice No", getattr(invoice, "invoice_no", "")],
        ["Order ID", getattr(invoice, "order_id", "")],
        ["Invoice Date", getattr(invoice, "invoice_date", "")],
        ["Payment Method", getattr(invoice, "payment_method", "")],
    ]
    info_table = Table(info_data, colWidths=[100, 200])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("RIGHTPADDING", (1, 0), (1, -1), 70),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 6))

    # Customer info
    elements.append(Paragraph(f"<b>Customer:</b> {getattr(invoice, 'customer_name', '')}", styles["Normal"]))
    elements.append(Spacer(1, 15))

    # Product table
    table_data = [["Sr", "Product", "SKU", "Qty", "Price", "Subtotal"]]
    for item in getattr(invoice, "items", []):
        table_data.append([
            item.get("sr", ""),
            item.get("product", ""),
            item.get("sku", ""),
            item.get("qty", ""),
            currency_cell(item.get("price", 0.0)),
            currency_cell(item.get("subtotal", 0.0)),
        ])
    item_table = Table(table_data, colWidths=[25, 160, 90, 40, 70, 70])
    item_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("ALIGN", (3, 1), (-1, -1), "CENTER"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(item_table)
    elements.append(Spacer(1, 15))

    # Payment info & summary
    p = getattr(invoice, "payment_info", {})
    s = getattr(invoice, "summary", {})

    left_col = [
        [Paragraph("<b>Payment Info</b>", styles["NormalBold"]), ""],
        ["Payment ID:", p.get("id", "")],
        ["Payment Status:", p.get("status", "")],
        ["Payment Date:", p.get("date", "")],
        ["Transaction Reference:", p.get("reference", "")],
    ]
    left_table = Table(left_col, colWidths=[130, 200])
    left_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))

    right_col = [
        ["Subtotal", currency_cell(s.get("subtotal", 0.0))],
        ["Discount", currency_cell(s.get("discount", 0.0))],
        ["Tax (GST 0%)", currency_cell(s.get("tax", 0.0))],
        ["Shipping", currency_cell(s.get("shipping", 0.0))],
        [Paragraph("<b>Total Payable</b>", styles["NormalBold"]), currency_cell(s.get("total", 0.0))],
    ]
    right_table = Table(right_col, colWidths=[120, 100])
    right_table.setStyle(TableStyle([
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("RIGHTPADDING", (1, 0), (1, -1), 50),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))

    payment_summary = Table([[left_table, right_table]], colWidths=[330, 170])
    payment_summary.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    elements.append(payment_summary)
    elements.append(Spacer(1, 15))

    # Notes
    elements.append(Paragraph("<b>Notes & Policies</b>", styles["NormalBold"]))
    elements.append(Paragraph(
        "Thank you for shopping with <b>Cartify</b>!<br/>"
        "For returns or exchanges, please visit our Returns Center within 7 days of delivery.<br/>"
        "Customer Support: support@cartify.com",
        styles["Small"],
    ))

    doc.build(elements)

# -------------------------------
# FastAPI endpoint
# -------------------------------
@router.get("/{order_id}", response_class=StreamingResponse)
def generate_invoice(
    order_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    invoice_data = get_invoice_data(order_id, db)
    if not invoice_data:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Access control: normal users only see their invoices
    if invoice_data.get("user_id") != current_user.id and not getattr(current_user, "is_admin", False):
        raise HTTPException(status_code=403, detail="Access forbidden")

    pdf_buffer = BytesIO()
    generate_pdf(invoice_data, pdf_buffer)
    pdf_buffer.seek(0)

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=invoice_{order_id}.pdf"}
    )
