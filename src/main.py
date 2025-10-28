from fastapi import FastAPI
from src.core.database import Base, engine
from src.models import user  # registers your tables
from src.routers import auth, users

# Create tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="E-commerce Backend",
    description="API for user authentication and management",
    version="1.0.0"
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
