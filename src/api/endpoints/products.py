import os
import uuid
from decimal import Decimal
from typing import List, Optional
from fastapi import (
    APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status,Path
)
from sqlalchemy.orm import Session
from sqlalchemy import or_
from src.schemas.users import UserResponse,UserRole
from src.core.database import SessionLocal 
from src.models.products import Product, Category
from src.models.users import User
from src.utils.auth import get_current_active_user,require_admin,require_roles
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

@router.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    categories = db.query(Category).filter(Category.is_active == True).all()
    return {"count": len(categories), "data": categories} 
@router.patch(
    "/{customer_id}/block-toggle",
    response_model=UserResponse,
    dependencies=[Depends(require_roles(UserRole.ADMIN))]
)
def toggle_customer_block(
    customer_id: int = Path(..., ge=1),
    db: Session = Depends(get_db)
):
    # 🔍 Find the customer by ID and role
    customer = db.query(User).filter(
        User.id == customer_id,
        User.role == UserRole.CUSTOMER
    ).first()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    # 🔁 Toggle block/unblock
    customer.is_blocked = not customer.is_blocked
    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer
