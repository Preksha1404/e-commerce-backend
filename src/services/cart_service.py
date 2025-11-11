from sqlalchemy.orm import Session
from typing import Optional, List

from src.models.orders import Cart, CartItem
from src.models.products import Product, ProductImage
from src.schemas.cart import CartOut, CartItemOut
from src.models.coupons import Coupon

def _compute_totals(db:Session, items: List[CartItemOut], coupon: Optional["Coupon"] = None) -> (float, float, float):
    subtotal = 0.0

    for item in items:
        # Fetch product from DB
        product = db.query(Product).filter(Product.id == item.product_id).first()
        
        if not product:
            continue

        price = product.price

        # Apply per-product discount (flat amount)
        if product.discount_price:
            price = max(price - product.discount_price, 0)

        # Update line total
        item.line_total = price * item.quantity
        subtotal += item.line_total

    discount = 0.0

    # Apply coupon discount if applicable
    if coupon:
        if not coupon.minimum_value or subtotal >= coupon.minimum_value:
            discount_type = getattr(coupon.discount_type, "value", coupon.discount_type)
            if discount_type == "flat":
                discount = coupon.discount_value or 0
            elif discount_type == "percentage":
                discount = subtotal * ((coupon.discount_value or 0) / 100)

    total = max(0.0, subtotal - discount)
    return float(subtotal), float(discount), float(total)

def _serialize_cart(db: Session, cart: Cart, coupon: Optional["Coupon"] = None) -> CartOut:
    item_models = (
        db.query(CartItem, Product)
        .join(Product, CartItem.product_id == Product.id)
        .filter(CartItem.cart_id == cart.id)
        .all()
    )

    items: List[CartItemOut] = []
    for ci, prod in item_models:
        # Try to fetch first image as image_url
        image_url = None
        if prod.images:
            # relationship Product.images may be configured; fallback to query if not loaded
            if isinstance(prod.images, list) and prod.images:
                image_url = prod.images[0].url
            else:
                img = (
                    db.query(ProductImage)
                    .filter(ProductImage.product_id == prod.id)
                    .order_by(ProductImage.position.asc())
                    .first()
                )
                image_url = img.url if img else None

        items.append(
            CartItemOut(
                product_id=prod.id,
                name=prod.name,
                unit_price=ci.unit_price,
                quantity=ci.quantity,
                line_total=ci.unit_price * ci.quantity,
                image_url=image_url,
            )
        )

    subtotal, discount, total = _compute_totals(db, items, coupon=coupon)
    return CartOut(items=items, subtotal=subtotal, discount=discount, total=total, coupon=coupon.coupon_code if coupon else None)


def get_or_create_cart(db: Session, user_id: int) -> Cart:
    cart = db.query(Cart).filter(Cart.user_id == user_id, Cart.is_active == True).first()
    if cart is None:
        cart = Cart(user_id=user_id, is_active=True)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


def get_cart(db: Session, user_id: int) -> CartOut:
    cart = get_or_create_cart(db, user_id)
    return _serialize_cart(db, cart)


def add_item(db: Session, user_id: int, product_id: int, quantity: int) -> CartOut:
    if quantity <= 0:
        raise ValueError("Quantity must be greater than 0")

    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise LookupError("Product not found")

    cart = get_or_create_cart(db, user_id)
    item = (
        db.query(CartItem)
        .filter(CartItem.cart_id == cart.id, CartItem.product_id == product_id)
        .first()
    )

    if item is None:
        # Cap by available stock if desired (soft check)
        item = CartItem(cart_id=cart.id, product_id=product_id, quantity=min(quantity, product.stock), unit_price=product.price)
        db.add(item)
    else:
        item.quantity = max(1, item.quantity + quantity)

    db.commit()
    return _serialize_cart(db, cart)


def update_item(db: Session, user_id: int, product_id: int, quantity: int) -> CartOut:
    cart = get_or_create_cart(db, user_id)
    item = (
        db.query(CartItem)
        .filter(CartItem.cart_id == cart.id, CartItem.product_id == product_id)
        .first()
    )
    if item is None:
        raise LookupError("Item not in cart")

    if quantity <= 0:
        db.delete(item)
    else:
        item.quantity = quantity
    db.commit()
    return _serialize_cart(db, cart)


def remove_item(db: Session, user_id: int, product_id: int) -> CartOut:
    cart = get_or_create_cart(db, user_id)
    item = (
        db.query(CartItem)
        .filter(CartItem.cart_id == cart.id, CartItem.product_id == product_id)
        .first()
    )
    if item:
        db.delete(item)
        db.commit()
    return _serialize_cart(db, cart)


def clear_cart(db: Session, user_id: int) -> CartOut:
    cart = get_or_create_cart(db, user_id)
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
    db.commit()
    return _serialize_cart(db, cart)


def apply_coupon(db: Session, user_id: int, code: str) -> CartOut:
    # Placeholder: accept any non-empty code as demo; integrate real coupon validation later
    if not code:
        raise ValueError("Coupon code required")
    cart = get_or_create_cart(db, user_id)
    return _serialize_cart(db, cart, coupon=code)


