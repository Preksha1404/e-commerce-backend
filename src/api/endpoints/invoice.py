from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.services.invoice_generator import get_invoice_data, generate_pdf
import os

router = APIRouter(prefix="/invoice", tags=["Invoice"])


@router.get("/{order_id}", response_class=FileResponse)
def generate_invoice(order_id: int, db: Session = Depends(get_db)):
    """Generate and return a PDF invoice for the given order ID."""

    # Fetch order data from service
    order_data = get_invoice_data(order_id, db)
    if not order_data:
        raise HTTPException(status_code=404, detail="Order not found")

    # Ensure the invoices directory exists
    invoices_dir = "invoices"
    os.makedirs(invoices_dir, exist_ok=True)

    # File path for generated invoice
    file_path = os.path.join(invoices_dir, f"invoice_{order_id}.pdf")

    # Generate PDF using the service
    generate_pdf(order_data, file_path)

    # Check if PDF was successfully created
    if not os.path.exists(file_path):
        raise HTTPException(status_code=500, detail="Failed to generate invoice")

    # Return the PDF file as a downloadable response
    return FileResponse(
        path=file_path,
        filename=f"invoice_{order_id}.pdf",
        media_type="application/pdf"
    )
