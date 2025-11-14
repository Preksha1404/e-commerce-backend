from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

# --- Review Schemas ---
class ReviewBase(BaseModel):
    rating: float = Field(..., ge=0, le=5)
    comment: str

    model_config = {"from_attributes": True}

class ReviewResponse(ReviewBase):
    name: str

    model_config = {"from_attributes": True}

class ReviewsWithAverage(BaseModel):
    average_rating: float
    reviews: List[ReviewResponse]

    model_config = {"from_attributes": True}

# ---------------- Product Schemas ----------------

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
    is_active: bool = True
    is_featured: bool = False


# ---------------- Image Schema ----------------

class ProductImageResponse(BaseModel):
    id: int
    product_id: int
    url: str
    position: int
    created_at: datetime

    class Config:
        orm_mode = True


# ---------------- Category Schema ----------------

class CategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    slug: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


# ---------------- Product Response Schema ----------------

class ProductResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: Decimal
    discount_price: Optional[Decimal] = None
    stock: int
    sku: Optional[str] = None
    slug: str
    category: CategoryResponse
    is_featured: bool
    status: str  # e.g., "pending", "approved", "rejected"
    is_active: bool
    images: List[ProductImageResponse] = Field(default_factory=list)
    seller_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class AddStockRequest(BaseModel):
    quantity: int = Field(gt=0)

class BulkUploadRow(ProductCreate):
    row_number: int
    status: str = "pending"  # pending, success, error
    error_message: Optional[str] = None


class BulkUploadResponse(BaseModel):
    total_records: int
    successful_records: int
    failed_records: int
    errors: List[BulkUploadRow]
    success_records: List[BulkUploadRow]

    class Config:
        orm_mode = True

# ---------------- LLM Schemas ----------------

class ReviewSummaryResponse(BaseModel):
    summary: str

class QARequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)

class QAResponse(BaseModel):
    answer: str
