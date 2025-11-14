from http.client import HTTPException
from fastapi import APIRouter, Depends # type: ignore
from sqlalchemy.orm import Session # type: ignore
from src.core.database import get_db
from src.models.products import Product
from src.schemas.ratings import RatingCreate, RatingResponse
from src.services.service_ratings import add_rating

router = APIRouter()

@router.post("/ratings", response_model=RatingResponse, status_code=status.HTTP_201_CREATED)
def rate_product(data: RatingCreate, db: Session = Depends(get_db)):
 
    product = db.query(Product).filter(Product.id == data.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    
    return add_rating(db, data)
