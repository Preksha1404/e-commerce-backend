import stripe
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize Stripe
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
STRIPE_CURRENCY = os.getenv("STRIPE_CURRENCY", "usd").lower()

if not STRIPE_SECRET_KEY:
    raise ValueError("STRIPE_SECRET_KEY environment variable is not set")

stripe.api_key = STRIPE_SECRET_KEY

def get_stripe_client():
    """Get Stripe client instance"""
    return stripe

def get_stripe_publishable_key():
    """Get Stripe publishable key for frontend"""
    return STRIPE_PUBLISHABLE_KEY

def get_stripe_webhook_secret():
    """Get Stripe webhook secret for webhook verification"""
    if not STRIPE_WEBHOOK_SECRET:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("STRIPE_WEBHOOK_SECRET is not set. Webhook verification will fail.")
    return STRIPE_WEBHOOK_SECRET

def get_stripe_currency():
    """Get default Stripe currency"""
    return STRIPE_CURRENCY



