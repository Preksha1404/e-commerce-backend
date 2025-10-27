from fastapi import BackgroundTasks
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
import os
from dotenv import load_dotenv

load_dotenv()

FRONTEND_URL = os.getenv("FRONTEND_URL")
RESET_TOKEN_EXPIRE_MINUTES = os.getenv("RESET_TOKEN_EXPIRE_MINUTES")

async def send_reset_email(
    email: str,
    token: str,
    background_tasks: BackgroundTasks,
):
    """Send password reset email using SendGrid SMTP"""

    reset_link = f"{FRONTEND_URL}/reset-password?token={token}"

    html_content = f"""
    <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>You requested to reset your password.</p>
            <p>Click below to reset:</p>
            <a href="{reset_link}">Reset Password</a>
            <p>Expires in {RESET_TOKEN_EXPIRE_MINUTES} minutes.</p>
            <p>If this isn't you, ignore this email.</p>
        </body>
    </html>
    """

    message = MessageSchema(
        subject="Password Reset Request",
        recipients=[email],
        body=html_content,
        subtype="html"
    )

    mail_conf = ConnectionConfig(
        MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
        MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
        MAIL_FROM=os.getenv("MAIL_FROM"),
        MAIL_PORT=int(os.getenv("MAIL_PORT")),
        MAIL_SERVER=os.getenv("MAIL_SERVER"),
        MAIL_TLS = os.getenv("MAIL_TLS", "True").lower() == "true",
        MAIL_SSL = os.getenv("MAIL_SSL", "False").lower() == "true",
        USE_CREDENTIALS=True,
    )

    fm = FastMail(mail_conf)
    background_tasks.add_task(fm.send_message, message)