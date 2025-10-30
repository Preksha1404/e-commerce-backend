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