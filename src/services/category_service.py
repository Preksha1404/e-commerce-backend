from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.models.products import Category as CategoryModel
from src.schemas.category import CategoryCreate,CategoryUpdate


def get_categories_by_status_service(db: Session, is_active: bool):
    """
    🧠 Service layer: handles business logic (data fetching)
    """
    # 1. Query database
    categories = db.query(CategoryModel).filter(CategoryModel.is_active == is_active).all()

    # 2. Handle if no data found
    if not categories:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No categories found for this status"
        )

    # 3. Return list of ORM objects
    return categories
def create_category_service(db: Session, category_data: dict):
    existing_category = db.query(CategoryModel) \
        .filter(CategoryModel.name == category_data["name"]) \
        .first()
    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category with this name already exists"
        )

    new_category = CategoryModel(
        name = category_data["name"],
        description = category_data.get("description"),
        slug = category_data["slug"],
        parent_id = category_data.get("parent_id"),
        is_active = category_data.get("is_active", True),
        image_url = category_data.get("image_url")
    )

    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category



def update_category_service(db: Session, category_id: int, update_data: CategoryUpdate):
    """
    🧠 Service: Update an existing category
    """
    category = db.query(CategoryModel).filter(CategoryModel.id == category_id).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} not found"
        )

    # Update only fields provided in request
    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(category, field, value)

    db.commit()
    db.refresh(category)
    return category

def delete_category_service(db: Session, category_id: int):
    """
    🧠 Service: Delete a category by its ID
    """

    # Step 1 — Fetch category
    category = db.query(CategoryModel).filter(CategoryModel.id == category_id).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} not found"
        )

    # Step 2 — Delete category
    db.delete(category)
    db.commit()

    return {"message": f"Category '{category.name}' deleted successfully."}