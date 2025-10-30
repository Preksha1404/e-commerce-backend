from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

class ProductCreate(BaseModel):
    name: str
    description: str
    price: Decimal = Field(ge=0)
    stock: int = Field(ge=0)
    category: str
    images: List[str] = Field(default_factory=list)  # List of image URLs
    # Optional fields
    sku: Optional[str] = None
    category_id: Optional[int] = None
    discount_price: Optional[Decimal] = Field(default=None, ge=0)
    is_active: Optional[bool] = True
    is_featured: Optional[bool] = False

class BulkUploadRow(ProductCreate):
    row_number: int
    error_message: Optional[str] = None
    status: str = "pending"  # pending, success, error

class BulkUploadResponse(BaseModel):
    total_records: int
    successful_records: int
    failed_records: int
    errors: List[BulkUploadRow]
    success_records: List[BulkUploadRow]
    
    class Config:
        from_attributes = True