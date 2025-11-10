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
    store_name: str,
    store_address: str,
    store_description: str,
    background_tasks: BackgroundTasks
):
    """Notify seller that their store details are under verification."""
    subject = "🕓 Your Seller Account is Under Verification"
    html_content = f"""
    <html>
        <body>
            <h2>Account Verification in Progress</h2>
            <p>Dear <strong>{full_name}</strong>,</p>
            <p>Your store details were recently updated and are now under review.</p>

            <h3>Updated Store Details:</h3>
            <ul>
                <li><strong>Store Name:</strong> {store_name}</li>
                <li><strong>Address:</strong> {store_address}</li>
                <li><strong>Description:</strong> {store_description or "N/A"}</li>
            </ul>

            <p>We’ll notify you once the review is complete.</p>
            <br />
            <p>Regards,<br><strong>Cartify Team</strong></p>
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
async def send_seller_block_status_email(
    email: str,
    full_name: str,
    is_blocked: bool,
    background_tasks: BackgroundTasks
):
    """Send email when a seller is blocked/unblocked by admin."""
    if is_blocked:
        subject = "⚠️ Seller Account Access Restricted"
        html_content = f"""
        <html>
          <body>
            <h2>⚠️ Seller Account Access Restricted</h2>
            <p>Dear <strong>{full_name}</strong>,</p>
            <p>Your seller account has been <strong>temporarily blocked</strong> due to a potential policy violation,
               incomplete verification, or unusual account activity.</p>
            <p>This restriction prevents you from accessing your dashboard and listing new products until the issue is resolved.</p>
            <p>To review or appeal this action, please contact our Seller Support team at:<br>
               📧 <strong>sellersupport@example.com</strong><br>
               Include your registered email, store name, and any relevant details to help us verify your account faster.</p>
            <br/>
            <p>Thank you for your cooperation and understanding.</p>
            <br/>
            <p>— Cartify Seller Support Team</p>
          </body>
        </html>
        """
    else:
        subject = "✅ Seller Account Access Restored"
        html_content = f"""
        <html>
          <body>
            <h2>✅ Seller Account Access Restored</h2>
            <p>Dear <strong>{full_name}</strong>,</p>
            <p>Your seller account access has been restored. You can now log in and manage your listings again.</p>
            <br/>
            <p>— Cartify Seller Support Team</p>
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
