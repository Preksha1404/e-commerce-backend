from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

# --- Review Schemas ---
class ReviewBase(BaseModel):
    name: str
    rating: float = Field(ge=0, le=5)
    comment: str

    model_config = {"from_attributes": True}

class ReviewResponse(ReviewBase):
    id: int
    product_id: int

    model_config = {"from_attributes": True}

class ReviewsWithAverage(BaseModel):
    average_rating: float
    reviews: List[ReviewResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}

# ---------------- ProductCreate Schema ----------------
class ProductCreate(BaseModel):
    name: str
    description: str
    price: Decimal = Field(ge=0)
    stock: int = Field(ge=0)
    category: str
    images: List[str] = Field(default_factory=list)

    sku: Optional[str] = None
    category_id: Optional[int] = None
    discount_price: Optional[Decimal] = Field(default=None, ge=0)
    is_active: bool = True
    is_featured: bool = False

    model_config = {"from_attributes": True}

# ---------------- Image Response Schema ----------------
class ProductImageResponse(BaseModel):
    id: int
    product_id: int
    url: str
    position: int
    created_at: datetime

    model_config = {"from_attributes": True}

# ---------------- Category Response Schema ----------------
class CategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    slug: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

# ---------------- Product Response Schema ----------------
class ProductResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: Decimal
    discount_price: Optional[Decimal] = None
    stock: int
    sku: Optional[str] = None
    slug: Optional[str] = None  # allow None if missing
    category: Optional[CategoryResponse] = None
    is_featured: Optional[bool] = False
    status: Optional[str] = None
    is_active: Optional[bool] = None
    images: List[ProductImageResponse] = Field(default_factory=list)
    seller_id: Optional[int] = None
    average_rating: Optional[float] = 0.0
    reviews: List[ReviewResponse] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


     

# ---------------- Additional Schemas ----------------
class AddStockRequest(BaseModel):
    quantity: int = Field(gt=0)

    model_config = {"from_attributes": True}

class BulkUploadRow(ProductCreate):
    row_number: int
    status: str = "pending"
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}

class BulkUploadResponse(BaseModel):
    total_records: int
    successful_records: int
    failed_records: int
    errors: List[BulkUploadRow]
    success_records: List[BulkUploadRow]

    model_config = {"from_attributes": True}
