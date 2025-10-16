from fastapi import BackgroundTasks
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
import os
from dotenv import load_dotenv

load_dotenv()

FRONTEND_URL=os.getenv('FRONTEND_URL')
RESET_TOKEN_EXPIRE_MINUTES=os.getenv('RESET_TOKEN_EXPIRE_MINUTES')

async def send_reset_email(
    email: str, 
    token: str, 
    background_tasks: BackgroundTasks,
):
    """Send password reset email"""
    
    reset_link = f"{FRONTEND_URL}/reset-password?token={token}"
    
    html_content = f"""
    <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>You have requested to reset your password.</p>
            <p>Click the link below to reset your password:</p>
            <a href="{reset_link}">Reset Password</a>
            <p>This link will expire in {RESET_TOKEN_EXPIRE_MINUTES} minutes.</p>
            <p>If you did not request this, please ignore this email.</p>
        </body>
    </html>
    """
    
    message = MessageSchema(
        subject=f"Password Reset Request",
        recipients=[email],
        body=html_content,
        subtype="html"
    )
    
    # Email Configuration
    mail_conf = ConnectionConfig(
        MAIL_USERNAME=os.getenv('MAIL_USERNAME'),
        MAIL_PASSWORD=os.getenv('MAIL_PASSWORD'),
        MAIL_FROM=os.getenv('MAIL_FROM'),
        MAIL_PORT=int(os.getenv('MAIL_PORT')),
        MAIL_SERVER=os.getenv('MAIL_SERVER'),
        MAIL_STARTTLS=True,
        MAIL_SSL_TLS=False,
        USE_CREDENTIALS=True
    )
    
    fm = FastMail(mail_conf)
    background_tasks.add_task(fm.send_message, message)