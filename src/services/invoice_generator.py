from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import os
import requests
import cloudinary
from cloudinary.utils import cloudinary_url
from jwt.exceptions import ExpiredSignatureError

from src.models.orders import Order, OrderItem, Payment
from src.models.products import Product
from src.models.users import User
from src.core.database import get_db
from src.utils.auth import get_current_active_user, verify_token

router = APIRouter(prefix="/invoice", tags=["Invoice"])

# ----------------- Cloudinary Configuration -----------------
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

LOGO_PATH = "assets/logo.png"

# ----------------- Fetch Invoice Data -----------------
def get_invoice_data(order_id: int, db: Session):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return None

    user = db.query(User).filter(User.id == order.user_id).first()
    customer_name = (
        getattr(user, "name", None)
        or getattr(user, "full_name", None)
        or getattr(user, "username", None)
        or getattr(user, "email", "N/A")
    )

    items = (
        db.query(OrderItem, Product)
        .join(Product, Product.id == OrderItem.product_id, isouter=True)
        .filter(OrderItem.order_id == order_id)
        .all()
    )

    item_list = []
    for idx, (item, product) in enumerate(items, start=1):
        item_list.append({
            "sr": idx,
            "product": product.name if product else "N/A",
            "sku": product.sku if product else "N/A",
            "qty": item.quantity,
            "price": float(item.unit_price or 0),
            "subtotal": float(item.total_price or 0),
        })

    payment = db.query(Payment).filter(Payment.order_id == order_id).first()
    payment_info = {}
    if payment:
        payment_info = {
            "id": payment.id,
            "status": payment.status,
            "date": str(getattr(payment, "payment_date", "")),
            "reference": getattr(payment, "transaction_reference", ""),
        }

    subtotal = sum(i["subtotal"] for i in item_list)
    total = subtotal

    return {
        "invoice_no": f"INV-{order.id:05d}",
        "order_id": order.id,
        "invoice_date": str(order.created_at),
        "payment_method": order.payment_method or "N/A",
        "customer_name": customer_name,
        "user_id": order.user_id,
        "items": item_list,
        "payment_info": payment_info,
        "summary": {
            "subtotal": subtotal,
            "discount": 0.0,
            "tax": 0.0,
            "shipping": 0.0,
            "total": total,
        },
    }

# ----------------- Cloudinary ₹ Symbol Helper -----------------
def get_cloudinary_rupee_image(amount: float):
    """Generate Cloudinary URL with ₹ overlay"""
    formatted = f"₹{amount:,.2f}"
    url, _ = cloudinary_url(
        "transparent_placeholder.png",  # Must exist in your Cloudinary
        overlay={
            "font_family": "Roboto",
            "font_size": 24,
            "text": formatted
        },
        width=200,
        height=40,
        crop="fit",
        color="black"
    )
    return url

# ----------------- PDF Generator -----------------
def generate_pdf(invoice_data, file_obj):
    doc = SimpleDocTemplate(
        file_obj,
        pagesize=A4,
        rightMargin=40, leftMargin=40,
        topMargin=30, bottomMargin=40
    )
    elements = []
    styles = getSampleStyleSheet()
    styles["Normal"].fontName = "Helvetica"
    styles["Normal"].fontSize = 10
    styles.add(ParagraphStyle(name="CartifyTitle", fontSize=20, fontName="Helvetica", textColor=colors.HexColor("#333333")))
    styles.add(ParagraphStyle(name="RightTitle", fontSize=18, fontName="Helvetica", alignment=2))
    styles.add(ParagraphStyle(name="NormalBold", fontSize=10, fontName="Helvetica-Bold", leading=14))
    styles.add(ParagraphStyle(name="Small", fontSize=9, fontName="Helvetica", textColor=colors.grey))

    # ----------------- Currency Cell -----------------
    def currency_cell(amount):
        try:
            amount_value = float(amount)
        except (ValueError, TypeError):
            amount_value = 0.0

        cloudinary_img_url = get_cloudinary_rupee_image(amount_value)
        try:
            resp = requests.get(cloudinary_img_url, timeout=5)
            resp.raise_for_status()
            img_buffer = BytesIO(resp.content)
            return RLImage(img_buffer, width=50, height=15)
        except Exception:
            return Paragraph(f"₹{amount_value:,.2f}", styles["Normal"])

    # ----------------- Header -----------------
    logo = RLImage(LOGO_PATH, width=1.0 * inch, height=1.0 * inch) if os.path.exists(LOGO_PATH) else Paragraph("<b>Cartify</b>", styles["CartifyTitle"])
    header = Table([[logo, "", Paragraph("INVOICE", styles["RightTitle"])]], colWidths=[80, 350, 100])
    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (2, 0), (2, 0), "RIGHT"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10)
    ]))
    elements.append(header)
    elements.append(Spacer(1, 12))

    # ----------------- Invoice Info -----------------
    info_table = Table([
        ["Invoice No", invoice_data["invoice_no"]],
        ["Order ID", invoice_data["order_id"]],
        ["Invoice Date", invoice_data["invoice_date"]],
        ["Payment Method", invoice_data["payment_method"]]
    ], colWidths=[120, 200])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3)
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(f"<b>Customer:</b> {invoice_data['customer_name']}", styles["Normal"]))
    elements.append(Spacer(1, 15))

    # ----------------- Items Table -----------------
    table_data = [["Sr", "Product", "SKU", "Qty", "Price", "Subtotal"]]
    for item in invoice_data["items"]:
        table_data.append([
            item["sr"],
            Paragraph(item["product"], styles["Normal"]),
            item["sku"],
            item["qty"],
            currency_cell(item["price"]),
            currency_cell(item["subtotal"])
        ])

    PAGE_WIDTH, PAGE_HEIGHT = A4
    usable_width = PAGE_WIDTH - 80
    col_widths = [0.06 * usable_width, 0.35 * usable_width, 0.19 * usable_width, 0.08 * usable_width, 0.16 * usable_width, 0.16 * usable_width]
    item_table = Table(table_data, colWidths=col_widths)
    item_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("ALIGN", (3, 1), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8)
    ]))
    elements.append(item_table)
    elements.append(Spacer(1, 15))

    # ----------------- Payment & Summary -----------------
    p = invoice_data["payment_info"]
    s = invoice_data["summary"]

    left_table = Table([
        [Paragraph("<b>Payment Info</b>", styles["NormalBold"]), ""],
        ["Payment ID:", p.get("id", "")],
        ["Status:", p.get("status", "")],
        ["Date:", p.get("date", "")],
        ["Reference:", p.get("reference", "")]
    ], colWidths=[130, 200])

    right_table = Table([
        ["Subtotal", currency_cell(s.get("subtotal", 0.0))],
        ["Discount", currency_cell(s.get("discount", 0.0))],
        ["Tax", currency_cell(s.get("tax", 0.0))],
        ["Shipping", currency_cell(s.get("shipping", 0.0))],
        [Paragraph("<b>Total Payable</b>", styles["NormalBold"]), currency_cell(s.get("total", 0.0))]
    ], colWidths=[120, 100])

    payment_summary = Table([[left_table, right_table]], colWidths=[330, 170])
    payment_summary.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    elements.append(payment_summary)
    elements.append(Spacer(1, 15))

    # ----------------- Notes -----------------
    elements.append(Paragraph("<b>Notes & Policies</b>", styles["NormalBold"]))
    elements.append(Paragraph(
        "Thank you for shopping with <b>Cartify</b>!<br/>"
        "For returns or exchanges, please visit our Returns Center within 7 days of delivery.<br/>"
        "Customer Support: support@cartify.com",
        styles["Small"]
    ))

    doc.build(elements)

# ----------------- FastAPI Endpoint -----------------
@router.get("/{order_id}", response_class=StreamingResponse)
def generate_invoice(request: Request, order_id: int, db: Session = Depends(get_db)):
    """
    Generate invoice PDF. Handles expired JWT gracefully.
    """
    # ----------------- Get token from Authorization header -----------------
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization token missing")
    token = token.split(" ")[1]

    # ----------------- Verify token -----------------
    try:
        current_user = verify_token(token)
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    invoice_data = get_invoice_data(order_id, db)
    if not invoice_data:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if current_user.role != "admin" and invoice_data["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Access forbidden")

    pdf_buffer = BytesIO()
    generate_pdf(invoice_data, pdf_buffer)
    pdf_buffer.seek(0)

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=invoice_{order_id}.pdf"}
    )
