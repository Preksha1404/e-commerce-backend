import os
from datetime import datetime

FRONTEND_URL = os.getenv("FRONTEND_URL")
RESET_TOKEN_EXPIRE_MINUTES = os.getenv("RESET_TOKEN_EXPIRE_MINUTES")

def password_reset_template(email: str, token: str):
    reset_link = f"{FRONTEND_URL}/reset-password?token={token}"
    subject = "Password Reset"

    html_content = f"""
    <html>
      <body style="margin:0; padding:0; background-color:#EFEBE9; font-family:'Helvetica Neue', Arial, sans-serif; color:#7B5C52;">
        <div style="max-width:600px; margin:0 auto; background-color:white; border-radius:10px; overflow:hidden; border:1px solid #e0d6d3;">
          <div style="background-color:#7B5C52; padding:20px; text-align:center;">
            <img src="https://e-commerce-backend-4-p9d1.onrender.com/static/cartify_logo.png" alt="Cartify Logo" width="120" />
          </div>
          <div style="padding:40px 30px; text-align:center;">
            <h2 style="color:#7B5C52;">Password Reset Request</h2>
            <p>Click the button below to reset your password:</p>
            <a href="{reset_link}"
              style="background:#7B5C52; color:white; padding:12px 30px; border-radius:6px; text-decoration:none; display:inline-block; margin-top:10px;">
              Reset Password
            </a>
            <p style="margin-top:20px;">This link expires in {RESET_TOKEN_EXPIRE_MINUTES} minutes.</p>
          </div>
          <div style="background:#EFEBE9; padding:20px; text-align:center; color:#7B5C52; font-size:13px;">
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
      <body style="margin:0; padding:0; background-color:#EFEBE9; font-family:'Helvetica Neue', Arial, sans-serif; color:#7B5C52;">
        <div style="max-width:600px; margin:0 auto; background-color:white; border-radius:10px; overflow:hidden; border:1px solid #e0d6d3;">
          <div style="background-color:#7B5C52; padding:20px; text-align:center;">
            <img src="https://e-commerce-backend-4-p9d1.onrender.com/static/cartify_logo.png" alt="Cartify Logo" width="120" />
          </div>

          <div style="padding:40px 30px 20px 30px; text-align:center;">
            <h1 style="color:#7B5C52; font-size:28px;">Welcome to <strong>Cartify!</strong></h1>
            <p style="font-size:16px;">Hi <strong>{full_name}</strong>, we’re thrilled to have you with us!</p>
          </div>

          <div style="padding:0 30px 20px 30px;">
            <ul style="line-height:1.8; color:#7B5C52;">
              <li>🛍️ Explore curated collections of trending products.</li>
              <li>💸 Enjoy exclusive discounts and offers.</li>
              <li>⚡ Experience fast delivery and secure checkout.</li>
            </ul>
          </div>

          <div style="text-align:center; padding:30px;">
            <a href="{FRONTEND_URL}"
              style="background-color:#7B5C52; color:white; padding:12px 30px; border-radius:6px; text-decoration:none; font-size:16px; font-weight:bold;">
              Shop Now
            </a>
          </div>

          <div style="background-color:#EFEBE9; padding:20px; text-align:center; font-size:13px; color:#7B5C52;">
            <p>Need help? <a href="{FRONTEND_URL}/contact" style="color:#7B5C52; text-decoration:underline;">Contact our support team</a></p>
            <p>© {datetime.now().year} Cartify. All rights reserved.</p>
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
      <body style="margin:0; padding:0; background-color:#EFEBE9; font-family:'Helvetica Neue', Arial, sans-serif; color:#7B5C52;">
        <div style="max-width:600px; margin:0 auto; background-color:white; border-radius:10px; overflow:hidden; border:1px solid #e0d6d3;">
          
          <div style="background-color:#7B5C52; padding:20px; text-align:center;">
            <img src="https://e-commerce-backend-4-p9d1.onrender.com/static/cartify_logo.png" width="120" />
          </div>

          <div style="padding:40px 30px 20px 30px; text-align:center;">
            <h1 style="color:#7B5C52; font-size:28px;">Welcome to <strong>Cartify Sellers!</strong></h1>
            <p style="font-size:16px;">Hi <strong>{full_name}</strong>, your seller account is created and under verification.</p>
          </div>

          <div style="padding:0 30px 20px 30px;">
            <ul style="line-height:1.8;">
              <li>🔍 Our team will verify your business details.</li>
              <li>✅ You’ll get a confirmation email once approved.</li>
              <li>⏳ If not verified within 15 days, please contact us.</li>
            </ul>
          </div>

          <div style="text-align:center; padding:30px;">
            <a href="{FRONTEND_URL}/seller/login"
              style="background-color:#7B5C52; color:white; padding:12px 30px; border-radius:6px; text-decoration:none; font-size:16px; font-weight:bold;">
              Go to Seller Portal
            </a>
          </div>

          <div style="background-color:#EFEBE9; padding:20px; text-align:center; font-size:13px; color:#7B5C52;">
            <p>Need help? <a href="{FRONTEND_URL}/contact" style="color:#7B5C52; text-decoration:underline;">Contact support</a></p>
            <p>© {datetime.now().year} Cartify. All rights reserved.</p>
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
      <body style="margin:0;padding:0;background-color:#EFEBE9;font-family:'Helvetica Neue',Arial,sans-serif;color:#7B5C52;">
        <div style="max-width:600px;margin:0 auto;background:white;border-radius:10px;overflow:hidden;border:1px solid #e0d6d3;">
          
          <div style="background-color:#7B5C52;padding:20px;text-align:center;">
            <img src="https://e-commerce-backend-4-p9d1.onrender.com/static/cartify_logo.png" width="120" />
          </div>

          <div style="padding:40px 30px;">
            <h2 style="color:#7B5C52;">Account Verification in Progress</h2>
            <p>Dear <strong>{full_name}</strong>, your store details were recently updated and are under verification.</p>
            <ul style="line-height:1.7;">
              <li><strong>Store Name:</strong> {store_name}</li>
              <li><strong>Address:</strong> {store_address}</li>
              <li><strong>Description:</strong> {store_description or "N/A"}</li>
            </ul>
            <p>We’ll notify you once verification is complete.</p>
          </div>

          <div style="background:#EFEBE9;padding:20px;text-align:center;color:#7B5C52;font-size:13px;">
            <p>© {datetime.now().year} Cartify. All rights reserved.</p>
          </div>

        </div>
      </body>
    </html>
    """
    return subject, html_content

def send_order_cancelled_email(user_email: str, user_name: str, order_id: int):
    subject = f"Your Order Has Been Cancelled"

    html_content = f"""
    <html>
    <body style="font-family:Arial,sans-serif;background-color:#EFEBE9;padding:20px;color:#7B5C52;">
        <div style="max-width:600px;margin:auto;background:white;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,0.08);overflow:hidden;border:1px solid #e0d6d3;">
            
            <div style="background-color:#7B5C52;padding:20px;text-align:center;color:white;">
                <h2 style="margin:0;">Order Cancelled</h2>
            </div>

            <div style="padding:25px;">
                <p style="font-size:16px;">Hi <strong>{user_name}</strong>,</p>
                <p>Your order <strong>#{order_id}</strong> has been successfully cancelled.</p>
                <p>If paid already, your refund will be processed within <strong>15 business days</strong>.</p>
                <p>Contact our support team if this was a mistake.</p>

                <div style="margin-top:30px;text-align:center;">
                    <a href="{FRONTEND_URL}/orders/{order_id}"
                       style="background-color:#7B5C52;color:white;padding:12px 24px;text-decoration:none;border-radius:6px;">
                       View Order Details
                    </a>
                </div>
            </div>

            <div style="background-color:#EFEBE9;padding:15px;text-align:center;font-size:13px;color:#7B5C52;">
                <p>Thank you for shopping with <strong>Cartify</strong>.</p>
                <p>Contact: <a href="mailto:support@cartify.com" style="color:#7B5C52;text-decoration:underline;">support@cartify.com</a></p>
            </div>

        </div>
    </body>
    </html>
    """

    return {"subject": subject, "html_content": html_content}

def seller_account_approved_template(full_name: str):
    subject = "Your Seller Account Has Been Approved! 🎉"

    html_content = f"""
    <html>
      <body style="margin:0; padding:0; background-color:#EFEBE9; 
                   font-family:'Helvetica Neue', Arial, sans-serif; color:#7B5C52;">

        <div style="max-width:600px; margin:0 auto; background-color:white; 
                    border-radius:10px; overflow:hidden; border:1px solid #e0d6d3;">

          <!-- Header -->
          <div style="background-color:#7B5C52; padding:20px; text-align:center;">
            <img src="https://e-commerce-backend-4-p9d1.onrender.com/static/cartify_logo.png" 
                 alt="Cartify Logo" width="120" />
          </div>

          <!-- Main Content -->
          <div style="padding:40px 30px; text-align:center;">
            <h1 style="color:#7B5C52; font-size:28px;">Welcome Aboard, Seller! 🎉</h1>
            <p style="font-size:16px;">
              Hi <strong>{full_name}</strong>, we’re excited to inform you that your seller
              account has been <strong>approved</strong>!
            </p>

            <p style="font-size:15px; margin-top:20px;">
              Your account is now active, and you can start building your business on Cartify.
            </p>

            <ul style="text-align:left; line-height:1.8; margin-top:20px; color:#7B5C52;">
              <li>🏬 Add and customize your store details</li>
              <li>📦 Upload products with images, variations & pricing</li>
              <li>📊 Access your seller dashboard & analytics</li>
              <li>🚚 Start receiving customer orders</li>
            </ul>

            <div style="margin-top:30px;">
              <a href="{FRONTEND_URL}/seller/dashboard"
                 style="background-color:#7B5C52; color:white; padding:12px 28px; 
                        border-radius:6px; text-decoration:none; font-size:16px; 
                        font-weight:bold;">
                Go to Seller Dashboard
              </a>
            </div>
          </div>

          <!-- Footer -->
          <div style="background-color:#EFEBE9; padding:20px; text-align:center; 
                      font-size:13px; color:#7B5C52;">
            <p>Need help? 
              <a href="{FRONTEND_URL}/contact" 
                 style="color:#7B5C52; text-decoration:underline;">
                Contact our support team
              </a>
            </p>
            <p>© {datetime.now().year} Cartify. All rights reserved.</p>
          </div>

        </div>
      </body>
    </html>
    """

    return subject, html_content

def seller_account_rejected_template(full_name: str):
    subject = "Your Seller Account Status Update"

    html_content = f"""
    <html>
      <body style="margin:0; padding:0; background-color:#EFEBE9; 
                   font-family:'Helvetica Neue', Arial, sans-serif; color:#7B5C52;">

        <div style="max-width:600px; margin:0 auto; background-color:white; 
                    border-radius:10px; overflow:hidden; border:1px solid #e0d6d3;">

          <!-- Header -->
          <div style="background-color:#7B5C52; padding:20px; text-align:center;">
            <img src="https://e-commerce-backend-4-p9d1.onrender.com/static/cartify_logo.png" 
                 alt="Cartify Logo" width="120" />
          </div>

          <!-- Main Content -->
          <div style="padding:40px 30px; text-align:center;">
            <h1 style="color:#7B5C52; font-size:28px;">Account Review Update</h1>
            <p style="font-size:16px;">
              Hi <strong>{full_name}</strong>, unfortunately your seller account request 
              has been <strong>rejected</strong> at this time.
            </p>

            <p style="font-size:15px; margin-top:20px;">
              Please review your details and try submitting again with correct information.
              Our team will be happy to review your application once more.
            </p>

            <div style="margin-top:30px;">
              <a href="{FRONTEND_URL}/support"
                 style="background-color:#7B5C52; color:white; padding:12px 28px; 
                        border-radius:6px; text-decoration:none; font-size:16px; 
                        font-weight:bold;">
                Contact Support
              </a>
            </div>
          </div>

          <!-- Footer -->
          <div style="background-color:#EFEBE9; padding:20px; text-align:center; 
                      font-size:13px; color:#7B5C52;">
            <p>© {datetime.now().year} Cartify. All rights reserved.</p>
          </div>

        </div>
      </body>
    </html>
    """

    return subject, html_content