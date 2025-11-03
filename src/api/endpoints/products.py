from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Form
from fastapi.responses import Response
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.models.users import User
from src.models.products import Product, ProductImage
from src.utils.auth import get_current_active_user
from src.utils.bulk_upload import process_upload_file, validate_row, save_products_batch, generate_bulk_upload_template
from src.schemas.products import BulkUploadResponse, BulkUploadRow
from typing import List
from src.schemas.products import BulkUploadResponse, BulkUploadRow, ProductResponse
from typing import List, Optional
from src.utils.functions import generate_slug
import cloudinary
import cloudinary.uploader
import os

router = APIRouter(prefix="/products", tags=["Products"])

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

# Product CRUD Operation
@router.get("/", response_model=List[ProductResponse])
def list_products(
    db: Session = Depends(get_db)
):
    products = db.query(Product).all()
    return products

@router.get("/sellers/{seller_id}/", response_model=List[ProductResponse])
def get_seller_products(
    seller_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all products belonging to a specific seller.
    - Sellers can view their own products.
    - Admins can view any seller's products.
    """
    # Authorization
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    if current_user.role == "seller" and current_user.id != seller_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own products"
        )

    # Fetch all products of that seller
    products = (
        db.query(Product)
        .filter(Product.seller_id == seller_id)
        .order_by(Product.created_at.desc())
        .all()
    )

    if not products:
        raise HTTPException(status_code=404, detail="No products found for this seller")

    return products

@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    price: float = Form(...),
    discount_price: Optional[str] = Form(None),
    stock: int = Form(...),
    sku: Optional[str] = Form(None),
    category_id: int = Form(...),
    is_featured: bool = Form(False),
    images: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Seller creates a new product — uploads images to Cloudinary, 
    saves product details, and marks status as 'pending' for admin approval.
    """
    # Authorization check
    if current_user.role != "seller":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only sellers can create products"
        )
    
    # Handle optional discount price and SKU
    discount_value = float(discount_price) if discount_price not in (None, "", "null") else None
    sku_value = sku.strip() if sku and sku.strip() else None

    # Product initially inactive until approved by admin
    db_product = Product(
        name=name,
        description=description,
        price=price,
        discount_price=discount_value,
        stock=stock,
        sku=sku_value,
        category_id=category_id,
        slug=generate_slug(name),
        seller_id=current_user.id,
        is_active=False,       # inactive until admin approves
        is_featured=is_featured,
        status="pending"       # default status
    )

    db.add(db_product)
    db.commit()
    db.refresh(db_product)

    # Upload product images
    for index, image in enumerate(images, start=1):
        if not image.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail=f"Invalid file type: {image.filename}")

        try:
            upload_result = cloudinary.uploader.upload(
                image.file,
                folder=f"seller_{current_user.id}/products/{db_product.id}",
                overwrite=True
            )
            image_url = upload_result.get("secure_url")

            db_image = ProductImage(
                product_id=db_product.id,
                url=image_url,
                position=index
            )
            db.add(db_image)

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")

    db.commit()
    db.refresh(db_product)

    return db_product

@router.get("/{product_id}/", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product

@router.patch("/{product_id}/update", response_model=ProductResponse)
async def update_product(
    product_id: int,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    discount_price: Optional[float] = Form(None),
    stock: Optional[int] = Form(None),
    sku: Optional[str] = Form(None),
    category_id: Optional[int] = Form(None),
    is_featured: Optional[bool] = Form(None),
    images: Optional[List[UploadFile]] = File(None),  # optional
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Seller updates product details and optionally uploads new images.
    Resets product status to 'pending' and is_active to False after edit.
    """

    # Authorization
    if current_user.role != "seller":
        raise HTTPException(status_code=403, detail="Only sellers can update products")

    # Fetch product
    db_product = db.query(Product).filter(
        Product.id == product_id,
        Product.seller_id == current_user.id
    ).first()

    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Update non-image fields if provided
    form_fields = {
        "name": name,
        "description": description,
        "price": price,
        "discount_price": discount_price,
        "stock": stock,
        "sku": sku,
        "category_id": category_id,
        "is_featured": is_featured
    }

    for key, value in form_fields.items():
        if value is not None:
            setattr(db_product, key, value)

    # Handle image updates only if new images are uploaded
    if images:
        # Delete old images
        db.query(ProductImage).filter(ProductImage.product_id == product_id).delete()

        for index, image in enumerate(images, start=1):
            if not image.content_type.startswith("image/"):
                raise HTTPException(status_code=400, detail=f"Invalid file type: {image.filename}")

            try:
                upload_result = cloudinary.uploader.upload(
                    image.file,
                    folder=f"seller_{current_user.id}/products/{db_product.id}",
                    overwrite=True
                )
                image_url = upload_result.get("secure_url")

                db.add(ProductImage(
                    product_id=db_product.id,
                    url=image_url,
                    position=index
                ))

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")

    # Reset status for admin review
    db_product.status = "pending"
    db_product.is_active = False

    db.commit()
    db.refresh(db_product)

    return db_product

# Delete product
@router.delete("/{product_id}/delete", status_code=status.HTTP_200_OK)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    db_product = db.query(Product).filter(Product.id == product_id).first()

    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )

    # Authorization
    if db_product.seller_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this product"
        )

    # Delete images
    db.query(ProductImage).filter(ProductImage.product_id == product_id).delete()

    # Delete product
    db.delete(db_product)
    db.commit()

    return {"message": f"Product '{db_product.name}' deleted successfully"}

@router.patch("/{product_id}/status", response_model=ProductResponse)
def update_product_status(
    product_id: int,
    status: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Admin updates product status (approve/reject)
    """
    # Authorization
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update product status"
        )

    db_product = db.query(Product).filter(Product.id == product_id).first()

    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )

    if status not in ["approved", "rejected"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status must be either 'approved' or 'rejected'"
        )

    db_product.status = status
    db_product.is_active = True if status == "approved" else False

    db.commit()
    db.refresh(db_product)

    return db_product

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