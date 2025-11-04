from decimal import Decimal
from typing import List, Optional
from fastapi import FastAPI, File, Form, UploadFile
from src.core.database import engine, Base
from src.api.endpoints import users, auth, sellers, products, profile, orders, user_orders, seller_orders
from src.api.endpoints import users, auth, sellers, products, profile, cart
from src.core.seed import seed_admin
from contextlib import asynccontextmanager  
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.requests import Request
from pydantic import BaseModel, Field
import os
from src.api.endpoints import categories

 

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    seed_admin()
    yield


app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:5173",
    "https://ecommerce-eight-black.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.options("/{rest_of_path:path}")
async def preflight_handler(request: Request, rest_of_path: str):
    return JSONResponse(content={"message": "OK"})


# Create tables
Base.metadata.create_all(bind=engine)


@app.get("/")
def read_root():
    return {"message": "Hello, World!"}


# Include routers
app.include_router(users.router)
app.include_router(auth.router)
app.include_router(sellers.router)
app.include_router(profile.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(user_orders.router)
app.include_router(seller_orders.router)
app.include_router(categories.router)
app.include_router(cart.router)
