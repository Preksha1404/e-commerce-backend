from fastapi import FastAPI
from src.core.database import Base, engine
from src.models import user
 
from src.api.endpoints import users, auth,adminseller, categories, product


Base.metadata.create_all(bind=engine) 

app = FastAPI(
    title="E-commerce Backend",
    description="API for user authentication and management",
    version="1.0.0"
)
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(categories.router, prefix="/categories", tags=["Categories"])
app.include_router(product.router, prefix="/products", tags=["Products"])
app.include_router(adminseller.router, prefix="/admin", tags=["Admin"])
