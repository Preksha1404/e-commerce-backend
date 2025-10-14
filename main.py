from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from src.core.database import SessionLocal, engine, Base
from src.models.users import User

app = FastAPI()

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


# Example route to test DB connection
@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users
