from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from src.core.database import get_db
from src.utils.auth import get_current_active_user
from src.models.users import User
from src.schemas.wishlist import Wishlist as WishlistSchema, WishlistCreate
from src.services.wishlist_service import WishlistService

router = APIRouter(prefix="/wishlist", tags=["Wishlist"])

wishlist_service = WishlistService()

@router.get("/", response_model=List[WishlistSchema])
def get_wishlist(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """
    Fetch the canonical wishlist for the authenticated user.
    """
    return wishlist_service.get_wishlist(user_id=current_user.id, db=db)

@router.post("/", response_model=WishlistSchema)
def add_to_wishlist(wishlist_data: WishlistCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """
    Add a product to the wishlist.
    """
    try:
        return wishlist_service.add_to_wishlist(user_id=current_user.id, product_id=wishlist_data.product_id, db=db)
    except HTTPException as e:
        raise e

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_wishlist(product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """
    Remove one product from the wishlist.
    """
    try:
        wishlist_service.remove_from_wishlist(user_id=current_user.id, product_id=product_id, db=db)
        return
    except HTTPException as e:
        raise e

@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def clear_wishlist(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """
    Clear the wishlist.
    """
    wishlist_service.clear_wishlist(user_id=current_user.id, db=db)
    return
