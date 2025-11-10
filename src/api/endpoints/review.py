from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from statistics import mean

from src.core.database import SessionLocal
from src.models import Product, Review
from src.schemas.products import ReviewBase, ReviewResponse, ReviewsWithAverage

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post(
    "/api/products/{product_id}/reviews",
    response_model=ReviewResponse,
    tags=["Reviews"]
)
def add_review(
    product_id: int,
    review: ReviewBase,
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    new_review = Review(
        product_id=product_id,
        name=review.name,
        rating=review.rating,
        comment=review.comment
    )
    db.add(new_review)
    db.commit()
    db.refresh(new_review)
    return new_review

@router.get(
    "/api/products/{product_id}/reviews",
    response_model=ReviewsWithAverage,
    tags=["Reviews"]
)
def get_reviews(
    product_id: int,
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    reviews = db.query(Review).filter(Review.product_id == product_id).all()
    avg_rating = round(mean([r.rating for r in reviews]), 2) if reviews else 0.0

    return ReviewsWithAverage(
        average_rating=avg_rating,
        reviews=reviews
    )
