import os
from uuid import uuid4
from fastapi import APIRouter, File, Form, HTTPException, Path, UploadFile, status, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
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
    slug: str = Form(...),
     
     
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if current_user.role.lower() != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can create categories")

    # Save image
    os.makedirs("images/categories", exist_ok=True)
    filename = f"{uuid4().hex}_{image.filename}"
    file_path = os.path.join("images/categories", filename)
    with open(file_path, "wb") as f:
        f.write(await image.read())

    category_data = {
        "name": name,
        "description": description,
        "slug": slug,
        
        "image_url": file_path
    }

    return create_category_service(db=db, category_data=category_data)


# ------------------- UPDATE Category ------------------- #
@router.patch("/{category_id}", response_model=CategoryRead, dependencies=[Depends(require_admin)])
async def update_category(
    category_id: int = Path(..., ge=1),
    name: str = Form(None),
    description: str = Form(None),
    slug: str = Form(None),
     
   
    image: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    category = db.query(CategoryModel).filter(CategoryModel.id == category_id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    # Update fields if provided
    if name: category.name = name
    if description: category.description = description
    if slug: category.slug = slug
    
    

    # Update image if provided
    if image:
        os.makedirs("images/categories", exist_ok=True)
        filename = f"{uuid4().hex}_{image.filename}"
        file_path = os.path.join("images/categories", filename)
        with open(file_path, "wb") as f:
            f.write(await image.read())
        category.image_url = file_path

    db.add(category)
    db.commit()
    db.refresh(category)
    return category


# ------------------- GET Categories by Status ------------------- #
@router.get("/status/{is_active}", response_model=List[CategoryResponse])
def get_categories_by_status(
    is_active: bool,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role.lower() != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can view categories by status")

    categories = db.query(CategoryModel).filter(CategoryModel.is_active == is_active).all()
    if not categories:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No categories found for this status")

    return [
        {
            "id": cat.id,
            "name": cat.name,
            "description": cat.description,
            "slug": cat.slug,
            "parent_id": cat.parent_id,
            "is_active": cat.is_active,
            "image_url": cat.image_url
        } for cat in categories
    ]


# ------------------- DELETE Category ------------------- #
@router.delete("/{category_id}", status_code=status.HTTP_200_OK, dependencies=[Depends(require_admin)])
async def delete_category(
    category_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
):
    return delete_category_service(db, category_id)


# ------------------- GET Category Image ------------------- #
@router.get("/image/{filename}")
def get_category_image(filename: str):
    file_path = os.path.join("images/categories", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(file_path)
