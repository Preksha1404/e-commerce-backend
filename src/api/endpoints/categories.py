from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.models.categories import Category  # adjust model name

router = APIRouter()

@router.get("/")
def get_all_categories(db: Session = Depends(get_db)):
    return db.query(Category).all()

@router.post("/")
def create_category(name: str, db: Session = Depends(get_db)):
    new_category = Category(name=name)
    db.add(new_category)
    db.commit()
    db.refresh(new_category) 
    return new_category
