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