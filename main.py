from fastapi import FastAPI
from src.core.database import engine, Base
from src.api.endpoints import users, auth, sellers, products, profile, cart
from src.core.seed import seed_admin
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.requests import Request

@asynccontextmanager
async def lifespan(app: FastAPI):
    seed_admin()
    yield
    
app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:5173",
    "https://ecommerce-eight-black.vercel.app",
]

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,           # List of allowed origins
    allow_credentials=True,          # Allow cookies / auth headers
    allow_methods=["*"],             # Allow all HTTP methods
    allow_headers=["*"],             # Allow all headers
)

@app.options("/{rest_of_path:path}")
async def preflight_handler(request: Request, rest_of_path: str):
    return JSONResponse(content={"message": "OK"})
                        
# Create tables if they don't exist
Base.metadata.create_all(bind=engine)


# (get_db is provided by src.core.database)


@app.get("/")
def read_root():
    return {"message": "Hello, World!"}
    
# Include routers
app.include_router(users.router)
app.include_router(auth.router)
app.include_router(sellers.router)
app.include_router(profile.router)
app.include_router(products.router)
app.include_router(cart.router)
