from pydantic import BaseModel, Field, validator
from typing import Optional, List,Union
from datetime import datetime
from decimal import Decimal

class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: Decimal = Field(ge=0)
    stock: int = Field(ge=0)
    sku: str
    category_id: int
    is_active: bool = True
    is_featured: bool = False
    images: Optional[Union[List[str], List[bytes]]] = Field(default_factory=list)  # List of image URLs

class BulkUploadRow(BaseModel):
    name: str
    description: str
    price: float
    stock: int
    category: str
    images: Optional[List[str]] = Field(default_factory=list)
    row_number: int
    status: str = "pending"  # pending, success, error
    error_message: Optional[str] = None
    category_id: Optional[int] = None

class BulkUploadResponse(BaseModel):
    total_records: int
    successful_records: int
    failed_records: int
    errors: List[BulkUploadRow]
    success_records: List[BulkUploadRow]
    
    class Config:
        from_attributes = True