# GET	--> /coupons	            --> List all coupons (Admin only)
# GET	--> /coupons/sellers	    --> List all seller coupons (Seller for own coupons)
# POST	--> /coupons	            --> Create new coupon	(Admin → global; Seller → product-specific)
# GET	--> /coupons/{coupon_id}	--> Get coupon details by ID (Admin/Seller)
# PATCH	--> /coupons/{coupon_id}	--> Update coupon	(Admin/Seller)
# DELETE--> /coupons/{coupon_id}	--> Delete or deactivate coupon	(Admin/Seller)
# POST	--> /coupons/apply	        --> Apply coupon to cart (validate, calculate discount)	--> Customer

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.schemas.coupons import (
    CouponCreate,
    CouponUpdate,
    CouponResponse,
)

from src.services.coupon_service import create_coupon, get_coupon_by_id, update_coupon, delete_coupon
from src.core.database import get_db
from src.utils.auth import get_current_active_user
from src.models.users import User

router = APIRouter(prefix="/coupons", tags=["Coupons"])

@router.post("/", response_model=CouponResponse)
def create_new_coupon(
    coupon_data: CouponCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create a new coupon. Admins can create global coupons, sellers can create product-specific coupons.
    """
    new_coupon = create_coupon(db, coupon_data, current_user)
    return new_coupon

@router.get("/{coupon_id}", response_model=CouponResponse)
def get_coupon_details(
    coupon_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get coupon details by ID. Accessible by Admins and Sellers (for their own coupons).
    """
    coupon = get_coupon_by_id(db, coupon_id, current_user)
    return coupon
    
@router.patch("/{coupon_id}", response_model=CouponResponse)
def update_existing_coupon(
    coupon_id: int,
    coupon_data: CouponUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return update_coupon(db, coupon_id, coupon_data, current_user)


@router.delete("/{coupon_id}", response_model=dict)
def delete_existing_coupon(
    coupon_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    delete_coupon(db, coupon_id, current_user)
    return {"detail": "Coupon deleted/deactivated successfully"}