from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile, status, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional
import os
from src.utils.email_templates import seller_welcome_template, seller_verification_template
from src.services.email_service import send_email
from src.models.users import User
from src.schemas.users import SellerCreate, SellerUpdate
from src.utils.functions import get_pwd_hash
from src.utils.email import send_seller_block_status_email,send_seller_verification_email
from src.models.products import Product
from src.schemas.products import ProductCreate

# ---------------- SELLER ACCOUNT MANAGEMENT ----------------
class SellerService:
    @staticmethod
    def get_all_sellers(db: Session, current_user: User):
        """Admin: Get all sellers"""
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view sellers"
            )
        return db.query(User).filter(User.role == "seller").all()

    @staticmethod
    async def register_seller(db: Session, seller: SellerCreate):
        """Register new seller"""
        if db.query(User).filter(User.email == seller.email).first():
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"status": "error", "message": "Email already exists"},
            )

        # Hash password and create new seller
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

        # Generate email template
        subject, html_content = seller_welcome_template(new_seller.full_name)

        # Send email using generic function
        await send_email(
            background_tasks,
            to_email=new_seller.email,
            subject=subject,
            html_content=html_content
        )

        return new_seller

    @staticmethod
    def get_seller_by_id(db: Session, seller_id: int, current_user: User):
        """Admin or Seller: Get seller by ID"""
        if current_user.role != "admin" and current_user.id != seller_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this seller"
            )

        seller = db.query(User).filter(
            User.id == seller_id, User.role == "seller"
        ).first()

        if not seller:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Seller not found"
            )

        return seller

    @staticmethod
    def update_seller_status(db: Session, seller_id: int, status: str, current_user: User, background_tasks: BackgroundTasks):
        """Admin: Approve / Reject / Block / Unblock Seller"""
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update seller status"
            )

        seller = db.query(User).filter(User.id == seller_id, User.role == "seller").first()
        if not seller:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Seller not found"
            )

        if status == "approved":
            seller.is_active = True
            seller.is_blocked = False
        elif status == "blocked":
            seller.is_active = False
            seller.is_blocked = True
        elif status == "unblocked":
            seller.is_active = True
            seller.is_blocked = False
        elif status == "pending":
            seller.is_active = False
            seller.is_blocked = False
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status value"
            )

        db.commit()
        db.refresh(seller)

        # Send seller notification email in background
        background_tasks.add_task(
            send_seller_block_status_email,
            seller.email,
            seller.full_name,
            status
        )

        return {"message": f"Seller {status} successfully", "seller": seller}

    @staticmethod
    async def update_seller(
        db: Session,
        seller_id: int,
        seller_update: SellerUpdate,
        current_user: User,
        background_tasks: BackgroundTasks
    ):
        """Seller: Update profile info (store name/address/description)"""
        if current_user.id != seller_id or current_user.role != "seller":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this seller"
            )

        seller = db.query(User).filter(User.id == seller_id, User.role == "seller").first()
        if not seller:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Seller not found"
            )

        # Track old values
        old_store_name = seller.store_name
        old_store_address = seller.store_address
        old_store_description = seller.store_description

        # Update new fields
        seller.full_name = seller_update.full_name or seller.full_name
        seller.phone = seller_update.phone or seller.phone
        seller.store_name = seller_update.store_name or seller.store_name
        seller.store_address = seller_update.store_address or seller.store_address
        seller.store_description = seller_update.store_description or seller.store_description

        # Detect business info change
        business_changed = (
            (seller_update.store_name and seller_update.store_name != old_store_name)
            or (seller_update.store_address and seller_update.store_address != old_store_address)
            or (seller_update.store_description and seller_update.store_description != old_store_description)
        )

        if business_changed:
            seller.is_active = False

            subject, html_content = seller_verification_template(
                seller.full_name,
                seller.store_name,
                seller.store_address,
                seller.store_description
            )

            await send_email(
                background_tasks,
                to_email=seller.email,
                subject=subject,
                html_content=html_content
            )

        db.commit()
        db.refresh(seller)
        return seller

    @staticmethod
    def get_seller_with_products(db: Session, seller_id: int, current_user: User):
        """Admin or Seller: View seller with their products"""
        if current_user.role not in ["admin", "seller"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view seller details"
            )

        if current_user.role == "seller" and current_user.id != seller_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own details"
            )

        seller = db.query(User).filter(User.id == seller_id, User.role == "seller").first()
        if not seller:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Seller not found"
            )

        products = db.query(Product).filter(Product.seller_id == seller_id).all()
        total_revenue = sum(p.price * p.stock for p in products)

        return {
            "seller": seller,
            "total_products": len(products),
            "total_revenue": total_revenue,
            "products": products
        }


# ---------------- PRODUCT MANAGEMENT ----------------
class ProductService:
    @staticmethod
    def add_product(
        db: Session,
        name: str,
        description: Optional[str],
        price: float,
        stock: int,
        category_id: int,
        current_user: User,
        images: Optional[List[UploadFile]] = None,
    ):
        """Seller: Add a new product"""
        if current_user.role != "seller":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to add products"
            )

        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)

        image_paths = []
        if images:
            for image in images:
                file_location = os.path.join(upload_dir, image.filename)
                with open(file_location, "wb") as f:
                    f.write(image.file.read())
                image_paths.append(file_location)

        new_product = Product(
            name=name,
            description=description,
            price=price,
            stock=stock,
            category_id=category_id,
            seller_id=current_user.id,
            images=image_paths,
            is_featured=False,
        )

        db.add(new_product)
        db.commit()
        db.refresh(new_product)

        return {
            "message": "Product added successfully",
            "product": {
                "id": new_product.id,
                "name": new_product.name,
                "price": new_product.price,
                "stock": new_product.stock,
                "category_id": new_product.category_id,
                "images": image_paths,
            },
        }

    @staticmethod
    def update_product(db: Session, seller_id: int, prod_id: int, current_user: User):
        """Seller: Update product details"""
        if current_user.id != seller_id or current_user.role != "seller":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update products"
            )

        product = db.query(Product).filter(Product.id == prod_id, Product.seller_id == seller_id).first()
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

        product.price += 10  # Example update
        db.commit()
        db.refresh(product)
        return {"message": "Product updated successfully", "product": product}

    @staticmethod
    def delete_product(db: Session, seller_id: int, prod_id: int, current_user: User):
        """Seller: Delete a product"""
        if current_user.id != seller_id or current_user.role != "seller":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete products"
            )

        product = db.query(Product).filter(Product.id == prod_id, Product.seller_id == seller_id).first()
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

        db.delete(product)
        db.commit()
        return {"message": "Product deleted successfully"}

    @staticmethod
    def get_all_products(db: Session, seller_id: int, current_user: User):
        """Seller: Get all their products"""
        if current_user.id != seller_id or current_user.role != "seller":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view products"
            )

        products = db.query(Product).filter(Product.seller_id == seller_id).all()
        return {"seller_id": seller_id, "products": products}
