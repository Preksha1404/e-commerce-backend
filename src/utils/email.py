from datetime import datetime
from fastapi import BackgroundTasks
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Environment configs
SENDGRID_API_KEY          = os.getenv("SENDGRID_API_KEY")
MAIL_FROM                 = os.getenv("MAIL_FROM", "noreply@yourstore.com")
FRONTEND_URL              = os.getenv("FRONTEND_URL", "http://localhost:3000")
RESET_TOKEN_EXPIRE_MINUTES = os.getenv("RESET_TOKEN_EXPIRE_MINUTES", "30")


def send_email_background(background_tasks: BackgroundTasks, message: Mail):
    """
    Schedules the actual send operation via SendGrid in the background.
    """
    def send_email_task():
        try:
            sg = SendGridAPIClient(api_key=SENDGRID_API_KEY)
            response = sg.client.mail.send.post(request_body=message.get())
            print("✅ Email send response:", response.status_code, response.body, response.headers)
        except Exception as e:
            print("❌ SendGrid Error:", e)

    background_tasks.add_task(send_email_task)


def send_mail(
    to_email: str,
    subject: str,
    html_content: str,
    background_tasks: BackgroundTasks
):
    """
    Generic function for sending any custom email.
    :param to_email: recipient email (string)
    :param subject: email subject string
    :param html_content: full HTML of the email body
    :param background_tasks: FastAPI BackgroundTasks instance
    """
    message = Mail(
        from_email=MAIL_FROM,
        to_emails=[to_email],
        subject=subject,
        html_content=html_content
    )
    send_email_background(background_tasks, message)


# ---------------------------------------------------------
# PASSWORD RESET EMAIL
# ---------------------------------------------------------
async def send_reset_email(
    email: str,
    token: str,
    background_tasks: BackgroundTasks
):
    """Send password reset link to user."""
    reset_link = f"{FRONTEND_URL}/reset-password?token={token}"
    html_content = f"""
    <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>Click the button below to reset your password:</p>
            <a href="{reset_link}"
               style="background:#007bff;color:white;padding:10px 20px;
                      border-radius:5px;text-decoration:none;">
                Reset Password
            </a>
            <p>This link expires in {RESET_TOKEN_EXPIRE_MINUTES} minutes.</p>
        </body>
    </html>
    """
    subject = "🔐 Password Reset Request"
    message = Mail(
        from_email=MAIL_FROM,
        to_emails=[email],
        subject=subject,
        html_content=html_content
    )
    send_email_background(background_tasks, message)
# ---------------------------------------------------------
# SELLER VERIFICATION EMAIL
# ---------------------------------------------------------
async def send_seller_verification_email(
    email: str,
    full_name: str,
    verification_link: str,
    background_tasks: BackgroundTasks
):
    """Send seller verification email after registration."""
    subject = "🛍️ Verify Your Seller Account Cartify"
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333;">
        <h2 style="color:#007bff;">Welcome to Cartify, {full_name}! 🎉</h2>
        <p>Thank you for registering as a seller on <strong>Cartify</strong>.</p>
        <p>To complete your registration and start listing your products, please verify your email address by clicking the button below:</p>
        <a href="{verification_link}" 
           style="background-color:#007bff;color:white;padding:10px 20px;
                  border-radius:5px;text-decoration:none;display:inline-block;margin-top:10px;">
           Verify My Account
        </a>
        <p>If you didn’t create a seller account, you can safely ignore this email.</p>
        <br/>
        <p>— The Cartify Seller Onboarding Team</p>
        <p><a href="https://cartify.com">www.cartify.com</a> | 
           <a href="mailto:sellersupport@cartify.com">sellersupport@cartify.com</a></p>
      </body>
    </html>
    """

    message = Mail(
        from_email=MAIL_FROM,
        to_emails=[email],
        subject=subject,
        html_content=html_content
    )
    send_email_background(background_tasks, message)

async def send_seller_block_status_email(
    email: str,
    full_name: str,
    is_blocked: bool,
    background_tasks: BackgroundTasks
):
    """Send email notification when a seller is blocked or unblocked by admin using dark theme."""
    
    status_text = "blocked" if is_blocked else "unblocked"
    subject = f"Your Seller Account Has Been {status_text.capitalize()}"

    html_content = f"""
    <html>
      <body style="margin:0; padding:0; background-color:#0d0d0d; font-family:'Helvetica Neue', Arial, sans-serif; color:#f0f0f0;">
        <div style="max-width:600px; margin:0 auto; background-color:#1a1a1a; border-radius:10px; overflow:hidden;">
          <div style="background-color:#000000; padding:20px; text-align:center;">
            <img src="https://i.postimg.cc/tCqfC2rQ/cartify-logo.png" alt="Cartify Logo" width="120" />
          </div>
          <div style="padding:40px 30px;">
            <h2 style="color:#ffffff;">Account {status_text.capitalize()}</h2>
            <p>Dear <strong>{full_name}</strong>,</p>
            <p>
              {"Your seller account has been temporarily blocked due to unusual activity or a potential policy violation. All your products are now hidden from customers." if is_blocked else "Access to your seller account has been restored. You can now log in and manage your products and orders."}
            </p>
            {f'<p>For assistance, contact <a href="mailto:sellersupport@cartify.com">sellersupport@cartify.com</a>.</p>' if is_blocked else ""}
          </div>
          <div style="background-color:#000000; padding:20px; text-align:center; color:#888888; font-size:13px;">
            <p>© {datetime.now().year} Cartify. All rights reserved.</p>
            <p><a href="https://cartify.com" style="color:#888888;">www.cartify.com</a> | <a href="mailto:sellersupport@cartify.com" style="color:#888888;">sellersupport@cartify.com</a></p>
          </div>
        </div>
      </body>
    </html>
    """

    message = Mail(
        from_email=MAIL_FROM,
        to_emails=[email],
        subject=subject,
        html_content=html_content
    )
    send_email_background(background_tasks, message)


# ---------------------------------------------------------
# SELLER BLOCK / UNBLOCK EMAIL
# ---------------------------------------------------------



# ---------------------------------------------------------
# CUSTOMER BLOCK / UNBLOCK EMAIL
# ---------------------------------------------------------
async def send_customer_block_status_email(
    email: str,
    full_name: str,
    is_blocked: bool,
    background_tasks: BackgroundTasks
):
    """Send email when a customer is blocked/unblocked by admin."""
    if is_blocked:
        subject = "⚠️ Account Access Restricted – Action Required"
        html_content = f"""
        <html>
          <body>
            <h2>⚠️ Account Access Restricted – Action Required</h2>
            <p>Dear <strong>{full_name}</strong>,</p>
            <p>We regret to inform you that your account has been <strong>temporarily blocked</strong> due to unusual activity or a potential policy violation.</p>
            <p>For your security, all access to your account features has been restricted until this issue is resolved.</p>
            <p>To restore access, please contact our support team at
              <strong>📧 support@cartify.com</strong><br/>
              Include your registered email address and any relevant details to help us verify your account faster.
            </p>
            <br/>
            <p>We appreciate your patience and cooperation in helping us keep your account secure.</p>
            <br/>
            <p>— Cartify Security Team</p>
          </body>
        </html>
        """
    else:
        subject = "✅ Account Access Restored"
        html_content = f"""
        <html>
          <body>
            <h2>✅ Account Access Restored</h2>
            <p>Dear <strong>{full_name}</strong>,</p>
            <p>Your account access has been fully restored. You may now log in and resume using your account as usual.</p>
            <br/>
            <p>Thank you for your cooperation and understanding.</p>
            <br/>
            <p>— Cartify Security Team</p>
          </body>
        </html>
        """

    message = Mail(
        from_email=MAIL_FROM,
        to_emails=[email],
        subject=subject,
        html_content=html_content
    )
    send_email_background(background_tasks, message)
