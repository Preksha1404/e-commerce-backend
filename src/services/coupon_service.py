from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from src.models.coupons import Coupon
from src.schemas.coupons import CouponCreate, CouponUpdate
from src.models.users import User
from src.utils.coupons import generate_coupon_code
from datetime import datetime, timezone

def create_coupon(db: Session, coupon_data: CouponCreate, current_user: User):

    if current_user.role not in ["admin", "seller"]:
        raise HTTPException(status_code=403, detail="Not authorized to create coupons")

    # Generate unique coupon code
    coupon_data.coupon_code = generate_coupon_code(coupon_data.coupon_name)

    # Check uniqueness
    existing_coupon = db.query(Coupon).filter(Coupon.coupon_code == coupon_data.coupon_code).first()
    if existing_coupon:
        raise HTTPException(status_code=400, detail="Coupon code already exists")

    # Set coupon_status based on expiry_date
    status = True if coupon_data.expiry_date > datetime.now(timezone.utc) else False

    new_coupon = Coupon(
        coupon_name=coupon_data.coupon_name,
        coupon_code=coupon_data.coupon_code,
        discount_type=coupon_data.discount_type,
        discount_value=coupon_data.discount_value,
        minimum_value=coupon_data.minimum_value,
        expiry_date=coupon_data.expiry_date,
        coupon_status=status,
        usage_limit=coupon_data.usage_limit,
        user_id=current_user.id
    )

    db.add(new_coupon)
    db.commit()
    db.refresh(new_coupon)
    return new_coupon

def get_coupon_by_id(db: Session, coupon_id: int, current_user: User):

    if current_user.role not in ["admin", "seller"]:
        raise HTTPException(status_code=403, detail="Not authorized to view coupon details")

    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()

    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")

    return coupon

def update_coupon(db: Session, coupon_id: int, coupon_data: CouponUpdate, current_user: User):
    """
    Update a coupon. Admins can update any coupon, sellers can update their own coupons.
    """
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")

    # Role-based permission check
    if current_user.role not in ["admin", "seller"] and coupon.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update coupons")
    
    update_data = coupon_data.dict(exclude_unset=True)

    for field, value in update_data.items():
        # Skip empty strings → retain old value
        if value == "" or value is None:
            continue

        setattr(coupon, field, value)

        # Regenerate coupon code if name updated
        if field == "coupon_name":
            coupon.coupon_code = generate_coupon_code(value)

    # Update coupon_status if expiry_date changed
    if "expiry_date" in update_data and update_data["expiry_date"]:
        current_time = datetime.now(timezone.utc)
        coupon.coupon_status = coupon.expiry_date > current_time

    db.commit()
    db.refresh(coupon)
    return coupon

def delete_coupon(db: Session, coupon_id: int, current_user: User):
    """
    Delete or deactivate a coupon. Admins can delete any coupon, sellers can delete their own coupons.
    """

    if current_user.role not in ["admin", "seller"] and coupon.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete coupons")
    
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()

    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")

    # Soft delete
    coupon.coupon_status = False
    db.commit()
    return coupon