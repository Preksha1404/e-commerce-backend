import cloudinary
import cloudinary.uploader
import os
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
import cloudinary.uploader
from src.models.users import User
from src.utils.auth import get_current_active_user
from src.core.database import SessionLocal

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router = APIRouter(prefix="/profile", tags=["Profile"])

@router.post("/upload-picture")
async def upload_profile_picture(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    user=db.query(User).filter(User.id == current_user.id).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an image.")
    
    try:
        upload_result = cloudinary.uploader.upload(
            file.file,
            folder=f"user_{current_user.id}/profile_pictures",
            overwrite=True
        )
        image_url = upload_result.get("secure_url")

        # Update user's profile picture in DB
        user.profile_picture = image_url
        db.commit()
        db.refresh(user)

        return {"message": "Profile picture uploaded successfully", "image_url": image_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
