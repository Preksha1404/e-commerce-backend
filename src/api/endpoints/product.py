from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.models.product import Product, ProductStatus
from src.models.user import User, UserRole
# from src.dependencies import get_current_user  # uncomment if you have auth

router = APIRouter(prefix="/products", tags=["Products"])

# 🟢 Get all approved products (public)
@router.get("/")
def get_all_products(db: Session = Depends(get_db)):
    products = db.query(Product).filter(Product.status == ProductStatus.APPROVED).all()
    return products


# 🟣 Seller creates product (goes for approval)
@router.post("/")
def create_product(name: str, price: float, db: Session = Depends(get_db)):
    # Example assumes seller info is known (later link with auth)
    new_product = Product(
        name=name,
        price=price,
        status=ProductStatus.PENDING,  # 🟡 Wait for admin approval
        is_active=False
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return {"message": "Product submitted for admin approval", "product_id": new_product.id}


# 🟡 Admin approves a product
@router.put("/approve/{product_id}")
def approve_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.status = ProductStatus.APPROVED
    product.is_active = True
    db.commit()
    db.refresh(product)
    return {"message": f"Product '{product.name}' approved successfully"}


# 🔴 Admin rejects a product
@router.put("/reject/{product_id}")
def reject_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.status = ProductStatus.REJECTED
    product.is_active = False
    db.commit()
    db.refresh(product)
    return {"message": f"Product '{product.name}' rejected by admin"}


# 🟠 Admin can view all pending products
@router.get("/pending")
def get_pending_products(db: Session = Depends(get_db)):
    pending = db.query(Product).filter(Product.status == ProductStatus.PENDING).all()
    return pending
