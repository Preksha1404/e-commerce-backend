import random
import string
from src.models.coupons import DiscountType

def generate_coupon_code(coupon_name: str, length: int = 6) -> str:
    """
    Generate a unique coupon code from coupon_name + random suffix
    Example: "SUMMER SALE" -> "SUMMERSALE-AB12CD"
    """
    # Remove spaces and uppercase
    base = coupon_name.replace(" ", "").upper()
    
    # Random alphanumeric suffix
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
    return f"{base}-{suffix}"


def calculate_discount(cart_total: float, discount_type: DiscountType, discount_value: float) -> float:
    """
    Calculate discount amount based on discount type.
    - flat: returns discount_value
    - percentage: returns cart_total * discount_value / 100
    """
    if discount_type == DiscountType.flat:
        return min(discount_value, cart_total)  # discount can't exceed cart total
    elif discount_type == DiscountType.percentage:
        return cart_total * (discount_value / 100)
    else:
        return 0.0