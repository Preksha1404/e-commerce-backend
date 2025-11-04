from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.utils.auth import get_current_active_user
from src.models.users import User
from src.schemas.cart import AddItemRequest, UpdateItemRequest, ApplyCouponRequest, CartOut, AddItemResponse, UpdateItemResponse, RemoveItemResponse
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


@router.post("/add", response_model=AddItemResponse)
def add_to_cart(payload: AddItemRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    try:
        cart = add_item(db, current_user.id, payload.product_id, payload.quantity)
        return AddItemResponse(
            message="Item added to cart",
            items=cart.items,
            subtotal=cart.subtotal,
            discount=cart.discount,
            total=cart.total,
            coupon=cart.coupon
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/update", response_model=UpdateItemResponse)
def update_cart_item(payload: UpdateItemRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    try:
        cart = update_item(db, current_user.id, payload.product_id, payload.quantity)
        return UpdateItemResponse(
            message="Cart item updated",
            items=cart.items,
            subtotal=cart.subtotal,
            discount=cart.discount,
            total=cart.total,
            coupon=cart.coupon
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/remove/{product_id}", response_model=RemoveItemResponse)
def remove_cart_item(product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    cart = remove_item(db, current_user.id, product_id)
    return RemoveItemResponse(
        message="Item removed from cart",
        items=cart.items,
        subtotal=cart.subtotal,
        discount=cart.discount,
        total=cart.total,
        coupon=cart.coupon
    )


@router.delete("/clear", response_model=CartOut)
def clear_user_cart(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return clear_cart(db, current_user.id)


@router.post("/apply-coupon", response_model=CartOut)
def apply_coupon_to_cart(payload: ApplyCouponRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    try:
        return apply_coupon(db, current_user.id, payload.code)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


