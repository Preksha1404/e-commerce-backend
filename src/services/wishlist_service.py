from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.models.wishlist import Wishlist
from src.models.products import Product
from src.schemas.wishlist import Wishlist as WishlistSchema
from src.services.product_service import ProductService
from typing import List

class WishlistService:

    def get_wishlist(self, user_id: int, db: Session):
        from src.services.product_service import ProductService
        product_service = ProductService(db=db, current_user=user_id)

        wishlist_items = (
            db.query(Wishlist)
            .filter(Wishlist.user_id == user_id)
            .all()
        )

        for item in wishlist_items:
            avg_rating = product_service.get_average_rating(item.product_id)
            item.product.average_rating = avg_rating

        return wishlist_items

    def add_to_wishlist(self, user_id: int, product_id: int, db: Session):
        from src.services.product_service import ProductService
        product_service = ProductService(db=db, current_user=user_id)

        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

        wishlist_item = db.query(Wishlist).filter(
            Wishlist.user_id == user_id,
            Wishlist.product_id == product_id
        ).first()

        if wishlist_item:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product already in wishlist")

        new_wishlist_item = Wishlist(user_id=user_id, product_id=product_id)
        db.add(new_wishlist_item)
        db.commit()
        db.refresh(new_wishlist_item)

        # inject rating
        avg_rating = product_service.get_average_rating(product_id)
        new_wishlist_item.product = product
        new_wishlist_item.product.average_rating = avg_rating

        return new_wishlist_item

    def remove_from_wishlist(self, user_id: int, product_id: int, db: Session):
        wishlist_item = db.query(Wishlist).filter(Wishlist.user_id == user_id, Wishlist.product_id == product_id).first()
        if not wishlist_item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not in wishlist")

        db.delete(wishlist_item)
        db.commit()
        return

    def clear_wishlist(self, user_id: int, db: Session):
        db.query(Wishlist).filter(Wishlist.user_id == user_id).delete()
        db.commit()
        return