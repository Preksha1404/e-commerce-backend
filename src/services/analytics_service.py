from sqlalchemy.orm import Session
from sqlalchemy import func, extract, and_, or_, desc, asc
from datetime import datetime, timedelta, date
from typing import List, Dict, Any
from src.models.orders import Order, OrderItem, OrderStatus, PaymentStatus as OrderPaymentStatus
from src.models.users import User
from src.models.products import Product, Category
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
        total_revenue = self.db.query(func.sum(Order.total_amount)).scalar() or 0

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
                "totalRevenue": float(total_revenue),
                "currentMonthRevenue": float(current_revenue),
                "lastMonthRevenue": float(last_revenue)
            },
            "totalOrders": {
                "totalOrders": current_orders,
                "lastMonthOrders": last_orders
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
                     Order.payment_status == "paid")
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
            Category.name,
            func.sum(OrderItem.total_price)
        ).join(OrderItem.product).join(Product.category).join(OrderItem.order).filter(
            Order.created_at >= now - timedelta(days=365)
        ).group_by(Category.id, Category.name).all()

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
            Category.name,
            func.sum(OrderItem.quantity),
            func.sum(OrderItem.total_price)
        ).join(OrderItem).join(Product.category).join(OrderItem.order).filter(
            Order.created_at >= one_year_ago
        ).group_by(Product.id, Product.name, Category.name).order_by(
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
            Category.name,
            func.sum(OrderItem.quantity),
            func.sum(OrderItem.total_price)
        ).join(OrderItem).join(Product.category).join(OrderItem.order).filter(
            Order.created_at >= one_year_ago
        ).group_by(Product.id, Product.name, Category.name).order_by(
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

class SellerAnalyticsService:
    """Seller-scoped analytics service. Instantiate with db Session and call methods with seller_id."""

    def __init__(self, db: Session):
        self.db = db

    def overview(self, seller_id: int) -> Dict[str, Any]:
        today = date.today()
        yesterday = today - timedelta(days=1)
        current_month = today.month
        current_year = today.year
        last_month_date = (today.replace(day=1) - timedelta(days=1))
        last_month = last_month_date.month
        last_month_year = last_month_date.year

        # Today's revenue
        todays_revenue = float(
            self.db.query(func.coalesce(func.sum(OrderItem.total_price), 0))
            .join(Order, Order.id == OrderItem.order_id)
            .filter(OrderItem.seller_id == seller_id,
                    func.date(Order.created_at) == today,
                    Order.payment_status == OrderPaymentStatus.PAID)
            .scalar() or 0.0
        )

        # Yesterday revenue
        yesterday_revenue = float(
            self.db.query(func.coalesce(func.sum(OrderItem.total_price), 0))
            .join(Order, Order.id == OrderItem.order_id)
            .filter(OrderItem.seller_id == seller_id,
                    func.date(Order.created_at) == yesterday,
                    Order.payment_status == OrderPaymentStatus.PAID)
            .scalar() or 0.0
        )

        # Monthly revenue
        monthly_revenue = float(
            self.db.query(func.coalesce(func.sum(OrderItem.total_price), 0))
            .join(Order, Order.id == OrderItem.order_id)
            .filter(OrderItem.seller_id == seller_id,
                    extract("month", Order.created_at) == current_month,
                    extract("year", Order.created_at) == current_year,
                    Order.payment_status == OrderPaymentStatus.PAID)
            .scalar() or 0.0
        )

        # Last month revenue
        last_month_revenue = float(
            self.db.query(func.coalesce(func.sum(OrderItem.total_price), 0))
            .join(Order, Order.id == OrderItem.order_id)
            .filter(OrderItem.seller_id == seller_id,
                    extract("month", Order.created_at) == last_month,
                    extract("year", Order.created_at) == last_month_year,
                    Order.payment_status == OrderPaymentStatus.PAID)
            .scalar() or 0.0
        )

        # Total revenue
        total_revenue = float(
            self.db.query(func.coalesce(func.sum(OrderItem.total_price), 0))
            .join(Order, Order.id == OrderItem.order_id)
            .filter(OrderItem.seller_id == seller_id,
                    Order.payment_status == OrderPaymentStatus.PAID)
            .scalar() or 0.0
        )

        # Order counts
        # Delivered orders
        delivered_orders = (
            self.db.query(func.count(func.distinct(Order.id)))
            .join(OrderItem, OrderItem.order_id == Order.id)
            .filter(
                OrderItem.seller_id == seller_id,
                Order.payment_status == OrderPaymentStatus.PAID,
                Order.status == OrderStatus.DELIVERED
            )
            .scalar() or 0
        )

        # Pending orders
        pending_orders = (
            self.db.query(func.count(func.distinct(Order.id)))
            .join(OrderItem, OrderItem.order_id == Order.id)
            .filter(
                OrderItem.seller_id == seller_id,
                Order.payment_status == OrderPaymentStatus.PAID,
                Order.status == OrderStatus.PENDING
            )
            .scalar() or 0
        )

        # Total seller orders
        total_orders = (
            self.db.query(func.count(func.distinct(Order.id)))
            .join(OrderItem, OrderItem.order_id == Order.id)
            .filter(
                OrderItem.seller_id == seller_id,
                Order.payment_status == OrderPaymentStatus.PAID
            )
            .scalar() or 0
        )

        # Pending shipments (OrderItem-level)
        pending_shipments = (
            self.db.query(func.count(OrderItem.id))
            .join(Order, Order.id == OrderItem.order_id)
            .filter(
                OrderItem.seller_id == seller_id,
                Order.payment_status == OrderPaymentStatus.PAID,
                OrderItem.status == OrderStatus.PENDING
            )
            .scalar() or 0
        )

        # Products stats
        total_products = int(self.db.query(func.coalesce(func.count(Product.id), 0)).filter(Product.seller_id == seller_id, Product.is_deleted == False).scalar() or 0)
        active_products = int(self.db.query(func.coalesce(func.count(Product.id), 0)).filter(Product.seller_id == seller_id, Product.status == "approved", Product.is_deleted == False).scalar() or 0)
        pending_products = int(self.db.query(func.coalesce(func.count(Product.id), 0)).filter(Product.seller_id == seller_id, Product.status == "pending", Product.is_deleted == False).scalar() or 0)
        low_stock_items = int(self.db.query(func.coalesce(func.count(Product.id), 0)).filter(Product.seller_id == seller_id, Product.is_active == True, Product.stock < 10, Product.is_deleted == False).scalar() or 0)

        # Coupon usage: count of Orders that used a coupon issued by seller
        coupon_usage = int(
            self.db.query(func.coalesce(func.count(Order.id), 0))
            .join(Coupon, Order.coupon_id == Coupon.id)
            .filter(Coupon.user_id == seller_id)
            .scalar() or 0
        )

        return {
            "total_revenue": total_revenue,
            "monthly_revenue": monthly_revenue,
            "last_month_revenue": last_month_revenue,
            "todays_revenue": todays_revenue,
            "yesterday_revenue": yesterday_revenue,
            "total_orders": total_orders,
            "delivered_orders": delivered_orders,
            "pending_orders": pending_orders,
            "pending_shipments": pending_shipments,
            "total_products": total_products,
            "active_products": active_products,
            "pending_approval_products": pending_products,
            "low_stock_items": low_stock_items,
            "coupon_usage": coupon_usage
        }

    def revenue_trend(self, seller_id: int) -> Dict[str, List]:
        today = date.today()
        start_date = (today.replace(day=1) - timedelta(days=365))

        rows = self.db.query(
            extract('year', Order.created_at).label("year"),
            extract('month', Order.created_at).label("month"),
            func.coalesce(func.sum(OrderItem.total_price), 0).label("revenue")
        ).join(Order, Order.id == OrderItem.order_id).filter(
            OrderItem.seller_id == seller_id,
            Order.payment_status == OrderPaymentStatus.PAID,
            Order.created_at >= start_date
        ).group_by(
            extract('year', Order.created_at),
            extract('month', Order.created_at)
        ).all()

        revenue_map = {(int(year), int(month)): float(revenue) for year, month, revenue in rows}

        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        labels = []
        data = []

        # Build the last 12 months in chronological order
        months_list = []
        current = today.replace(day=1)
        for _ in range(11):
            # Move back 11 months
            if current.month == 1:
                current = current.replace(year=current.year - 1, month=12)
            else:
                current = current.replace(month=current.month - 1)

        for _ in range(12):
            year = current.year
            month = current.month
            months_list.append((year, month))
            if month == 12:
                current = current.replace(year=year + 1, month=1)
            else:
                current = current.replace(month=month + 1)

        for year, month in months_list:
            labels.append(f"{month_names[month - 1]} {year}")
            data.append(revenue_map.get((year, month), 0.0))

        return {"labels": labels, "data": data}

    def order_status_distribution(self, seller_id: int) -> Dict[str, List]:
        rows = self.db.query(Order.status, func.coalesce(func.count(Order.id), 0)).join(
            OrderItem, OrderItem.order_id == Order.id
        ).filter(OrderItem.seller_id == seller_id).group_by(Order.status).all()

        total_orders = sum(count for _, count in rows) or 1

        status_order = [OrderStatus.DELIVERED, OrderStatus.PENDING, OrderStatus.SHIPPED, OrderStatus.CANCELLED]
        status_name_map = {
            OrderStatus.DELIVERED: "Delivered",
            OrderStatus.PENDING: "Pending",
            OrderStatus.SHIPPED: "Shipped",
            OrderStatus.CANCELLED: "Cancelled"
        }

        status_count_map = {status: count for status, count in rows}

        labels = []
        percentages = []
        for status in status_order:
            count = status_count_map.get(status, 0)
            percent = round((count / total_orders) * 100, 2)
            labels.append(status_name_map.get(status, str(status)))
            percentages.append(percent)

        return {"labels": labels, "percentages": percentages}

    def top_selling_products(self, seller_id: int, limit: int = 10) -> Dict[str, List]:
        rows = (
            self.db.query(
                Product.id,
                Product.sku,
                func.coalesce(func.sum(OrderItem.quantity), 0).label("total_sold")
            )
            .join(OrderItem, OrderItem.product_id == Product.id)
            .filter(OrderItem.seller_id == seller_id, Product.is_deleted == False)
            .group_by(Product.id, Product.sku)
            .order_by(desc(func.sum(OrderItem.quantity)))
            .limit(limit)
            .all()
        )

        labels = [sku for _, sku, _ in rows]
        data = [int(total_sold) for _, _, total_sold in rows]
        return {"labels": labels, "units_sold": data}

    def coupon_usage(self, seller_id: int, limit: int = 5) -> Dict[str, List]:
        rows = (
            self.db.query(
                Coupon.id,
                Coupon.coupon_code,
                func.coalesce(func.count(Order.id), 0).label("usage")
            )
            .outerjoin(Order, Order.coupon_id == Coupon.id)
            .filter(Coupon.user_id == seller_id)
            .group_by(Coupon.id, Coupon.coupon_code)
            .order_by(desc(func.count(Order.id)))
            .limit(limit)
            .all()
        )

        labels = [coupon_code for _, coupon_code, _ in rows]
        data = [int(usage) for _, _, usage in rows]
        return {"labels": labels, "usage": data}

    def low_stock_items(self, seller_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        low_stock_products = self.db.query(
            Product.id, Product.name, Product.sku, Product.stock
        ).filter(Product.seller_id == seller_id, Product.stock < 10, Product.is_deleted == False).order_by(Product.stock.asc()).limit(limit).all()

        return [{"product_id": pid, "product_name": name, "sku": sku, "stock": int(stock)} for pid, name, sku, stock in low_stock_products]

    def product_performance(self, seller_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        results = (
            self.db.query(
                Product.id,
                Product.name,
                Product.sku,
                Product.stock,
                Product.status,
                func.coalesce(func.sum(OrderItem.quantity), 0).label("units_sold")
            )
            .outerjoin(OrderItem, Product.id == OrderItem.product_id)
            .filter(Product.seller_id == seller_id, Product.is_deleted == False)
            .group_by(Product.id)
            .order_by(desc(func.coalesce(func.sum(OrderItem.quantity), 0)))
            .limit(limit)
            .all()
        )

        return [
            {
                "product_id": r.id,
                "product_name": r.name,
                "sku": r.sku,
                "units_sold": int(r.units_sold),
                "stock": int(r.stock),
                "approval_status": r.status
            }
            for r in results
        ]