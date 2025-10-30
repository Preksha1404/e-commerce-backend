from fastapi import APIRouter, HTTPException, Path, status, Depends
from sqlalchemy.orm import Session
from typing import List
from src.core.database import SessionLocal
from src.models.products import Category as CategoryModel
from src.models.users import User  
from src.schemas.category import CategoryResponse,CategoryCreate,CategoryUpdate,CategoryRead
from src.services.category_service import create_category_service,get_categories_by_status_service,delete_category_service
from src.utils.auth import get_current_active_user,require_admin


# ✅ Dependency for DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


router = APIRouter(prefix="/category", tags=["Category"])


@router.get("/status/{is_active}", response_model=List[CategoryResponse])
def get_categories_by_status(
    is_active: bool,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    ✅ Admin can filter categories by active/inactive status
    """
    if current_user.role.lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can view categories by status"
        )

    categories = db.query(CategoryModel).filter(CategoryModel.is_active == is_active).all()

    if not categories:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No categories found for this status"
        )

    return categories


@router.post("/create", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category_data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    ✅ Admin can create a new category
    """
    # Authorization check
    if current_user.role.lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can create categories"
        )

    # Call service layer
    return create_category_service(db=db, category_data=category_data)



@router.patch("/{category_id}", response_model=CategoryRead, dependencies=[Depends(require_admin)])
async def update_category(
    category_id: int = Path(..., ge=1),
    category_update: CategoryUpdate = Depends(),
    db: Session = Depends(get_db),
):
    # Fetch existing category
    category = db.query(CategoryModel).filter(CategoryModel.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Apply updates
    category.name = category_update.name
    category.description = category_update.description
    # Save changes
    db.add(category)
    db.commit()
    db.refresh(category)

    return category

@router.delete("/{category_id}", status_code=status.HTTP_200_OK, dependencies=[Depends(require_admin)])
async def delete_category(
    category_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
):
    """
    ✅ Admin-only endpoint to delete a category by ID
    """
    return delete_category_service(db, category_id)