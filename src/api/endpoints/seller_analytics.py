# GET /seller/analytics/overview --> Total Revenue, Monthly Revenue, Today's Revenue, Total orders (Delivered, Pending), Pending Shipments, Active products, Approval Pending Products, Low stock Items (Stock < 10), Coupon Usage (Total Discount)

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any, Dict, List
from src.core.database import get_db
from src.utils.auth import get_current_active_user
from src.models.users import User
from src.services.analytics_service import SellerAnalyticsService

router = APIRouter(prefix="/seller/analytics", tags=["Seller Analytics"])

def _ensure_seller(user: User):
    if user.role != "seller":
        raise HTTPException(status_code=403, detail="Only sellers can view analytics")

@router.get("/overview")
def seller_overview(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)) -> Dict[str, Any]:
    _ensure_seller(current_user)
    return SellerAnalyticsService(db).overview(current_user.id)

@router.get("/revenue-trend")
def seller_revenue_trend(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)) -> Dict[str, List]:
    _ensure_seller(current_user)
    return SellerAnalyticsService(db).revenue_trend(current_user.id)

@router.get("/order-status-distribution")
def seller_order_status_distribution(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)) -> Dict[str, List]:
    _ensure_seller(current_user)
    return SellerAnalyticsService(db).order_status_distribution(current_user.id)

@router.get("/top-selling-products")
def seller_top_selling_products(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    _ensure_seller(current_user)
    return SellerAnalyticsService(db).top_selling_products(current_user.id)

@router.get("/coupon-usage")
def seller_coupon_usage(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    _ensure_seller(current_user)
    return SellerAnalyticsService(db).coupon_usage(current_user.id)

@router.get("/low-stock-items")
def seller_low_stock_items(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    _ensure_seller(current_user)
    return SellerAnalyticsService(db).low_stock_items(current_user.id)

@router.get("/product-performance")
def seller_product_performance(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    _ensure_seller(current_user)
    return SellerAnalyticsService(db).product_performance(current_user.id)