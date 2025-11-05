from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from io import BytesIO
from src.core.database import get_db
from src.models.users import User
from src.services.invoice_generator import get_invoice_data, generate_pdf
from src.utils.auth import get_current_active_user

router = APIRouter(prefix="/invoice", tags=["Invoice"])

@router.get("/{order_id}", response_class=StreamingResponse)
def generate_invoice(
    order_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session= Depends(get_db)
):
    print("Reached here, user id:", current_user.id)
    invoice_data = get_invoice_data(order_id,db)
    if not invoice_data:
        raise HTTPException(status_code=404, detail="Invoice not found")

    pdf_buffer = BytesIO()
    generate_pdf(invoice_data, pdf_buffer)
    pdf_buffer.seek(0)

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=invoice_{order_id}.pdf"}
    )
