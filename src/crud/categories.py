from sqlalchemy.orm import Session
from src.models.categories import Category

def create_category(db: Session, name: str, slug: str, description: str = None, parent_id: int = None):
    new_cat = Category(name=name, slug=slug, description=description, parent_id=parent_id)
    db.add(new_cat)
    db.commit()
    db.refresh(new_cat)
    return new_cat

def get_all_categories(db: Session):
    return db.query(Category).all()

def get_category(db: Session, category_id: int):
    return db.query(Category).filter(Category.id == category_id).first()

def update_category(db: Session, category_id: int, **updates):
    category = get_category(db, category_id)
    if not category:
        return None
    for key, value in updates.items():
        setattr(category, key, value)
    db.commit()
    db.refresh(category)
    return category

def delete_category(db: Session, category_id: int):
    category = get_category(db, category_id)
    if category:
        db.delete(category)
        db.commit()
    return category
