import pytest
from src.utils.email_templates import coupon_notification_template
from src.models.coupons import DiscountType


def test_coupon_template_with_string_discount_type():
    subject, html = coupon_notification_template(
        user_name="alice",
        coupon_code="PROMO50",
        coupon_name="Half Off",
        discount_value=50,
        discount_type="percent",
        expiry_date="2026-12-31",
        coupon_description="Great savings"
    )

    assert "PROMO50" in subject or "PROMO50" in html
    assert "% OFF" in html or "50%" in html


def test_coupon_template_with_enum_discount_type():
    # pass an Enum value (DiscountType.flat) to ensure template handles enums
    subject, html = coupon_notification_template(
        user_name="bob",
        coupon_code="FLAT100",
        coupon_name="Flat Discount",
        discount_value=100,
        discount_type=DiscountType.flat,
        expiry_date="2026-12-31",
        coupon_description="Flat rupee discount"
    )

    assert "FLAT100" in subject or "FLAT100" in html
    # For flat discounts we expect a rupee symbol or the word OFF
    assert ("₹" in html) or ("OFF" in html)
