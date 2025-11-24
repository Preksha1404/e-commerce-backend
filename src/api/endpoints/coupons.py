# GET	--> /coupons	            --> List all coupons (Admin only)
# GET	--> /coupons/sellers	    --> List all seller coupons (Seller for own coupons)
# POST	--> /coupons	            --> Create new coupon	(Admin → global; Seller → product-specific)
# GET	--> /coupons/{coupon_id}	--> Get coupon details by ID (Admin/Seller)
# PATCH	--> /coupons/{coupon_id}	--> Update coupon	(Admin/Seller)
# DELETE--> /coupons/{coupon_id}	--> Delete or deactivate coupon	(Admin/Seller)

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.services.coupon_service import CouponService
from src.schemas.coupons import CouponCreate, CouponUpdate, CouponResponse
from src.core.database import get_db
from src.utils.auth import get_current_active_user
from src.models.users import User

router = APIRouter(prefix="/coupons", tags=["Coupons"])

@router.get("/", response_model=list[CouponResponse])
def list_coupons(
    role: str = Query(..., description="Role of the user: admin or seller"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = CouponService(db)
    return service.list_coupons(current_user, role)

@router.get("/customer", summary="List coupons available to a customer")
def get_customer_coupons(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    service = CouponService(db)
    return service.list_coupons_for_customer(current_user.id)

@router.post("/", response_model=CouponResponse)
def create_new_coupon(
    coupon_data: CouponCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = CouponService(db)
    return service.create_coupon(coupon_data, current_user)

@router.get("/{coupon_id}", response_model=CouponResponse)
def get_coupon_details(
    coupon_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = CouponService(db)
    return service.get_coupon_by_id(coupon_id, current_user)

@router.patch("/{coupon_id}", response_model=CouponResponse)
def update_existing_coupon(
    coupon_id: int,
    coupon_data: CouponUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = CouponService(db)
    return service.update_coupon(coupon_id, coupon_data, current_user)

@router.delete("/{coupon_id}", response_model=dict)
def delete_existing_coupon(
    coupon_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = CouponService(db)
    service.delete_coupon(coupon_id, current_user)
    return {"detail": "Coupon deleted/deactivated successfully"}
 