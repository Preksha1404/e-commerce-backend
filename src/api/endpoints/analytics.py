from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.services.analytics_service import AnalyticsService
from src.utils.auth import get_current_active_user
from src.models.users import User

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/kpis")
def get_kpi_cards(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all KPI card data for admin dashboard"""
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    service = AnalyticsService(db)
    return {"kpis": service.get_kpi_cards()}

@router.get("/charts")
def get_charts_data(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all chart data for admin dashboard"""
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    service = AnalyticsService(db)
    return {"charts": service.get_charts_data()}

@router.get("/products")
def get_products_data(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get top selling and worst performing products"""
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    service = AnalyticsService(db)
    return {"products": service.get_products_data()}

@router.get("/recent-orders")
def get_recent_orders(
    limit: int = 10,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get recent orders for admin dashboard"""
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    service = AnalyticsService(db)
    return {"recentOrders": service.get_recent_orders(limit)}
