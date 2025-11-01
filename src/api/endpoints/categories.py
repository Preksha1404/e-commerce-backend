import os
from uuid import uuid4
from fastapi import (
    APIRouter, File, Form, HTTPException, Path, UploadFile, status, Depends
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
from src.core.cloudinary_config import cloudinary
from src.core.database import SessionLocal
from src.models.products import Category as CategoryModel
from src.models.users import User
from src.schemas.category import CategoryResponse, CategoryRead
from src.services.category_service import create_category_service, delete_category_service
from src.utils.auth import get_current_active_user, require_admin

router = APIRouter(prefix="/category", tags=["Category"])


# ------------------- DB Dependency ------------------- #
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ------------------- CREATE Category ------------------- #
@router.post("/create", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    name: str = Form(...),
    description: str = Form(None),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """✅ Only admin can create categories"""
    if current_user.role.lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can create categories",
        )

    # ✅ Upload image to Cloudinary
    try:
        upload_result = cloudinary.uploader.upload(
            image.file,
            folder="ecommerce/categories",
            public_id=f"{uuid4().hex}_{image.filename.split('.')[0]}",
            overwrite=True,
            resource_type="image",
        )
        image_url = upload_result.get("secure_url")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")

    # ✅ Call service properly
    return create_category_service(
        db=db,
        name=name,
        description=description,
        image_url=image_url,
    )


# ------------------- UPDATE Category ------------------- #
@router.patch("/{category_id}", response_model=CategoryRead, dependencies=[Depends(require_admin)])
async def update_category(
    category_id: int = Path(..., ge=1),
    name: str = Form(None),
    description: str = Form(None),
    image: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    """✅ Update category details (Admin only)"""
    category = db.query(CategoryModel).filter(CategoryModel.id == category_id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    # Update provided fields
    if name:
        category.name = name
    if description:
        category.description = description

    # ✅ Upload new image to Cloudinary if provided
    if image:
        try:
            upload_result = cloudinary.uploader.upload(
                image.file,
                folder="ecommerce/categories",
                public_id=f"{uuid4().hex}_{image.filename.split('.')[0]}",
                overwrite=True,
                resource_type="image",
            )
            category.image_url = upload_result.get("secure_url")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")

    db.commit()
    db.refresh(category)
    return category


# ------------------- GET ALL Categories ------------------- #
@router.get("/", response_model=List[CategoryResponse])
def get_all_categories(db: Session = Depends(get_db)):
    """✅ Retrieve all categories"""
    categories = db.query(CategoryModel).all()
    if not categories:
        raise HTTPException(status_code=404, detail="No categories found")
    return categories


# ------------------- DELETE Category ------------------- #
@router.delete("/{category_id}", status_code=status.HTTP_200_OK, dependencies=[Depends(require_admin)])
async def delete_category(
    category_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
):
    """✅ Delete category (Admin only)"""
    return delete_category_service(db, category_id)


# ------------------- GET Category Image ------------------- #
@router.get("/image/{filename}")
def get_category_image(filename: str):
    """✅ Fetch category image from local storage (legacy)"""
    file_path = os.path.join("images/categories", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(file_path)
