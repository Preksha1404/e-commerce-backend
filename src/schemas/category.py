from pydantic import BaseModel, Field # type: ignore
from typing import Optional
from datetime import datetime


# 🔹 Base schema: shared fields (no slug)
class CategoryBase(BaseModel):
    name: str = Field(..., example="Electronics", description="Category name")
    description: Optional[str] = Field(None, example="All types of electronic devices")


# 🔹 Schema for creating a category
class CategoryCreate(CategoryBase):
    """Used when admin creates a new category."""
    pass


# 🔹 Schema for updating a category (image_url added)
class CategoryUpdate(BaseModel):
    """Used for partial updates by admin."""
    name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None  # ✅ allow updating image


# 🔹 Schema for API response
class CategoryResponse(CategoryBase):
    id: int = Field(..., example=1)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    image_url: Optional[str] = None  # ✅ matches DB column

    class Config:
        from_attributes = True


# 🔹 Schema for GET operations
class CategoryRead(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
