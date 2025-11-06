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


# -------------------------------
# Mock function to get invoice data
# -------------------------------
def get_invoice_data(order_id: int, db: Session):
    """Fetch order and related data for invoice generation."""
    
    order = {
        "has_coupon": True,         # Assume coupon applied
        "coupon_discount": 100.00,  # Discount amount from DB or logic
    }

    # Compute subtotal
    items = [
        {"sr": 1, "product": "Wireless Mouse", "sku": "MSE-001", "qty": 1, "price": 599.00, "subtotal": 599.00},
        {"sr": 2, "product": "Keyboard", "sku": "KEY-002", "qty": 1, "price": 899.00, "subtotal": 899.00},
    ]
    subtotal = sum(i["subtotal"] for i in items)

    # Apply discount if coupon exists
    discount = order["coupon_discount"] if order["has_coupon"] else 0.00
    tax = 0.00
    shipping = 50.00
    total = subtotal - discount + tax + shipping

    return {
        "invoice_no": f"INV-{order_id:05d}",
        "order_id": order_id,
        "invoice_date": "2025-11-04",
        "payment_method": "Credit Card",
        "customer_name": "John Doe",
        "items": items,
        "payment_info": {
            "id": "PMT-123456",
            "status": "Paid",
            "date": "2025-11-04",
            "reference": "TXN123456789",
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
# Mock function to get invoice data
# -------------------------------
 
RUPEE_PATH = r"C:\e-commerce-backend\uploads\pngegg.png"
 

def generate_pdf(invoice_data: dict, file_obj):
    """Generate invoice PDF with ₹ image before the amount (properly aligned)."""
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

    # ✅ Helper to align ₹ before amount
    from reportlab.platypus import Table as InnerTable

    def currency_cell(amount):
        """Display ₹ image before the amount (side by side, aligned)."""
        rupee_img = Image(RUPEE_PATH, width=6, height=6)  # smaller and balanced
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

    # --- Header ---
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

    # --- Invoice Info ---
    info_data = [
        ["Invoice No", invoice_data["invoice_no"]],
        ["Order ID", invoice_data["order_id"]],
        ["Invoice Date", invoice_data["invoice_date"]],
        ["Payment Method", invoice_data["payment_method"]],
    ]
    info_table = Table(info_data, colWidths=[100, 200])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("RIGHTPADDING", (1, 0), (1, -1),70),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 6))
    
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
            currency_cell(item["price"]),
            currency_cell(item["subtotal"]),
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

    # --- Payment Info & Summary ---
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
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))

    right_col = [
        ["Subtotal", currency_cell(s["subtotal"])],
        ["Discount", currency_cell(s["discount"])],
        ["Tax (GST 0%)", currency_cell(s["tax"])],
        ["Shipping", currency_cell(s["shipping"])],
        [Paragraph("<b>Total Payable</b>", styles["NormalBold"]), currency_cell(s["total"])],
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

    # --- Notes ---
    elements.append(Paragraph("<b>Notes & Policies</b>", styles["NormalBold"]))
    elements.append(Paragraph(
        "Thank you for shopping with <b>Cartify</b>!<br/>"
        "For returns or exchanges, please visit our Returns Center within 7 days of delivery.<br/>"
        "Customer Support: support@cartify.com",
        styles["Small"],
    ))

    doc.build(elements)