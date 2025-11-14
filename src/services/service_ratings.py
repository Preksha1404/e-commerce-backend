from sqlalchemy.orm import Session
from src.models.ratings import Rating

def add_rating(db: Session, data):
    new_rating = Rating(
        product_id=data.product_id,
        rating=data.rating,
        user_id=data.user_id
    )

    db.add(new_rating)
    db.commit()
    db.refresh(new_rating)
    return new_rating
