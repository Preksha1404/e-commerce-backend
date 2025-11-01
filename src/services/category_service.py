from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.models.products import Category as CategoryModel
from src.schemas.category import CategoryUpdate
from slugify import slugify
from src.core.cloudinary_config import cloudinary


# ---------------- GET CATEGORIES BY STATUS ---------------- #
def get_categories_by_status_service(db: Session, is_active: bool):
    categories = db.query(CategoryModel).filter(CategoryModel.is_active == is_active).all()
    if not categories:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No categories found for this status"
        )
    return categories


# ---------------- CREATE CATEGORY ---------------- #
def create_category_service(db: Session, name: str, description: str, image_url: str = None):
    """✅ Creates a category (expects image_url already uploaded to Cloudinary)."""
    new_category = CategoryModel(
        name=name,
        description=description,
        slug=slugify(name),
        image_url=image_url,
        is_active=True
    )

    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category


# ---------------- UPDATE CATEGORY ---------------- #
def update_category_service(db: Session, category_id: int, update_data: CategoryUpdate, image_url: str = None):
    """✅ Updates category details and optionally replaces Cloudinary image."""
    category = db.query(CategoryModel).filter(CategoryModel.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} not found"
        )

    update_fields = update_data.dict(exclude_unset=True)

    # ✅ Auto-update slug if name changes
    if "name" in update_fields and update_fields["name"]:
        category.slug = slugify(update_fields["name"])

    # ✅ Replace image if new one uploaded
    if image_url:
        category.image_url = image_url

    for field, value in update_fields.items():
        setattr(category, field, value)

    db.commit()
    db.refresh(category)
    return category


# ---------------- DELETE CATEGORY ---------------- #
def delete_category_service(db: Session, category_id: int):
    """✅ Deletes a category (admin-only)."""
    category = db.query(CategoryModel).filter(CategoryModel.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} not found"
        )

    db.delete(category)
    db.commit()

    return {"message": f"Category '{category.name}' deleted successfully."}
