import os
from datetime import datetime

FRONTEND_URL = os.getenv("FRONTEND_URL")
RESET_TOKEN_EXPIRE_MINUTES = os.getenv("RESET_TOKEN_EXPIRE_MINUTES")

def password_reset_template(email: str, token: str):
    reset_link = f"{FRONTEND_URL}/reset-password?token={token}"
    subject = "Password Reset"

    html_content = f"""
    <html>
      <body style="margin:0; padding:0; background-color:#0d0d0d; font-family:'Helvetica Neue', Arial, sans-serif; color:#f0f0f0;">
        <div style="max-width:600px; margin:0 auto; background-color:#1a1a1a; border-radius:10px; overflow:hidden;">
          <div style="background-color:#000000; padding:20px; text-align:center;">
            <img src="https://i.postimg.cc/tCqfC2rQ/cartify-logo.png" alt="Cartify Logo" width="120" />
          </div>
          <div style="padding:40px 30px; text-align:center;">
            <h2 style="color:#ffffff;">Password Reset Request</h2>
            <p style="color:#cccccc;">Click the button below to reset your password:</p>
            <a href="{reset_link}"
              style="background:#ff6600;color:white;padding:12px 30px;border-radius:6px;text-decoration:none;display:inline-block;margin-top:10px;">
              Reset Password
            </a>
            <p style="color:#aaaaaa;margin-top:20px;">This link expires in {RESET_TOKEN_EXPIRE_MINUTES} minutes.</p>
          </div>
          <div style="background:#000000; padding:20px; text-align:center; color:#888888; font-size:13px;">
            <p>© {datetime.now().year} Cartify. All rights reserved.</p>
          </div>
        </div>
      </body>
    </html>
    """
    return subject, html_content


def customer_welcome_template(full_name: str):
    subject = "Welcome to Cartify – Discover Your Perfect Find!"
    html_content = f"""
    <html>
      <body style="margin:0; padding:0; background-color:#0d0d0d; font-family:'Helvetica Neue', Arial, sans-serif; color:#f0f0f0;">
        <div style="max-width:600px; margin:0 auto; background-color:#1a1a1a; border-radius:10px; overflow:hidden;">
          <div style="background-color:#000000; padding:20px; text-align:center;">
            <img src="https://i.postimg.cc/tCqfC2rQ/cartify-logo.png" alt="Cartify Logo" width="120" />
          </div>
          <div style="padding:40px 30px 20px 30px; text-align:center;">
            <h1 style="color:#ffffff; font-size:28px;">Welcome to <span style="color:#ff6600;">Cartify!</span></h1>
            <p style="color:#cccccc; font-size:16px;">Hi <strong>{full_name}</strong>, we’re thrilled to have you with us!</p>
          </div>
          <div style="padding:0 30px 20px 30px;">
            <ul style="color:#dddddd; line-height:1.8;">
              <li>🛍️ Explore curated collections of trending products.</li>
              <li>💸 Enjoy exclusive discounts and limited-time offers.</li>
              <li>⚡ Experience fast delivery and secure checkout.</li>
            </ul>
          </div>
          <div style="text-align:center; padding:30px;">
            <a href="{FRONTEND_URL}" style="background-color:#ff6600;color:#ffffff;padding:12px 30px;border-radius:6px;text-decoration:none;font-size:16px;font-weight:bold;">
              Shop Now
            </a>
          </div>
          <div style="background-color:#000000; padding:20px; text-align:center; font-size:13px; color:#888888;">
            <p>Need help? <a href="{FRONTEND_URL}/contact" style="color:#ff6600; text-decoration:none;">Contact our support team</a></p>
            <p style="margin-top:10px;">© {datetime.now().year} Cartify. All rights reserved.</p>
          </div>
        </div>
      </body>
    </html>
    """
    return subject, html_content


def seller_welcome_template(full_name: str):
    subject = "Welcome to Cartify – Seller Account Under Verification"
    html_content = f"""
    <html>
      <body style="margin:0; padding:0; background-color:#0d0d0d; font-family:'Helvetica Neue', Arial, sans-serif; color:#f0f0f0;">
        <div style="max-width:600px; margin:0 auto; background-color:#1a1a1a; border-radius:10px; overflow:hidden;">
          <div style="background-color:#000000; padding:20px; text-align:center;">
            <img src="https://i.postimg.cc/tCqfC2rQ/cartify-logo.png" alt="Cartify Logo" width="120" />
          </div>
          <div style="padding:40px 30px 20px 30px; text-align:center;">
            <h1 style="color:#ffffff; font-size:28px;">Welcome to <span style="color:#ff6600;">Cartify Sellers!</span></h1>
            <p style="color:#cccccc; font-size:16px;">Hi <strong>{full_name}</strong>, your seller account is created and currently under verification.</p>
          </div>
          <div style="padding:0 30px 20px 30px;">
            <ul style="color:#dddddd; line-height:1.8;">
              <li>🔍 Our team will verify your business details.</li>
              <li>✅ You’ll get a confirmation email once approved.</li>
              <li>⏳ If not verified within 15 days, please contact us.</li>
            </ul>
          </div>
          <div style="text-align:center; padding:30px;">
            <a href="{FRONTEND_URL}/seller/login" style="background-color:#ff6600;color:#ffffff;padding:12px 30px;border-radius:6px;text-decoration:none;font-size:16px;font-weight:bold;">
              Go to Seller Portal
            </a>
          </div>
          <div style="background-color:#000000; padding:20px; text-align:center; font-size:13px; color:#888888;">
            <p>Need help? <a href="{FRONTEND_URL}/contact" style="color:#ff6600; text-decoration:none;">Contact our support team</a></p>
            <p style="margin-top:10px;">© {datetime.now().year} Cartify. All rights reserved.</p>
          </div>
        </div>
      </body>
    </html>
    """
    return subject, html_content


def seller_verification_template(full_name: str, store_name: str, store_address: str, store_description: str):
    subject = "Your Seller Account is Under Verification"
    html_content = f"""
    <html>
      <body style="margin:0; padding:0; background-color:#0d0d0d; font-family:'Helvetica Neue', Arial, sans-serif; color:#f0f0f0;">
        <div style="max-width:600px; margin:0 auto; background-color:#1a1a1a; border-radius:10px; overflow:hidden;">
          <div style="background-color:#000000; padding:20px; text-align:center;">
            <img src="https://i.postimg.cc/tCqfC2rQ/cartify-logo.png" alt="Cartify Logo" width="120" />
          </div>
          <div style="padding:40px 30px;">
            <h2 style="color:#ffffff;">Account Verification in Progress</h2>
            <p>Dear <strong>{full_name}</strong>, your store details were recently updated and are now under verification.</p>
            <ul style="color:#dddddd;">
              <li><strong>Store Name:</strong> {store_name}</li>
              <li><strong>Address:</strong> {store_address}</li>
              <li><strong>Description:</strong> {store_description or "N/A"}</li>
            </ul>
            <p style="margin-top:10px;">We’ll notify you once verification is complete.</p>
          </div>
          <div style="background-color:#000000; padding:20px; text-align:center; color:#888888; font-size:13px;">
            <p>© {datetime.now().year} Cartify. All rights reserved.</p>
          </div>
        </div>
      </body>
    </html>
    """
    return subject, html_content