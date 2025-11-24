import os
from datetime import datetime
from typing import List, Dict, Optional

FRONTEND_URL = os.getenv("FRONTEND_URL")
RESET_TOKEN_EXPIRE_MINUTES = os.getenv("RESET_TOKEN_EXPIRE_MINUTES")

def password_reset_template(email: str, token: str):
    reset_link = f"{FRONTEND_URL}/reset-password?token={token}"
    subject = "Password Reset"

    frontend = FRONTEND_URL or "#"

    html_content = f"""
    <html>
      <body style="margin:0; padding:0; background-color:#EFEBE9; font-family:'Helvetica Neue', Arial, sans-serif; color:#7B5C52;">
        <div style="max-width:600px; margin:0 auto; background-color:white; border-radius:10px; overflow:hidden; border:1px solid #e0d6d3;">
          <div style="background-color:#7B5C52; padding:20px; text-align:center;">
            <img src="https://res.cloudinary.com/duamb3iin/image/upload/cartify_logo.png" alt="Cartify Logo" width="120" />
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
            <img src="https://res.cloudinary.com/duamb3iin/image/upload/cartify_logo.png" alt="Cartify Logo" width="120" />
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
            <img src="https://res.cloudinary.com/duamb3iin/image/upload/cartify_logo.png" width="120" />
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
            <img src="https://res.cloudinary.com/duamb3iin/image/upload/cartify_logo.png" width="120" />
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
                    <a href="{FRONTEND_URL}/profile/orders"
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


def _format_currency(amount: float) -> str:
    return f"₹{amount:,.2f}"


def _build_order_items_table(items: List[Dict[str, float]]) -> str:
    if not items:
        return """
        <tr>
            <td colspan="3" style="padding:12px;text-align:center;color:#999;">
                No items were found in this order.
            </td>
        </tr>
        """

    rows = ""
    for item in items:
        rows += f"""
        <tr>
            <td style="padding:12px;border-bottom:1px solid #f0e7e4;">{item.get("name", "Item")}</td>
            <td style="padding:12px;text-align:center;border-bottom:1px solid #f0e7e4;">{item.get("quantity", 1)}</td>
            <td style="padding:12px;text-align:right;border-bottom:1px solid #f0e7e4;">{_format_currency(item.get("total_price", 0.0))}</td>
        </tr>
        """
    return rows


def send_order_confirmation_email(
    user_name: str,
    order_id: int,
    total_amount: float,
    payment_method: str,
    items: List[Dict[str, float]],
    shipping_address: str,
    subtotal: float,
    discount: float,
    coupon_code: Optional[str] = None,
):
    subject = f"Your Cartify Order #{order_id} is Confirmed"
    items_html = _build_order_items_table(items)

    coupon_text = coupon_code if coupon_code else "Not applied"
    discount_text = _format_currency(discount if discount else 0.0)

    html_content = f"""
    <html>
      <body style="margin:0; padding:0; background-color:#EFEBE9; font-family:'Helvetica Neue', Arial, sans-serif; color:#7B5C52;">
        <div style="max-width:640px; margin:0 auto; background-color:white; border-radius:10px; overflow:hidden; border:1px solid #e0d6d3;">
          <div style="background-color:#7B5C52; padding:20px; text-align:center;">
            <img src="https://res.cloudinary.com/duamb3iin/image/upload/cartify_logo.png" alt="Cartify Logo" width="120" />
          </div>

          <div style="padding:35px;">
            <h2 style="margin-top:0;">Hi {user_name},</h2>
            <p>Thank you for shopping with Cartify. Your order has been successfully placed.</p>

            <div style="margin-top:25px;">
              <h3 style="margin-bottom:10px;">Order Summary</h3>
              <table style="width:100%; border-collapse:collapse; font-size:14px;">
                <thead>
                  <tr style="background-color:#f9f4f2;">
                    <th style="text-align:left; padding:12px;">Item</th>
                    <th style="text-align:center; padding:12px;">Qty</th>
                    <th style="text-align:right; padding:12px;">Total</th>
                  </tr>
                </thead>
                <tbody>
                  {items_html}
                </tbody>
              </table>
            </div>

            <div style="margin-top:25px; border-top:1px solid #f0e7e4; padding-top:20px; font-size:14px;">
              <p><strong>Subtotal:</strong> {_format_currency(subtotal)}</p>
              <p><strong>Discount:</strong> {discount_text}</p>
              <p><strong>Coupon:</strong> {coupon_text}</p>
              <p><strong>Payment Method:</strong> {payment_method}</p>
              <p><strong>Grand Total:</strong> {_format_currency(total_amount)}</p>
            </div>

            <div style="margin-top:25px;">
              <h3 style="margin-bottom:10px;">Shipping To</h3>
              <p style="line-height:1.6;">{shipping_address}</p>
            </div>

            <div style="text-align:center; margin-top:30px;">
              <a href="{FRONTEND_URL}/profile/orders" style="background-color:#7B5C52; color:white; padding:12px 28px; border-radius:6px; text-decoration:none; font-weight:bold;">
                Track Order
              </a>
            </div>
          </div>

          <div style="background-color:#EFEBE9; padding:20px; text-align:center; font-size:13px; color:#7B5C52;">
            <p>Need help? <a href="{FRONTEND_URL}/contact" style="color:#7B5C52; text-decoration:underline;">Contact support</a></p>
            <p>© {datetime.now().year} Cartify. All rights reserved.</p>
          </div>
        </div>
      </body>
    </html>
    """

    return {"subject": subject, "html_content": html_content}


def send_order_delivered_email(
    user_name: str,
    order_id: int,
    total_amount: float,
    items: List[Dict[str, float]],
    shipping_address: str,
):
    subject = f"Good news! Order #{order_id} has been delivered"
    items_html = _build_order_items_table(items)

    frontend = FRONTEND_URL or "#"

    html_content = f"""
    <html>
      <body style="margin:0; padding:0; background-color:#EFEBE9; font-family:'Helvetica Neue', Arial, sans-serif; color:#7B5C52;">
        <div style="max-width:640px; margin:0 auto; background-color:white; border-radius:10px; overflow:hidden; border:1px solid #e0d6d3;">
          <div style="background-color:#7B5C52; padding:20px; text-align:center;">
            <img src="https://res.cloudinary.com/duamb3iin/image/upload/cartify_logo.png" alt="Cartify Logo" width="120" />
          </div>

          <div style="padding:35px;">
            <h2 style="margin-top:0;">Hi {user_name},</h2>
            <p>Your order <strong>#{order_id}</strong> has been delivered successfully. We hope you enjoy your purchase!</p>

            <div style="margin-top:25px;">
              <h3 style="margin-bottom:10px;">Items Delivered</h3>
              <table style="width:100%; border-collapse:collapse; font-size:14px;">
                <thead>
                  <tr style="background-color:#f9f4f2;">
                    <th style="text-align:left; padding:12px;">Item</th>
                    <th style="text-align:center; padding:12px;">Qty</th>
                    <th style="text-align:right; padding:12px;">Total</th>
                  </tr>
                </thead>
                <tbody>
                  {items_html}
                </tbody>
              </table>
            </div>

            <div style="margin-top:25px; border-top:1px solid #f0e7e4; padding-top:20px; font-size:14px;">
              <p><strong>Grand Total Paid:</strong> {_format_currency(total_amount)}</p>
            </div>

            <div style="margin-top:25px;">
              <h3 style="margin-bottom:10px;">Delivered To</h3>
              <p style="line-height:1.6;">{shipping_address}</p>
            </div>

            <div style="text-align:center; margin-top:30px;">
              <a href="{frontend}/orders/{order_id}" style="background-color:#7B5C52; color:white; padding:12px 28px; border-radius:6px; text-decoration:none; font-weight:bold;">
                View Order
              </a>
            </div>
          </div>

          <div style="background-color:#EFEBE9; padding:20px; text-align:center; font-size:13px; color:#7B5C52;">
            <p>Would you like to tell us how we did? <a href="{frontend}/orders/{order_id}/review" style="color:#7B5C52; text-decoration:underline;">Share feedback</a></p>
            <p>© {datetime.now().year} Cartify. All rights reserved.</p>
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
            <img src="https://res.cloudinary.com/duamb3iin/image/upload/cartify_logo.png" 
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
            <img src="https://res.cloudinary.com/duamb3iin/image/upload/cartify_logo.png 
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

def user_block_status_template(full_name: str, is_blocked: bool):
    if is_blocked:
        subject = "⚠️ Your Cartify Account Has Been Restricted"

        message_title = "⚠️ Account Access Restricted"
        message_body = f"""
            <p style="font-size:16px;">Dear <strong>{full_name}</strong>,</p>
            <p>Your account has been <strong>temporarily blocked</strong> due to suspicious activity or a policy violation.</p>
            <p>Please contact our support team for further assistance.</p>
        """
    else:
        subject = "✅ Your Cartify Account Is Now Active"

        message_title = "✅ Account Access Restored"
        message_body = f"""
            <p style="font-size:16px;">Dear <strong>{full_name}</strong>,</p>
            <p>Your account has been <strong>successfully unblocked</strong>.</p>
            <p>You can now log in and continue shopping without any issues.</p>
        """

    html_content = f"""
    <html>
      <body style="margin:0; padding:0; background-color:#EFEBE9; font-family:'Helvetica Neue', Arial, sans-serif; color:#7B5C52;">

        <div style="max-width:600px; margin:0 auto; background-color:white; border-radius:10px; overflow:hidden; border:1px solid #e0d6d3;">

          <!-- Header -->
          <div style="background-color:#7B5C52; padding:20px; text-align:center;">
            <img src="https://res.cloudinary.com/duamb3iin/image/upload/cartify_logo.png" width="120" />
          </div>

          <!-- Title -->
          <div style="padding:40px 30px 20px 30px; text-align:center;">
            <h1 style="color:#7B5C52; font-size:26px;">{message_title}</h1>
          </div>

          <!-- Body -->
          <div style="padding:0 30px 20px 30px; line-height:1.7; font-size:15px;">
            {message_body}
          </div>

          <!-- Button -->
          <div style="text-align:center; padding:25px;">
            <a href="{FRONTEND_URL}/login"
              style="background-color:#7B5C52; color:white; padding:12px 30px; border-radius:6px; text-decoration:none; font-size:16px; font-weight:bold;">
              Visit Cartify
            </a>
          </div>

          <!-- Footer -->
          <div style="background-color:#EFEBE9; padding:20px; text-align:center; font-size:13px; color:#7B5C52;">
            <p>Need help? <a href="{FRONTEND_URL}/contact" style="color:#7B5C52; text-decoration:underline;">Contact Support</a></p>
            <p>© {datetime.now().year} Cartify. All rights reserved.</p>
          </div>

        </div>
      </body>
    </html>
    """

    return subject, html_content

def contact_us_email_template(form):
    html = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px;">
        <h2>Contact Us Message</h2>

        <p><strong>Name:</strong> {form.first_name} {form.last_name}</p>
        <p><strong>Email:</strong> {form.email}</p>
        <p><strong>Phone:</strong> {form.phone or "Not Provided"}</p>
        <p><strong>Subject:</strong> {form.subject}</p>
        <p><strong>Message:</strong><br>{form.message}</p>
    </div>
    """
    subject = f"Contact Form: {form.subject}"
    return subject, html
