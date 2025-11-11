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
    """Send email notification when a seller is blocked or unblocked by admin."""

    if is_blocked:
        subject = "Account Access Restricted – Seller Account Temporarily Blocked"
        html_content = f"""
        <html>
          <body style="font-family: Arial, sans-serif; color: #333;">
            <h2 style="color:#d9534f;">⚠️ Account Access Restricted</h2>
            <p>Dear <strong>{full_name}</strong>,</p>
            <p>We regret to inform you that your <strong>seller account</strong> has been temporarily blocked due to unusual activity or a potential policy violation.</p>
            <p>For security reasons, access to your seller dashboard and related features has been restricted until this issue is resolved.</p>
            <p>To restore access, please contact our Seller Support team at 
               <a href="mailto:sellersupport@cartify.com"><strong>sellersupport@cartify.com</strong></a>
               using your registered email address and include your store name along with any relevant details.</p>
            <p>Our compliance team will review your case and assist you promptly.</p>
            <br/>
            <p>We appreciate your patience and cooperation in helping us maintain a secure and trustworthy marketplace.</p>
            <br/>
            <p>Warm regards,<br/>
            <strong>The Cartify Seller Support Team</strong></p>
            <p><a href="https://cartify.com">www.cartify.com</a> | <a href="mailto:sellersupport@cartify.com">sellersupport@cartify.com</a></p>
          </body>
        </html>
        """
    else:
        subject = "✅ Seller Account Access Restored"
        html_content = f"""
        <html>
          <body style="font-family: Arial, sans-serif; color: #333;">
            <h2 style="color:#28a745;">✅ Seller Account Access Restored</h2>
            <p>Dear <strong>{full_name}</strong>,</p>
            <p>We’re pleased to inform you that access to your seller account has been restored. You can now log in and continue managing your products and orders as usual.</p>
            <br/>
            <p>Thank you for your understanding and cooperation.</p>
            <br/>
            <p>Warm regards,<br/>
            <strong>The Cartify Seller Support Team</strong></p>
            <p><a href="https://cartify.com">www.cartify.com</a> | <a href="mailto:sellersupport@cartify.com">sellersupport@cartify.com</a></p>
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
