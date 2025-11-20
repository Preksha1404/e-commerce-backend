from pydantic import BaseModel
from typing import List
from src.schemas.products import ProductResponse

class WishlistBase(BaseModel):
    product_id: int

class WishlistCreate(WishlistBase):
    pass

class Wishlist(WishlistBase):
    id: int
    user_id: int
    product: ProductResponse

    class Config:
        orm_mode = True
