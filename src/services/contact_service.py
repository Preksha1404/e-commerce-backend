from fastapi import BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from src.schemas.contact import ContactRequest
from src.services.email_service import send_email
from src.utils.email_templates import contact_us_email_template
import os

class ContactService:

    @staticmethod
    async def submit_contact_form(
        db: Session,
        form: ContactRequest,
        background_tasks: BackgroundTasks
    ):
        """
        Handles contact form submission and sends the details to admin email.
        """

        # Your admin email from environment variablese
        admin_email = os.getenv("MAIL_FROM")
        
        if not admin_email:
            raise HTTPException(
                status_code=500,
                detail="Admin email not configured on server."
            )

        subject, html_content = contact_us_email_template(form)

        # Send email to admin
        await send_email(
            background_tasks=background_tasks,
            to_email=admin_email,
            subject=subject,
            html_content=html_content,
            reply_to=form.email
        )

        return {
            "status": "success",
            "message": "Your message has been sent successfully."
        }
