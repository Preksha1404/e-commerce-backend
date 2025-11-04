from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.utils.auth import get_current_active_user
from src.models.users import User
from src.schemas.cart import AddItemRequest, UpdateItemRequest, ApplyCouponRequest, CartOut, MessageResponse
from src.services.cart_service import (
    get_cart,
    add_item,
    update_item,
    remove_item,
    clear_cart,
    apply_coupon,
)


router = APIRouter(prefix="/cart", tags=["Cart"])


@router.get("/", response_model=CartOut)
def get_user_cart(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return get_cart(db, current_user.id)


@router.post("/add", response_model=MessageResponse)
def add_to_cart(payload: AddItemRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    try:
        add_item(db, current_user.id, payload.product_id, payload.quantity)
        return MessageResponse(message="Item added to cart")
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/update", response_model=CartOut)
def update_cart_item(payload: UpdateItemRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    try:
        return update_item(db, current_user.id, payload.product_id, payload.quantity)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/remove/{product_id}", response_model=CartOut)
def remove_cart_item(product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return remove_item(db, current_user.id, product_id)


@router.delete("/clear", response_model=CartOut)
def clear_user_cart(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return clear_cart(db, current_user.id)


@router.post("/apply-coupon", response_model=CartOut)
def apply_coupon_to_cart(payload: ApplyCouponRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    try:
        return apply_coupon(db, current_user.id, payload.code)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


