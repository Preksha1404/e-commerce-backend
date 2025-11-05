# src/core/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

CONNECTION_URL = os.getenv("DATABASE_URL")
if not CONNECTION_URL:
    raise ValueError("DATABASE_URL is not set in environment variables")

# ✅ Create engine
engine = create_engine(
    CONNECTION_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# ✅ Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ✅ Base model for ORM
Base = declarative_base()


# ✅ Dependency for FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ⚠️ DO NOT import models here — it causes circular imports.
# All model imports should happen in `main.py` after `Base` is defined.
