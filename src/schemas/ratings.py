from pydantic import BaseModel

class RatingCreate(BaseModel):
    product_id: int
    rating: float   # 1 to 5
    user_id: int | None = None


class RatingResponse(BaseModel):
    id: int
    product_id: int
    rating: float
    user_id: int | None

    class Config:
        from_attributes = True