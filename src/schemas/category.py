from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# 🔹 Base schema: common fields shared across create/update/response
class CategoryBase(BaseModel):
    name: str = Field(..., example="Electronics", description="Category name")
    description: Optional[str] = Field(None, example="All types of electronic devices")
    slug: Optional[str] = Field(None, example="electronics", description="SEO-friendly slug")
    parent_id: Optional[int] = Field(None, example=1, description="Parent category ID (if any)")
    is_active: bool = Field(True, description="Is the category active?")


# 🔹 Schema for creating a category
class CategoryCreate(CategoryBase):
    """
    Used when admin creates a new category.
    Inherits all fields from CategoryBase.
    """
    pass


# 🔹 Schema for updating a category
class CategoryUpdate(BaseModel):
    """
    Used for partial updates by admin.
    """
    name: Optional[str] = None
    description: Optional[str] = None
    slug: Optional[str] = None
    parent_id: Optional[int] = None
    is_active: Optional[bool] = None


# 🔹 Schema for API response
class CategoryResponse(CategoryBase):
    id: int = Field(..., example=1)
    created_at: Optional[datetime] = Field(None, example="2025-10-30T10:15:00")
    updated_at: Optional[datetime] = Field(None, example="2025-10-30T10:15:00")

       # allows ORM -> Pydantic model conversion

class CategoryRead(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    slug: Optional[str] = None
    parent_id: Optional[int] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    image_url:str

    
    
    class config:
        from_attribbutes=True
