from sqlalchemy.orm import Session
from fastapi import HTTPException, status, BackgroundTasks
from fastapi.responses import JSONResponse
from src.models.users import User
from src.schemas.users import SellerCreate, SellerUpdate
from src.utils.functions import get_pwd_hash
from src.utils.email import send_seller_verification_email

class SellerService:
    @staticmethod
    def get_all_sellers(db: Session, current_user: User):
        if current_user.role != "admin":
            raise HTTPException(
                status_code=403,
                detail="Not authorized to view sellers"
            )
        sellers = db.query(User).filter(User.role == "seller").all()
        return sellers

    @staticmethod
    def register_seller(db: Session, seller: SellerCreate):
        # Check if email already exists
        if db.query(User).filter(User.email == seller.email).first():
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "status": "error",
                    "message": "Email already exists"
                }
            )

        hashed_password = get_pwd_hash(seller.password)
        
        new_seller = User(
            email=seller.email,
            full_name=seller.full_name,
            hashed_password=hashed_password,
            phone=seller.phone,
            store_name=seller.store_name,
            store_address=seller.store_address,
            store_description=seller.store_description,
            role="seller",
            is_active=False,
            is_blocked=False,
        )
        db.add(new_seller)
        db.commit()
        db.refresh(new_seller)
        return new_seller
    
    @staticmethod
    def get_seller_by_id(db: Session, seller_id: int, current_user: User):
        """Get seller details by ID (accessible by admin or the seller themselves)."""
        if current_user.role != "admin" and current_user.id != seller_id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to view this seller"
            )

        seller = db.query(User).filter(User.id == seller_id, User.role == "seller").first()

        if not seller:
            raise HTTPException(
                status_code=404,
                detail="Seller not found"
            )

        return seller

    @staticmethod
    def update_seller_status(db: Session, seller_id: int, status: str, current_user: User):
        """Admin updates seller approval status."""
        if current_user.role != "admin":
            raise HTTPException(
                status_code=403,
                detail="Not authorized to update seller status"
            )

        seller = db.query(User).filter(User.id == seller_id, User.role == "seller").first()
        if not seller:
            raise HTTPException(
                status_code=404,
                detail="Seller not found"
            )

        if status == "approved":
            seller.is_active = True
            seller.is_blocked = False
        elif status == "rejected":
            seller.is_active = False
            seller.is_blocked = True
        elif status == "pending":
            seller.is_active = False
            seller.is_blocked = False
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid status value"
            )

        db.commit()
        db.refresh(seller)
        return seller
    
    @staticmethod
    async def update_seller(db: Session, seller_id: int, seller_update: SellerUpdate, current_user: User, background_tasks: BackgroundTasks):
        """Seller updates their own profile."""
        if current_user.id != seller_id or current_user.role != "seller":
            raise HTTPException(
                status_code=403,
                detail="Not authorized to update this seller"
            )

        seller = db.query(User).filter(User.id == seller_id, User.role == "seller").first()
        if not seller:
            raise HTTPException(
                status_code=404,
                detail="Seller not found"
            )

        # Track old data
        old_store_name = seller.store_name
        old_store_address = seller.store_address
        old_store_description = seller.store_description

        # Update fields
        seller.full_name = seller_update.full_name or seller.full_name
        seller.phone = seller_update.phone or seller.phone
        seller.store_name = seller_update.store_name or seller.store_name
        seller.store_address = seller_update.store_address or seller.store_address
        seller.store_description = seller_update.store_description or seller.store_description

        # Detect if business info changed
        business_changed = (
            (seller_update.store_name and seller_update.store_name != old_store_name)
            or (seller_update.store_address and seller_update.store_address != old_store_address)
            or (seller_update.store_description and seller_update.store_description != old_store_description)
        )

        if business_changed:
            seller.is_active = False # Deactivate account

            # Send verification email
            await send_seller_verification_email(
                email=seller.email,
                full_name=seller.full_name,
                store_name=seller.store_name,
                store_address=seller.store_address,
                store_description=seller.store_description or "",
                background_tasks=background_tasks
            )

        db.commit()
        db.refresh(seller)
        return seller