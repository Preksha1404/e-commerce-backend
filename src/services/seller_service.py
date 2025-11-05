from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile, status, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional
import os

from src.models.users import User
from src.schemas.users import SellerCreate, SellerUpdate
from src.utils.functions import get_pwd_hash
from src.utils.email import send_seller_verification_email, send_seller_welcome_email
from src.models.products import Product
from src.schemas.products import ProductCreate


# ---------------- SELLER ACCOUNT MANAGEMENT ----------------
class SellerService:
    @staticmethod
    def get_all_sellers(db: Session, current_user: User):
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view sellers"
            )

        return db.query(User).filter(User.role == "seller").all()

    @staticmethod
    async def register_seller(db: Session, seller: SellerCreate, background_tasks: BackgroundTasks):
        if db.query(User).filter(User.email == seller.email).first():
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"status": "error", "message": "Email already exists"},
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

        # Send seller verification email
        await send_seller_welcome_email(
            email=new_seller.email,
            full_name=new_seller.full_name,
            background_tasks=background_tasks,
        )

        return new_seller

    @staticmethod
    def get_seller_by_id(db: Session, seller_id: int, current_user: User):
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
    def update_seller_status(db: Session, seller_id: int, status: str, current_user: User):
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update seller status"
            )

        seller = db.query(User).filter(
            User.id == seller_id, User.role == "seller"
        ).first()
        if not seller:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
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
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status value"
            )

        db.commit()
        db.refresh(seller)
        return seller

    @staticmethod
    async def update_seller(
        db: Session,
        seller_id: int,
        seller_update: SellerUpdate,
        current_user: User,
        background_tasks: BackgroundTasks
    ):
        if current_user.id != seller_id or current_user.role != "seller":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this seller"
            )

        seller = db.query(User).filter(
            User.id == seller_id, User.role == "seller"
        ).first()
        if not seller:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Seller not found"
            )

        old_store_name = seller.store_name
        old_store_address = seller.store_address
        old_store_description = seller.store_description

        seller.full_name = seller_update.full_name or seller.full_name
        seller.phone = seller_update.phone or seller.phone
        seller.store_name = seller_update.store_name or seller.store_name
        seller.store_address = seller_update.store_address or seller.store_address
        seller.store_description = (
            seller_update.store_description or seller.store_description
        )

        business_changed = (
            (seller_update.store_name and seller_update.store_name != old_store_name)
            or (seller_update.store_address and seller_update.store_address != old_store_address)
            or (seller_update.store_description and seller_update.store_description != old_store_description)
        )

        if business_changed:
            seller.is_active = False
            await send_seller_verification_email(
                email=seller.email,
                full_name=seller.full_name,
                store_name=seller.store_name,
                store_address=seller.store_address,
                store_description=seller.store_description or "",
                background_tasks=background_tasks,
            )

        db.commit()
        db.refresh(seller)
        return seller

    # ✅ Combined seller + product dashboard
    @staticmethod
    def get_seller_with_products(db: Session, seller_id: int, current_user: User):
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

        seller = db.query(User).filter(
            User.id == seller_id, User.role == "seller"
        ).first()

        if not seller:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Seller not found"
            )

        products = db.query(Product).filter(Product.seller_id == seller_id).all()

        seller_data = {
            "id": seller.id,
            "full_name": seller.full_name,
            "email": seller.email,
            "phone": seller.phone,
            "store_name": seller.store_name,
            "store_address": seller.store_address,
            "store_description": seller.store_description,
            "is_active": seller.is_active,
            "is_blocked": seller.is_blocked,
            "created_at": seller.created_at,
        }

        product_data = [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "price": p.price,
                "stock": p.stock,
                "category_id": p.category_id,
                "images": p.images,
                "is_featured": p.is_featured,
                "created_at": p.created_at,
                "updated_at": p.updated_at,
            }
            for p in products
        ]

        total_revenue = sum(p.price * p.stock for p in products)

        return {
            "seller": seller_data,
            "total_products": len(product_data),
            "total_revenue": total_revenue,
            "products": product_data
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
        # ✅ Only sellers can add products
        if current_user.role != "seller":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to add products"
            )

        # ✅ Ensure the upload directory exists
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)

        # ✅ Handle uploaded images
        image_paths = []
        if images:
            for image in images:
                file_location = os.path.join(upload_dir, image.filename)
                with open(file_location, "wb") as f:
                    f.write(image.file.read())
                image_paths.append(file_location)

        # ✅ Create and save the new product
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
        if current_user.id != seller_id or current_user.role != "seller":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update products"
            )

        product = db.query(Product).filter(
            Product.id == prod_id, Product.seller_id == seller_id
        ).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )

        product.price = product.price + 10
        db.commit()
        db.refresh(product)
        return {"message": "Product updated successfully", "product": product}

    @staticmethod
    def delete_product(db: Session, seller_id: int, prod_id: int, current_user: User):
        if current_user.id != seller_id or current_user.role != "seller":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete products"
            )

        product = db.query(Product).filter(
            Product.id == prod_id, Product.seller_id == seller_id
        ).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )

        db.delete(product)
        db.commit()
        return {"message": "Product deleted successfully"}

    @staticmethod
    def get_all_products(db: Session, seller_id: int, current_user: User):
        if current_user.id != seller_id or current_user.role != "seller":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view products"
            )

        products = db.query(Product).filter(Product.seller_id == seller_id).all()
        return {"seller_id": seller_id, "products": products}
