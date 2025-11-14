from sqlalchemy.orm import Session
from sqlalchemy import func
from src.models.ratings import Rating
from src.models.products import Product   # adjust import if needed

def add_rating(db: Session, data):
    # 1. Save the new rating
    new_rating = Rating(
        product_id=data.product_id,
        rating=data.rating,
        user_id=data.user_id
    )

    db.add(new_rating)
    db.commit()
    db.refresh(new_rating) 

    # 2. Calculate total and count from the database
    total, count = db.query(
        func.sum(Rating.rating),
        func.count(Rating.id)
    ).filter(
        Rating.product_id == data.product_id
    ).first()

    # 3. Calculate average rating
    average = float(total) / float(count) if count else 0.0

    # 4. Update product table with new average
    product = db.query(Product).filter(Product.id == data.product_id).first()
    product.average_rating = average

    db.commit()
    db.refresh(product)

    return {
        "message": "Rating added successfully",
        "average_rating": average
    }
