import os
import uuid
from decimal import Decimal
from typing import List, Optional
from fastapi import (
    APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
)
from sqlalchemy.orm import Session
from sqlalchemy import or_

from src.core.database import SessionLocal
from src.models.products import Product, Category
from src.models.users import User
from src.utils.auth import get_current_active_user
from src.utils.bulk_upload import process_upload_file, validate_row, save_products_batch
from src.schemas.products import BulkUploadResponse

router = APIRouter(prefix="/api", tags=["Customer & Seller Products"])

# ---------------------------------------------------------------------
# DB Dependency
# ---------------------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------
# ✅ CREATE PRODUCT (multipart/form-data)
# ---------------------------------------------------------------------
@router.post("/products/create")
async def create_product(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    price: Decimal = Form(...),
    discount_price: Optional[Decimal] = Form(None),
    stock: int = Form(...),
    sku: str = Form(...),
    category_id: int = Form(...),
    is_active: bool = Form(True),
    is_featured: bool = Form(False),
    images: Optional[List[UploadFile]] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role != "seller":
        raise HTTPException(status_code=403, detail="Only sellers can create products")

    upload_dir = "static/uploads"
    os.makedirs(upload_dir, exist_ok=True)

    image_urls = []
    if images:
        for image in images:
            ext = image.filename.split(".")[-1]
            filename = f"{uuid.uuid4()}.{ext}"
            file_path = os.path.join(upload_dir, filename)

            with open(file_path, "wb") as buffer:
                buffer.write(await image.read())

            image_urls.append(f"/{file_path}")

    new_product = Product(
        name=name,
        description=description,
        price=price,
        discount_price=discount_price,
        stock=stock,
        sku=sku,
        category_id=category_id,
        is_active=is_active,
        is_featured=is_featured,
        seller_id=current_user.id,
        images=image_urls
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return {"message": "Product created successfully", "data": new_product}


# ---------------------------------------------------------------------
# Other CRUD and routes remain the same below
# ---------------------------------------------------------------------

@router.get("/products/search")
def search_products_route(
    keyword: str = Query(..., min_length=1, description="Search keyword"),
    db: Session = Depends(get_db)
):
    products = db.query(Product).filter(
        Product.is_active == True,
        or_(
            Product.name.ilike(f"%{keyword}%"),
            Product.description.ilike(f"%{keyword}%")
        )
    ).all()
    return {"count": len(products), "data": products}


@router.get("/products/{productId}")
def get_product(productId: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == productId).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    categories = db.query(Category).filter(Category.is_active == True).all()
    return {"count": len(categories), "data": categories}


@router.post("/products/bulk-upload", response_model=BulkUploadResponse)
async def bulk_upload_products(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role != "seller":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only sellers can upload products"
        )

    try:
        df = await process_upload_file(file, current_user.id)
        validated_products, errors = [], []

        for index, row in df.iterrows():
            is_valid, product = validate_row(row, index + 2)
            (validated_products if is_valid else errors).append(product)

        success_records = []
        if validated_products:
            success_records, batch_errors = save_products_batch(db, validated_products, current_user.id)
            errors.extend(batch_errors)

        return BulkUploadResponse(
            total_records=len(df),
            successful_records=len(success_records),
            failed_records=len(errors),
            errors=errors,
            success_records=success_records
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bulk upload failed: {str(e)}"
        )
