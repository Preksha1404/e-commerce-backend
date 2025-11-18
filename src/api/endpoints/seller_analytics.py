# GET /seller/analytics/overview --> Total Revenue, Monthly Revenue, Today's Revenue, Total orders (Delivered, Pending), Pending Shipments, Active products, Approval Pending Products, Low stock Items (Stock < 10), Coupon Usage (Total Discount)

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, and_
from datetime import datetime, date, timedelta
from src.core.database import get_db
from src.models.orders import Order, OrderItem, OrderStatus, PaymentStatus, Cart
from src.models.users import User
from src.models.products import Product
from src.models.coupons import Coupon
from src.utils.auth import get_current_active_user

router = APIRouter(prefix="/seller/analytics", tags=["Seller Analytics"])

@router.get("/overview")
def seller_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):

    # Only sellers can view analytics
    if current_user.role != "seller":
        raise HTTPException(status_code=403, detail="Only sellers can view analytics")

    seller_id = current_user.id
    today = date.today()
    current_month = today.month
    current_year = today.year

    # TODAY'S REVENUE
    todays_revenue = db.query(
        func.coalesce(func.sum(OrderItem.total_price), 0)
    ).join(Order).filter(
        OrderItem.seller_id == seller_id,
        func.date(Order.created_at) == today,
        Order.payment_status == PaymentStatus.PAID
    ).scalar()

    # MONTHLY REVENUE
    monthly_revenue = db.query(
        func.coalesce(func.sum(OrderItem.total_price), 0)
    ).join(Order).filter(
        OrderItem.seller_id == seller_id,
        extract("month", Order.created_at) == current_month,
        extract("year", Order.created_at) == current_year,
        Order.payment_status == PaymentStatus.PAID
    ).scalar()

    # TOTAL REVENUE
    total_revenue = db.query(
        func.coalesce(func.sum(OrderItem.total_price), 0)
    ).join(Order).filter(
        OrderItem.seller_id == seller_id,
        Order.payment_status == PaymentStatus.PAID
    ).scalar()

    # ORDER COUNTS
    delivered_orders = db.query(Order).join(OrderItem).filter(
        OrderItem.seller_id == seller_id,
        Order.status == OrderStatus.DELIVERED
    ).count()

    pending_orders = db.query(Order).join(OrderItem).filter(
        OrderItem.seller_id == seller_id,
        Order.status == OrderStatus.PENDING
    ).count()

    total_orders = db.query(Order).join(OrderItem).filter(
        OrderItem.seller_id == seller_id
    ).count()

    # PENDING SHIPMENTS
    pending_shipments = db.query(OrderItem).filter(
        OrderItem.seller_id == seller_id,
        OrderItem.status.in_([OrderStatus.PENDING, OrderStatus.SHIPPED])
    ).count()

    # PRODUCT COUNTS
    total_products = db.query(Product).filter(
        Product.seller_id == seller_id
    ).count()

    active_products = db.query(Product).filter(
        Product.seller_id == seller_id,
        Product.status == "approved"
    ).count()

    pending_products = db.query(Product).filter(
        Product.seller_id == seller_id,
        Product.status == "pending"
    ).count()

    low_stock_items = db.query(Product).filter(
        Product.seller_id == seller_id,
        Product.stock < 10
    ).count()

    # COUPON USAGE
    coupon_usage = db.query(Order).join(Coupon).filter(
        Coupon.user_id == seller_id,
        Order.coupon_id == Coupon.id
    ).count()

    return {
        "total_revenue": float(total_revenue),
        "monthly_revenue": float(monthly_revenue),
        "todays_revenue": float(todays_revenue),

        "total_orders": total_orders,
        "delivered_orders": delivered_orders,
        "pending_orders": pending_orders,

        "pending_shipments": pending_shipments,

        "total_products": total_products,
        "active_products": active_products,
        "pending_approval_products": pending_products,

        "low_stock_items": low_stock_items,

        "coupon_usage": coupon_usage,
    }


@router.get("/revenue-trend")
def seller_revenue_trend(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
    ):
        # Ensure only sellers can access
        if current_user.role != "seller":
            raise HTTPException(status_code=403, detail="Only sellers can view analytics")

        seller_id = current_user.id
        today = date.today()
        twelve_months_ago = today.replace(day=1) - timedelta(days=365)

        # Query revenue grouped by month
        rows = db.query(
            extract('year', Order.created_at).label("year"),
            extract('month', Order.created_at).label("month"),
            func.sum(OrderItem.total_price).label("revenue")
        ).join(Order).filter(
            OrderItem.seller_id == seller_id,
            Order.payment_status == PaymentStatus.PAID,
            Order.created_at >= twelve_months_ago
        ).group_by(
            extract('year', Order.created_at),
            extract('month', Order.created_at)
        ).order_by(
            extract('year', Order.created_at),
            extract('month', Order.created_at)
        ).all()

        # Convert results to chart format
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        labels = []
        data = []

        for year, month, revenue in rows:
            labels.append(month_names[int(month) - 1])
            data.append(float(revenue))

        return {
            "labels": labels,
            "data": data
        }

@router.get("/order-status-distribution")
def order_status_distribution(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Only sellers allowed
    if current_user.role != "seller":
        raise HTTPException(status_code=403, detail="Only sellers can view analytics")

    seller_id = current_user.id

    # Count orders grouped by status
    rows = db.query(
        Order.status,
        func.count(Order.id)
    ).join(OrderItem).filter(
        OrderItem.seller_id == seller_id
    ).group_by(
        Order.status
    ).all()

    # Total orders
    total_orders = sum([count for status, count in rows]) or 1  # prevent divide-by-zero

    # Prepare chart response
    labels = []
    percentages = []

    # Keep fixed order (delivered, pending, shipped, cancelled)
    status_order = [
        OrderStatus.DELIVERED,
        OrderStatus.PENDING,
        OrderStatus.SHIPPED,
        OrderStatus.CANCELLED
    ]

    status_name_map = {
        OrderStatus.DELIVERED: "Delivered",
        OrderStatus.PENDING: "Pending",
        OrderStatus.SHIPPED: "Shipped",
        OrderStatus.CANCELLED: "Cancelled"
    }

    # Convert DB result to dict for fast lookup
    status_count_map = {status: count for status, count in rows}

    for status in status_order:
        count = status_count_map.get(status, 0)
        percent = round((count / total_orders) * 100, 2)
        labels.append(status_name_map[status])
        percentages.append(percent)

    return {
        "labels": labels,
        "percentages": percentages
    }

@router.get("/top-selling-products")
def top_selling_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Only sellers allowed
    if current_user.role != "seller":
        raise HTTPException(status_code=403, detail="Only sellers can view analytics")

    seller_id = current_user.id

    # Query top selling products for this seller
    rows = (
        db.query(
            Product.id,
            Product.sku,
            func.sum(OrderItem.quantity).label("total_sold")
        )
        .join(OrderItem, OrderItem.product_id == Product.id)
        .filter(OrderItem.seller_id == seller_id)
        .group_by(Product.id, Product.sku)
        .order_by(func.sum(OrderItem.quantity).desc())
        .all()
    )

    # Prepare response
    labels = []
    data = []

    for product_id, sku, total_sold in rows:
        labels.append(sku)
        data.append(int(total_sold))

    return {
        "labels": labels,
        "units_sold": data
    }

@router.get("/coupon-usage")
def coupon_usage(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role != "seller":
        raise HTTPException(status_code=403, detail="Only sellers can view analytics")

    seller_id = current_user.id

    rows = (
        db.query(
            Coupon.id,
            Coupon.coupon_code,
            func.count(Order.id).label("usage")
        )
        .outerjoin(Order, Order.coupon_id == Coupon.id)
        .filter(Coupon.user_id == seller_id)
        .group_by(Coupon.id, Coupon.coupon_code)
        .order_by(func.count(Order.id).desc())
        .limit(5)
        .all()
    )

    labels = [coupon_code for _, coupon_code, _ in rows]
    data   = [usage for _, _, usage in rows]

    return {
        "labels": labels,
        "usage": data
    }

@router.get("/low-stock-items")
def get_low_stock_items(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role != "seller":
        raise HTTPException(status_code=403, detail="Only sellers can view analytics")

    seller_id = current_user.id

    low_stock_products = db.query(
        Product.id,
        Product.name,
        Product.sku,
        Product.stock
    ).filter(
        Product.seller_id == seller_id,
        Product.stock < 10
    ).all()

    return [
        {
            "product_id": prod.id,
            "product_name": prod.name,
            "sku": prod.sku,
            "stock": prod.stock,
        }
        for prod in low_stock_products
    ]

@router.get("/product-performance")
def product_performance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role != "seller":
        raise HTTPException(status_code=403, detail="Only sellers can view analytics")

    seller_id = current_user.id

    results = (
        db.query(
            Product.id,
            Product.name,
            Product.sku,
            Product.stock,
            Product.status,
            func.COALESCE(func.sum(OrderItem.quantity), 0).label("units_sold")
        )
        .outerjoin(OrderItem, Product.id == OrderItem.product_id)
        .filter(Product.seller_id == seller_id)
        .group_by(Product.id)
        .all()
    )

    return [
        {
            "product_id": r.id,
            "product_name": r.name,
            "sku": r.sku,
            "units_sold": r.units_sold,
            "stock": r.stock,
            "approval_status": r.status
        }
        for r in results
    ]