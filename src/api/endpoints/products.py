from fastapi import APIRouter, Depends, UploadFile, File, status, Form, Body, Cookie, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Union
from src.core.database import get_db
from src.models.users import User
from src.models.products import Product
from src.schemas.products import BulkUploadResponse, ProductResponse, AddStockRequest, QARequest
from src.utils.auth import get_current_active_user
from src.services.product_service import ProductService
import cloudinary
import os

router = APIRouter(prefix="/products", tags=["Products"])

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)


@router.get("/", response_model=List[ProductResponse])
def list_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    ):
    return ProductService(db, current_user).list_products()

@router.get("/approved/", response_model=List[ProductResponse])
def list_approved_products(
    db: Session = Depends(get_db),
    ):
    products = (
            db.query(Product)
            .filter(Product.status == "approved", Product.is_active == True, Product.is_deleted == False)
            .all()
        )
    service = ProductService(db, None)
    for product in products:
        product.average_rating = service.get_average_rating(product.id)
    return products

@router.get("/category/{category_name}/", response_model=List[ProductResponse])
def get_products_by_category_name(category_name: str, db: Session = Depends(get_db)):
    return ProductService(db, None).get_products_by_category_name(category_name)


def get_optional_user(
    access_token: Optional[str] = Cookie(None, include_in_schema=False),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Optional authentication - returns user if token is present, None otherwise"""
    if not access_token:
        return None
    try:
        from src.utils.functions import verify_token
        token_data = verify_token(access_token)
        user = db.query(User).filter(User.email == token_data.email).first()
        if user and user.is_active:
            return user
    except:
        pass
    return None


@router.get("/search/", response_model=List[ProductResponse])
def search_products(
    q: str,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Search products by name, description, or SKU.
    - q: Search query string (required)
    - status: Optional status filter (only for admins): 'pending', 'approved', 'rejected'
    """
    if not q or not q.strip():
        return []
    return ProductService(db, current_user).search_products(q.strip(), status)


@router.get("/new-arrivals/", response_model=List[ProductResponse])
def get_new_arrivals(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Get the latest 2 products from each category.
    Only returns approved and active products.
    """
    return ProductService(db, current_user).get_new_arrivals()


@router.get("/sellers/{seller_id}/", response_model=List[ProductResponse])
def get_seller_products(seller_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return ProductService(db, current_user).get_seller_products(seller_id)


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    price: float = Form(...),
    discount_price: Optional[str] = Form(None),
    stock: int = Form(...),
    sku: Optional[str] = Form(None),
    category_id: int = Form(...),
    is_featured: bool = Form(False),
    images: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return await ProductService(db, current_user).create_product(name, description, price, discount_price, stock, sku, category_id, is_featured, images)


@router.get("/{product_id}/", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    return ProductService(db, None).get_product(product_id)


@router.patch("/{product_id}/update", response_model=ProductResponse)
async def update_product(
    product_id: int,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    discount_price: Optional[str] = Form(None),
    stock: Optional[int] = Form(None),
    sku: Optional[str] = Form(None),
    category_id: Optional[int] = Form(None),
    is_featured: Optional[bool] = Form(None),
    images: Optional[Union[List[UploadFile], List[str]]] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return await ProductService(db, current_user).update_product(product_id, name, description, price, discount_price, stock, sku, category_id, is_featured, images)


@router.delete("/{product_id}/delete", status_code=status.HTTP_200_OK)
def delete_product(product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return ProductService(db, current_user).delete_product(product_id)


@router.patch("/{product_id}/stock", response_model=ProductResponse)
async def add_product_stock(product_id: int, stock_data: AddStockRequest = Body(...), current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return ProductService(db, current_user).add_product_stock(product_id, stock_data)


@router.patch("/{product_id}/status", response_model=ProductResponse)
def update_product_status(product_id: int, status: str = Form(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return ProductService(db, current_user).update_product_status(product_id, status)


@router.get("/bulk-upload/template")
def download_bulk_upload_template():
    return ProductService(None, None).download_bulk_upload_template()


@router.post("/bulk-upload", response_model=BulkUploadResponse)
async def bulk_upload_products(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return await ProductService(db, current_user).bulk_upload_products(file)


# ---------------- LLM-Powered Endpoints ----------------

@router.post("/{product_id}/summarize-reviews", response_model=dict)
def summarize_reviews(product_id: int, db: Session = Depends(get_db)):
    """
    Summarize reviews for a specific product using Gemini AI.
    """
    from src.services.llm_service import LLMService
    from src.models.review import Review

    product = db.query(Product).filter(Product.id == product_id, Product.is_deleted == False).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    reviews = db.query(Review).filter(Review.product_id == product_id).all()

    llm_service = LLMService()
    summary = llm_service.summarize_reviews(product, reviews)

    return {"summary": summary}


@router.post("/{product_id}/qa", response_model=dict)
def qa_chatbot(product_id: int, qa_request: QARequest, db: Session = Depends(get_db)):
    """
    Answer questions about a product using Gemini AI, based on product details and reviews.
    """
    from src.services.llm_service import LLMService
    from src.models.review import Review

    product = db.query(Product).filter(Product.id == product_id, Product.is_deleted == False).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    reviews = db.query(Review).filter(Review.product_id == product_id).all()

    llm_service = LLMService()
    answer = llm_service.answer_question(product, reviews, qa_request.question)

    return {"answer": answer}
