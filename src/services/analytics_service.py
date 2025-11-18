from sqlalchemy.orm import Session
from sqlalchemy import func, extract, and_, or_, desc, asc
from datetime import datetime, timedelta
from typing import List, Dict, Any
from src.models.orders import Order, OrderItem, OrderStatus
from src.models.users import User
from src.models.products import Product
from src.models.coupons import Coupon
from src.models.payments import Payment, PaymentStatus


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def get_kpi_cards(self) -> Dict[str, Any]:
        """Get all KPI card data in one response"""
        now = datetime.now()
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
        last_month_end = current_month_start - timedelta(seconds=1)

        # Total Revenue
        current_revenue = self.db.query(func.sum(Order.total_amount)).filter(
            Order.created_at >= current_month_start
        ).scalar() or 0

        last_revenue = self.db.query(func.sum(Order.total_amount)).filter(
            and_(Order.created_at >= last_month_start, Order.created_at <= last_month_end)
        ).scalar() or 0

        revenue_trend = ((current_revenue - last_revenue) / last_revenue * 100) if last_revenue > 0 else 0

        # Total Orders
        current_orders = self.db.query(func.count(Order.id)).filter(
            Order.created_at >= current_month_start
        ).scalar()

        last_orders = self.db.query(func.count(Order.id)).filter(
            and_(Order.created_at >= last_month_start, Order.created_at <= last_month_end)
        ).scalar()

        orders_trend = ((current_orders - last_orders) / last_orders * 100) if last_orders > 0 else 0

        # Active Customers
        total_customers = self.db.query(func.count(User.id)).filter(User.role == "customer").scalar()
        thirty_days_ago = now - timedelta(days=30)
        new_customers = self.db.query(func.count(User.id)).filter(
            and_(User.role == "customer", User.created_at >= thirty_days_ago)
        ).scalar()

        # Active Sellers
        approved_sellers = self.db.query(func.count(User.id)).filter(
            User.role == "seller"
        ).scalar()
        pending_sellers = 0  # Simplified - no pending status in current model

        # Total Products
        approved_products = self.db.query(func.count(Product.id)).filter(Product.is_active == True).scalar()
        pending_products = self.db.query(func.count(Product.id)).filter(Product.is_active == False).scalar()

        # Failed Payments
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        failed_payments_today = self.db.query(func.count(Payment.id)).filter(
            and_(Payment.status == PaymentStatus.FAILED, Payment.created_at >= today_start)
        ).scalar()

        total_payments_today = self.db.query(func.count(Payment.id)).filter(
            Payment.created_at >= today_start
        ).scalar()

        failed_rate = (failed_payments_today / total_payments_today * 100) if total_payments_today > 0 else 0

        # Coupons Used
        coupon_usages = self.db.query(func.sum(Coupon.used_count)).scalar() or 0

        # Calculate total discount given (simplified - from order totals vs item subtotals)
        total_discount = 0
        orders_with_coupons = self.db.query(Order).filter(Order.coupon_id.isnot(None)).all()
        for order in orders_with_coupons:
            items_total = sum(item.total_price for item in order.items)
            total_discount += (items_total - order.total_amount)

        return {
            "totalRevenue": {
                "value": float(current_revenue),
                "trend": float(revenue_trend)
            },
            "totalOrders": {
                "value": current_orders,
                "trend": float(orders_trend)
            },
            "activeCustomers": {
                "total": total_customers,
                "new30Days": new_customers
            },
            "activeSellers": {
                "approved": approved_sellers,
                "pending": pending_sellers
            },
            "totalProducts": {
                "approved": approved_products,
                "pending": pending_products
            },
            "failedPayments": {
                "failedToday": failed_payments_today,
                "failureRate": float(failed_rate)
            },
            "couponsUsed": {
                "usages": coupon_usages,
                "totalDiscount": float(total_discount)
            }
        }

    def get_charts_data(self) -> Dict[str, Any]:
        """Get all chart data in one response"""
        # Revenue Trend (Last 12 months)
        revenue_trend = []
        now = datetime.now()
        for i in range(12):
            month_start = (now - timedelta(days=30*i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)

            revenue = self.db.query(func.sum(Order.total_amount)).filter(
                and_(Order.created_at >= month_start, Order.created_at <= month_end)
            ).scalar() or 0

            revenue_trend.append({
                "month": month_start.strftime("%b %Y"),
                "revenue": float(revenue)
            })

        revenue_trend.reverse()  # Oldest first

        # Order Overview (Last 12 months)
        order_overview = []
        for i in range(12):
            month_start = (now - timedelta(days=30*i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)

            success = self.db.query(func.count(Order.id)).filter(
                and_(Order.created_at >= month_start, Order.created_at <= month_end,
                     Order.payment_status == PaymentStatus.SUCCEEDED)
            ).scalar()

            cancelled = self.db.query(func.count(Order.id)).filter(
                and_(Order.created_at >= month_start, Order.created_at <= month_end,
                     Order.status == OrderStatus.CANCELLED)
            ).scalar()

            failed = self.db.query(func.count(Order.id)).filter(
                and_(Order.created_at >= month_start, Order.created_at <= month_end,
                     Order.payment_status == PaymentStatus.FAILED)
            ).scalar()

            # Average Order Value
            total_orders = success + cancelled + failed
            total_revenue = self.db.query(func.sum(Order.total_amount)).filter(
                and_(Order.created_at >= month_start, Order.created_at <= month_end)
            ).scalar() or 0
            aov = total_revenue / total_orders if total_orders > 0 else 0

            order_overview.append({
                "month": month_start.strftime("%b %Y"),
                "success": success,
                "cancelled": cancelled,
                "failed": failed,
                "aov": float(aov)
            })

        order_overview.reverse()

        # Category Revenue Breakdown
        category_revenue = self.db.query(
            Product.category,
            func.sum(OrderItem.total_price)
        ).join(OrderItem.product).join(OrderItem.order).filter(
            Order.created_at >= now - timedelta(days=365)
        ).group_by(Product.category).all()

        category_data = [{"category": cat, "revenue": float(rev)} for cat, rev in category_revenue]

        # Top Performing Sellers
        top_sellers = self.db.query(
            User.full_name,
            func.sum(OrderItem.total_price),
            func.count(OrderItem.id)
        ).join(OrderItem.seller).join(OrderItem.order).filter(
            Order.created_at >= now - timedelta(days=365)
        ).group_by(User.id, User.full_name).order_by(desc(func.sum(OrderItem.total_price))).limit(10).all()

        sellers_data = [{
            "sellerName": name,
            "revenue": float(rev),
            "orders": orders
        } for name, rev, orders in top_sellers]

        return {
            "revenueTrend": revenue_trend,
            "orderOverview": order_overview,
            "categoryRevenue": category_data,
            "topSellers": sellers_data
        }

    def get_products_data(self) -> Dict[str, Any]:
        """Get top selling and worst performing products"""
        now = datetime.now()
        one_year_ago = now - timedelta(days=365)

        # Top Selling Products
        top_products = self.db.query(
            Product.id,
            Product.name,
            Product.category,
            func.sum(OrderItem.quantity),
            func.sum(OrderItem.total_price)
        ).join(OrderItem.order).filter(
            Order.created_at >= one_year_ago
        ).group_by(Product.id, Product.name, Product.category).order_by(
            desc(func.sum(OrderItem.quantity))
        ).limit(10).all()

        top_selling = [{
            "id": pid,
            "name": name,
            "category": category,
            "sold": int(sold),
            "revenue": float(revenue)
        } for pid, name, category, sold, revenue in top_products]

        # Worst Performing Products (least sold in last year)
        worst_products = self.db.query(
            Product.id,
            Product.name,
            Product.category,
            func.sum(OrderItem.quantity),
            func.sum(OrderItem.total_price)
        ).join(OrderItem.order).filter(
            Order.created_at >= one_year_ago
        ).group_by(Product.id, Product.name, Product.category).order_by(
            asc(func.sum(OrderItem.quantity))
        ).limit(10).all()

        worst_performing = [{
            "id": pid,
            "name": name,
            "category": category,
            "sold": int(sold),
            "revenue": float(revenue)
        } for pid, name, category, sold, revenue in worst_products]

        return {
            "topSelling": top_selling,
            "worstPerforming": worst_performing
        }

    def get_recent_orders(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent orders"""
        recent_orders = self.db.query(
            Order.id,
            User.full_name.label("customer_name"),
            Order.total_amount,
            Order.status,
            Order.created_at
        ).join(Order.user).order_by(desc(Order.created_at)).limit(limit).all()

        return [{
            "orderId": oid,
            "customerName": customer,
            "amount": float(amount),
            "status": status.value,
            "createdDate": created_at.isoformat()
        } for oid, customer, amount, status, created_at in recent_orders]
