from fastapi import FastAPI
from src.core.database import SessionLocal, engine, Base
from src.api.endpoints import users, auth, sellers, admin
from src.core.seed import seed_admin
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    seed_admin()
    yield
    
app = FastAPI(lifespan=lifespan)

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def read_root():
    return {"message": "Hello, World!"}
    
# Include routers
app.include_router(users.router)
app.include_router(auth.router)
app.include_router(sellers.router)
app.include_router(admin.router)