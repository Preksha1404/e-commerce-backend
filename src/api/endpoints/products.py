from fastapi import APIRouter, Depends, UploadFile, File, status, Form, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from src.core.database import get_db
from src.models.users import User
from src.schemas.products import BulkUploadResponse, ProductResponse, AddStockRequest
from src.utils.auth import get_current_active_user
from src.services.product_service import ProductService
import cloudinary
import os

router = APIRouter(prefix="/products", tags=["Products"])

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)


@router.get("/", response_model=List[ProductResponse])
def list_products(db: Session = Depends(get_db)):
    return ProductService(db, None).list_products()


@router.get("/sellers/{seller_id}/", response_model=List[ProductResponse])
def get_seller_products(seller_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return ProductService(db, current_user).get_seller_products(seller_id)


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
    return await ProductService(db, current_user).create_product(name, description, price, discount_price, stock, sku, category_id, is_featured, images)


@router.get("/{product_id}/", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    return ProductService(db, None).get_product(product_id)


@router.patch("/{product_id}/update", response_model=ProductResponse)
async def update_product(
    product_id: int,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    discount_price: Optional[str] = Form(None),
    stock: Optional[int] = Form(None),
    sku: Optional[str] = Form(None),
    category_id: Optional[int] = Form(None),
    is_featured: Optional[bool] = Form(None),
    images: Optional[List[UploadFile]] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return await ProductService(db, current_user).update_product(product_id, name, description, price, discount_price, stock, sku, category_id, is_featured, images)


@router.delete("/{product_id}/delete", status_code=status.HTTP_200_OK)
def delete_product(product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return ProductService(db, current_user).delete_product(product_id)


@router.patch("/{product_id}/stock", response_model=ProductResponse)
async def add_product_stock(product_id: int, stock_data: AddStockRequest = Body(...), current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return ProductService(db, current_user).add_product_stock(product_id, stock_data)


@router.patch("/{product_id}/status", response_model=ProductResponse)
def update_product_status(product_id: int, status: str = Form(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return ProductService(db, current_user).update_product_status(product_id, status)


@router.get("/bulk-upload/template")
def download_bulk_upload_template():
    return ProductService(None, None).download_bulk_upload_template()


@router.post("/bulk-upload", response_model=BulkUploadResponse)
async def bulk_upload_products(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return await ProductService(db, current_user).bulk_upload_products(file)