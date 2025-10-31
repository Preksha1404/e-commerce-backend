from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.models.users import User
from src.utils.auth import get_current_active_user
from src.utils.bulk_upload import process_upload_file, validate_row, save_products_batch, generate_bulk_upload_template
from src.schemas.products import BulkUploadResponse, BulkUploadRow
from typing import List

router = APIRouter(prefix="/products", tags=["Products"])

@router.get("/bulk-upload/template")
def download_bulk_upload_template():
    template = generate_bulk_upload_template()
    return Response(
        content=template,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=bulk_upload_template.csv"
        }
    )

@router.post("/bulk-upload", response_model=BulkUploadResponse)
async def bulk_upload_products(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Bulk upload products from CSV/Excel file
    """
    # Check if user is a seller
    if current_user.role != "seller":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only sellers can upload products"
        )
    
    try:
        # Process the file
        df = await process_upload_file(file, current_user.id)
        
        # Validate each row
        validated_products: List[BulkUploadRow] = []
        errors: List[BulkUploadRow] = []
        
        for index, row in df.iterrows():
            is_valid, product = validate_row(row, index + 2)  # +2 because Excel rows start at 1 and header is row 1
            if is_valid:
                validated_products.append(product)
            else:
                errors.append(product)
        
        # Save valid products to database
        if validated_products:
            success_records, batch_errors = save_products_batch(
                db, validated_products, current_user.id
            )
            # If there are row-level errors, return a single concise message
            if batch_errors:
                # pick first meaningful error_message
                first_msg = None
                for err in batch_errors:
                    # BulkUploadRow may be a pydantic model or dict-like
                    if hasattr(err, "error_message") and err.error_message:
                        first_msg = err.error_message
                        break
                    if isinstance(err, dict) and err.get("error_message"):
                        first_msg = err.get("error_message")
                        break

                if not first_msg:
                    # Fallback concise message
                    row_info = getattr(batch_errors[0], "row_number", None) or (batch_errors[0].get("row_number") if isinstance(batch_errors[0], dict) else None)
                    first_msg = f"Bulk upload failed: {len(batch_errors)} rows failed. First failure at row {row_info or 'unknown'}."

                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=first_msg)

            errors.extend(batch_errors)
        else:
            success_records = []
        
        # Prepare response
        response_payload = BulkUploadResponse(
            total_records=len(df),
            successful_records=len(success_records),
            failed_records=len(errors),
            errors=errors,
            success_records=success_records
        )
        if len(success_records) == 0:
            # All records failed: return client error
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=response_payload.model_dump()
            )
        return response_payload
        
    except Exception as e:
        # Return a concise error message (single line). Try to extract a useful reason
        msg = str(e)
        try:
            # If the exception string contains a dict-like representation with an 'errors' key,
            # attempt to extract the first error_message.
            import ast
            parsed = ast.literal_eval(msg) if msg.strip().startswith("{") else None
            if isinstance(parsed, dict) and parsed.get("errors"):
                first = parsed.get("errors")[0]
                if isinstance(first, dict) and first.get("error_message"):
                    msg = first.get("error_message")
        except Exception:
            # ignore parse errors and fall back to original message
            pass

        # Keep only the first line to avoid huge SQL dumps
        msg = (msg.splitlines()[0]) if msg else "Bulk upload failed"

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg
        )