from fastapi import BackgroundTasks
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os
from dotenv import load_dotenv
from typing import Optional
import logging

load_dotenv()

logger = logging.getLogger(__name__)

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
MAIL_FROM = os.getenv("MAIL_FROM")

logger.info(f"SendGrid API Key configured: {bool(SENDGRID_API_KEY)}")
logger.info(f"Mail from address: {MAIL_FROM}")

def send_email(
    background_tasks: Optional[BackgroundTasks],
    to_email: str,
    subject: str,
    html_content: str,
    from_email: str = MAIL_FROM,
    reply_to: Optional[str] = None
):
    """Generic function to send email synchronously via SendGrid"""

    logger.info(f"Preparing email - To: {to_email}, Subject: {subject}")

    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject=subject,
        html_content=html_content
    )

    if reply_to:
        message.reply_to = reply_to
        
    def send():
        try:
            logger.info(f"Sending email via SendGrid to {to_email}")
            sg = SendGridAPIClient(SENDGRID_API_KEY)
            response = sg.send(message)
            logger.info(f"Email sent successfully to {to_email}. Status code: {response.status_code}")
        except Exception as e:
            logger.error(f"SendGrid Error sending to {to_email}: {str(e)}")

    if background_tasks is not None:
        background_tasks.add_task(send)
        logger.info(f"Email task added to background tasks for {to_email}")
    else:
        send()