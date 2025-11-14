from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from statistics import mean

from src.core.database import SessionLocal
from src.models import Product, Review
from src.schemas.products import ReviewBase, ReviewResponse, ReviewsWithAverage
from src.schemas.users import User
from src.utils.auth import get_current_active_user

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------- Add Review ----------------
@router.post(
    "/products/{product_id}/reviews",
    response_model=ReviewResponse,
    tags=["Reviews"]
)
def add_review(
    review: ReviewBase,
    product_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)  # login required
):
    # ✅ Allow only customers
    if current_user.role.lower() != "customer":
        raise HTTPException(
            status_code=403,
            detail="Only customers can add reviews."
        )

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # ✅ Prevent duplicate reviews
    existing_review = (
        db.query(Review)
        .filter(Review.product_id == product_id, Review.name == current_user.full_name)
        .first()
    )
    if existing_review:
        raise HTTPException(
            status_code=400,
            detail="You have already reviewed this product."
        )

    new_review = Review(
        product_id=product_id,
        name=current_user.full_name,
        rating=review.rating,
        comment=review.comment
    )
    db.add(new_review)
    db.commit()
    db.refresh(new_review)
    return new_review

# ---------------- Get Reviews ----------------
@router.get(
    "/products/{product_id}/reviews",
    response_model=ReviewsWithAverage,
    tags=["Reviews"]
)
def get_reviews(
    product_id: int = Path(..., ge=1),
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