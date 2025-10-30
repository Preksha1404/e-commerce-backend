import pandas as pd
from typing import List, Tuple, Dict, Any
from src.schemas.products import ProductCreate, BulkUploadRow
from fastapi import UploadFile
import logging
from sqlalchemy.orm import Session
from src.models.products import Product, Category, ProductImage
from src.utils.functions import generate_slug
import io

logger = logging.getLogger(__name__)

def generate_bulk_upload_template() -> str:
    """Generate a sample CSV template for bulk product upload."""
    header = (
        "name,description,price,discount_price,stock,sku,category_id,is_active,is_featured,images\n"
    )
    sample_row = (
        "Wireless Mouse,Ergonomic 2.4G mouse,19.99,14.99,120,WM-1001,3,true,false,https://img.example.com/mouse1.jpg|https://img.example.com/mouse2.jpg\n"
    )
    return header + sample_row

async def process_upload_file(file: UploadFile, seller_id: int) -> pd.DataFrame:
    """Read and validate the uploaded file"""
    if file.filename.endswith('.csv'):
        content = await file.read()
        return pd.read_csv(io.StringIO(content.decode('utf-8')))
    elif file.filename.endswith(('.xls', '.xlsx')):
        content = await file.read()
        return pd.read_excel(io.BytesIO(content))
    else:
        raise ValueError("Unsupported file format. Please upload CSV or Excel file.")

def validate_row(row: Dict[str, Any], row_number: int) -> Tuple[bool, BulkUploadRow]:
    """Validate a single row of product data"""
    try:
        # Convert row to ProductCreate schema
        product_data = {
            "name": str(row.get("name", "")),
            "description": str(row.get("description", "")),
            "price": float(row.get("price", 0)),
            "discount_price": float(row.get("discount_price", 0)) if pd.notna(row.get("discount_price")) else None,
            "stock": int(row.get("stock", 0)),
            "sku": str(row.get("sku", "")),
            "category_id": int(row.get("category_id", 0)),
            "is_active": bool(row.get("is_active", True)),
            "is_featured": bool(row.get("is_featured", False)),
            "images": str(row.get("images", "")).split("|") if pd.notna(row.get("images")) else []
        }
        
        # Validate using Pydantic model
        product = ProductCreate(**product_data)
        
        return True, BulkUploadRow(
            **product.model_dump(),
            row_number=row_number,
            status="success"
        )
    except Exception as e:
        logger.error(f"Error validating row {row_number}: {str(e)}")
        return False, BulkUploadRow(
            **row,
            row_number=row_number,
            status="error",
            error_message=str(e)
        )

def save_products_batch(
    db: Session,
    products: List[BulkUploadRow],
    seller_id: int,
    batch_size: int = 100
) -> Tuple[List[BulkUploadRow], List[BulkUploadRow]]:
    """Save validated products to database in batches"""
    success_records = []
    error_records = []
    
    # Process in batches
    for i in range(0, len(products), batch_size):
        batch = products[i:i + batch_size]
        try:
            # Create Product instances while validating category and SKU
            db_products = []
            inserted_rows = []
            for p in batch:
                # Validate category exists
                category = db.query(Category).filter(Category.id == p.category_id).first()
                if not category:
                    p.status = "error"
                    p.error_message = f"Category id {p.category_id} does not exist"
                    error_records.append(p)
                    continue

                # Check if SKU already exists
                existing_product = db.query(Product).filter(Product.sku == p.sku).first()
                if existing_product:
                    p.status = "error"
                    p.error_message = f"SKU {p.sku} already exists"
                    error_records.append(p)
                    continue

                product_dict = p.model_dump().copy()
                # remove metadata fields if present
                product_dict.pop('row_number', None)
                product_dict.pop('error_message', None)
                product_dict.pop('status', None)

                # Extract images from product_dict
                images = product_dict.pop('images', [])
                
                db_prod = Product(
                    **product_dict,
                    seller_id=seller_id,
                    slug=generate_slug(p.name)
                )
                
                # Create product images
                for position, image_url in enumerate(images):
                    if image_url.strip():  # Only create if URL is not empty
                        db_prod.images.append(ProductImage(
                            url=image_url.strip(),
                            position=position
                        ))
                db_products.append(db_prod)
                inserted_rows.append(p)

            # Insert using ORM so related images are persisted via cascade
            if db_products:
                db.add_all(db_products)
                db.commit()
                success_records.extend(inserted_rows)
        except Exception as e:
            logger.error(f"Error saving batch: {str(e)}")
            # Mark all products in failed batch as error
            for product in batch:
                product.status = "error"
                product.error_message = str(e)
            error_records.extend(batch)
            db.rollback()
    
    return success_records, error_records