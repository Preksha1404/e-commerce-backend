from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: Decimal = Field(ge=0)
    discount_price: Optional[Decimal] = Field(default=None, ge=0)
    stock: int = Field(ge=0)
    sku: str
    category_id: int
    is_active: bool = True
    is_featured: bool = False
    images: Optional[List[str]] = Field(default_factory=list)

    class Config:
        orm_mode = True


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime


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
