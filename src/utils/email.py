from fastapi import BackgroundTasks
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os
from dotenv import load_dotenv

load_dotenv()

FRONTEND_URL = os.getenv("FRONTEND_URL")
RESET_TOKEN_EXPIRE_MINUTES = os.getenv("RESET_TOKEN_EXPIRE_MINUTES")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
MAIL_FROM = os.getenv("MAIL_FROM")

async def send_reset_email(
    email: str,
    token: str,
    background_tasks: BackgroundTasks
):
    """Send password reset email using SendGrid Web API"""

    reset_link = f"{FRONTEND_URL}/reset-password?token={token}"

    html_content = f"""
    <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>Click the button below to reset your password:</p>
            <a href="{reset_link}" 
                style="background:#007bff;color:white;padding:10px 20px;border-radius:5px;text-decoration:none;">
                Reset Password
            </a>
            <p>Expires in {RESET_TOKEN_EXPIRE_MINUTES} minutes.</p>
        </body>
    </html>
    """

    message = Mail(
        from_email=MAIL_FROM,
        to_emails=email,
        subject="Password Reset",
        html_content=html_content
    )

    def send_email():
        try:
            sg = SendGridAPIClient(SENDGRID_API_KEY)
            sg.send(message)
        except Exception as e:
            print("SendGrid Error:", e)

    background_tasks.add_task(send_email)

async def send_seller_verification_email(
    email: str,
    full_name: str,
    store_name: str,
    store_address: str,
    store_description: str,
    background_tasks: BackgroundTasks
):
    """Send verification email when seller updates store info"""

    subject = "Your Seller Account is Under Verification"
    html_content = f"""
    <html>
        <body>
            <h2>Account Verification in Progress</h2>
            <p>Dear <strong>{full_name}</strong>,</p>
            <p>Your store details were recently updated. 
            Your account is temporarily inactive while we verify the new information.</p>

            <h3>Updated Store Details</h3>
            <ul>
                <li><strong>Store Name:</strong> {store_name}</li>
                <li><strong>Address:</strong> {store_address}</li>
                <li><strong>Description:</strong> {store_description or "N/A"}</li>
            </ul>

            <p>We’ll notify you once your account is verified again.</p>
            <br />
            <p>Regards,<br><strong>Admin Team</strong></p>
        </body>
    </html>
    """

    message = Mail(
        from_email=MAIL_FROM,
        to_emails=email,
        subject=subject,
        html_content=html_content
    )

    def send_email():
        try:
            sg = SendGridAPIClient(SENDGRID_API_KEY)
            sg.send(message)
        except Exception as e:
            print("SendGrid Error:", e)

    background_tasks.add_task(send_email)

async def send_welcome_email(
    email: str,
    full_name: str,
    background_tasks: BackgroundTasks
):
    """Send Cartify-themed welcome email to new customer"""
    
    subject = "Welcome to Cartify – Discover Your Perfect Find!"
    
    html_content = f"""
    <html>
      <body style="margin:0; padding:0; background-color:#0d0d0d; font-family: 'Helvetica Neue', Arial, sans-serif; color:#f0f0f0;">
        <div style="max-width:600px; margin:0 auto; background-color:#1a1a1a; border-radius:10px; overflow:hidden;">
          
          <!-- Header -->
          <div style="background-color:#000000; padding:20px; text-align:center;">
            <img src="https://i.postimg.cc/tCqfC2rQ/cartify-logo.png" alt="Cartify Logo" width="120" style="margin-bottom:5px;" />
          </div>
          
          <!-- Hero Section -->
          <div style="padding:40px 30px 20px 30px; text-align:center;">
            <h1 style="color:#ffffff; font-size:28px; margin-bottom:10px;">
              Welcome to <span style="color:#ff6600;">Cartify!</span>
            </h1>
            <p style="color:#cccccc; font-size:16px; line-height:1.6;">
              Hi <strong>{full_name}</strong>, we’re thrilled to have you join <strong>Cartify</strong> — your destination for
              fashion, electronics, furniture and more.
            </p>
          </div>
          
          <!-- What to Do Next -->
          <div style="padding:0 30px 20px 30px;">
            <p style="font-size:15px; color:#cccccc;">Here’s what you can do next:</p>
            <ul style="color:#dddddd; line-height:1.8;">
              <li>🛍️ Explore curated collections of trending products.</li>
              <li>💸 Enjoy exclusive discounts and limited-time offers.</li>
              <li>⚡ Experience fast delivery and secure checkout.</li>
            </ul>
          </div>
          
          <!-- CTA Button -->
          <div style="text-align:center; padding:30px;">
            <a href="{FRONTEND_URL}"
               style="background-color:#ff6600; color:#ffffff; padding:12px 30px; border-radius:6px; text-decoration:none; font-size:16px; font-weight:bold;">
               Shop Now
            </a>
          </div>
          
          <!-- Footer -->
          <div style="background-color:#000000; padding:20px; text-align:center; font-size:13px; color:#888888;">
            <p>Need help? <a href="{FRONTEND_URL}/contact" style="color:#ff6600; text-decoration:none;">Contact our support team</a></p>
            <p style="margin-top:10px;">© {2025} Cartify. All rights reserved.</p>
          </div>
        </div>
      </body>
    </html>
    """
    
    message = Mail(
      from_email=MAIL_FROM,
      to_emails=email,
      subject=subject,
      html_content=html_content
    )
    
    def send_email():
        try:
          sg = SendGridAPIClient(SENDGRID_API_KEY)
          sg.send(message)
        except Exception as e:
          print("SendGrid Error:", e)
    
    background_tasks.add_task(send_email)

async def send_seller_welcome_email(
    email: str,
    full_name: str,
    background_tasks: BackgroundTasks
):
    """Send Cartify-themed welcome email to new seller after registration"""

    subject = "Welcome to Cartify – Seller Account Under Verification"

    html_content = f"""
    <html>
      <body style="margin:0; padding:0; background-color:#0d0d0d; font-family: 'Helvetica Neue', Arial, sans-serif; color:#f0f0f0;">
        <div style="max-width:600px; margin:0 auto; background-color:#1a1a1a; border-radius:10px; overflow:hidden;">
          
          <!-- Header -->
          <div style="background-color:#000000; padding:20px; text-align:center;">
            <img src="https://i.postimg.cc/tCqfC2rQ/cartify-logo.png" alt="Cartify Logo" width="120" style="margin-bottom:5px;" />
          </div>

          <!-- Hero Section -->
          <div style="padding:40px 30px 20px 30px; text-align:center;">
            <h1 style="color:#ffffff; font-size:28px; margin-bottom:10px;">
              Welcome to <span style="color:#ff6600;">Cartify Sellers!</span>
            </h1>
            <p style="color:#cccccc; font-size:16px; line-height:1.6;">
              Hi <strong>{full_name}</strong>, thank you for registering as a seller on <strong>Cartify</strong>.
              Your account has been successfully created and is currently
              <span style="color:#ff6600;">under verification</span>.
            </p>
          </div>

          <!-- Info Section -->
          <div style="padding:0 30px 20px 30px;">
            <p style="font-size:15px; color:#cccccc;">Here’s what happens next:</p>
            <ul style="color:#dddddd; line-height:1.8;">
              <li>🔍 Our team will review and verify your business details.</li>
              <li>✅ Once approved, you’ll receive an activation confirmation email.</li>
              <li>⏳ If your account isn’t approved within 15 days, please reach out to us for assistance.</li>
            </ul> 
          </div>

          <!-- CTA Button -->
          <div style="text-align:center; padding:30px;">
            <a href="{FRONTEND_URL}/seller/login"
               style="background-color:#ff6600; color:#ffffff; padding:12px 30px; border-radius:6px; text-decoration:none; font-size:16px; font-weight:bold;">
               Go to Seller Portal
            </a>
          </div>

          <!-- Footer -->
          <div style="background-color:#000000; padding:20px; text-align:center; font-size:13px; color:#888888;">
            <p>Need help? <a href="{FRONTEND_URL}/contact" style="color:#ff6600; text-decoration:none;">Contact our support team</a></p>
            <p style="margin-top:10px;">© {2025} Cartify. All rights reserved.</p>
          </div>
        </div>
      </body>
    </html>
    """

    message = Mail(
      from_email=MAIL_FROM,
      to_emails=email,
      subject=subject,
      html_content=html_content
    )

    def send_email():
        try:
          sg = SendGridAPIClient(SENDGRID_API_KEY)
          sg.send(message)
        except Exception as e:
          print("SendGrid Error:", e)

    background_tasks.add_task(send_email)