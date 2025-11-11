from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from src.models.coupons import Coupon
from src.schemas.coupons import CouponCreate, CouponUpdate
from src.models.users import User
from src.utils.coupons import generate_coupon_code

class CouponService:
    def __init__(self, db: Session):
        self.db = db

    def list_coupons(self, current_user: User, role: str):
        if role == "admin":
            if current_user.role != "admin":
                raise HTTPException(status_code=403, detail="Not authorized")
            return self.db.query(Coupon).filter(Coupon.coupon_status == "True").all()

        elif role == "seller":
            if current_user.role != "seller":
                raise HTTPException(status_code=403, detail="Not authorized")
            return self.db.query(Coupon).filter(Coupon.user_id == current_user.id).filter(Coupon.coupon_status == "True").all()

        else:
            raise HTTPException(status_code=400, detail="Invalid role")

    def create_coupon(self, coupon_data: CouponCreate, current_user: User):
        if current_user.role not in ["admin", "seller"]:
            raise HTTPException(status_code=403, detail="Not authorized to create coupons")

        # Generate unique coupon code
        coupon_code = generate_coupon_code(coupon_data.coupon_name)

        # Check uniqueness
        if self.db.query(Coupon).filter(Coupon.coupon_code == coupon_code).first():
            raise HTTPException(status_code=400, detail="Coupon code already exists")

        status = coupon_data.expiry_date > datetime.now(timezone.utc)

        new_coupon = Coupon(
            coupon_name=coupon_data.coupon_name,
            coupon_code=coupon_code,
            discount_type=coupon_data.discount_type,
            discount_value=coupon_data.discount_value,
            minimum_value=coupon_data.minimum_value,
            expiry_date=coupon_data.expiry_date,
            coupon_status=status,
            usage_limit=coupon_data.usage_limit,
            user_id=current_user.id
        )
        self.db.add(new_coupon)
        self.db.commit()
        self.db.refresh(new_coupon)
        return new_coupon

    def get_coupon_by_id(self, coupon_id: int, current_user: User):
        if current_user.role not in ["admin", "seller"]:
            raise HTTPException(status_code=403, detail="Not authorized to view coupon details")

        coupon = self.db.query(Coupon).filter(Coupon.id == coupon_id).first()
        if not coupon:
            raise HTTPException(status_code=404, detail="Coupon not found")
        return coupon

    def update_coupon(self, coupon_id: int, coupon_data: CouponUpdate, current_user: User):
        coupon = self.db.query(Coupon).filter(Coupon.id == coupon_id).first()
        if not coupon:
            raise HTTPException(status_code=404, detail="Coupon not found")

        # Permission check
        if current_user.role == "seller" and coupon.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to update this coupon")
        
        elif current_user.role not in ["admin", "seller"]:
            raise HTTPException(status_code=403, detail="Not authorized")

        update_data = coupon_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if value is None or value == "":
                continue
            setattr(coupon, field, value)
            if field == "coupon_name":
                coupon.coupon_code = generate_coupon_code(value)

        if "expiry_date" in update_data and update_data["expiry_date"]:
            coupon.coupon_status = coupon.expiry_date > datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(coupon)
        return coupon

    def delete_coupon(self, coupon_id: int, current_user: User):
        coupon = self.db.query(Coupon).filter(Coupon.id == coupon_id).first()
        if not coupon:
            raise HTTPException(status_code=404, detail="Coupon not found")

        if current_user.role not in ["admin", "seller"] and coupon.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to delete coupons")

        # Soft delete
        coupon.coupon_status = False
        self.db.commit()
        return coupon