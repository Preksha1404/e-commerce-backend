from sqlalchemy.orm import Session
from src.models.products import Product

def create_product(db: Session, name: str, slug: str, sku: str, price: float, category_id: int, **kwargs):
    product = Product(name=name, slug=slug, sku=sku, price=price, category_id=category_id, **kwargs)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

def get_all_products(db: Session):
    return db.query(Product).all()

def get_product(db: Session, product_id: int):
    return db.query(Product).filter(Product.id == product_id).first()

def update_product(db: Session, product_id: int, **updates):
    product = get_product(db, product_id)
    if not product:
        return None
    for key, value in updates.items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product

def delete_product(db: Session, product_id: int):
    product = get_product(db, product_id)
    if product:
        db.delete(product)
        db.commit()
    return product
