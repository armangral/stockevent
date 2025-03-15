from datetime import datetime
import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from tempfile import NamedTemporaryFile

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
import jinja2
import pdfkit
from pydantic import EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User


# Generate a random binary password of a specified length (e.g., 16 bytes)
def generate_random_password(length: int = 16):
    return os.urandom(length)


class EmailException(Exception):
    pass


conf = ConnectionConfig(
    MAIL_USERNAME=settings.SMTP_USERNAME,
    MAIL_PASSWORD="okeckxzrxjtkpbkg",
    MAIL_FROM=settings.EMAIL_FROM,
    MAIL_PORT=587,
    MAIL_SERVER=settings.SMTP_SERVER,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    TEMPLATE_FOLDER=os.path.join(os.path.dirname(__file__), "templates"),
)


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    user = await db.execute(select(User).where(User.email == email))
    user = user.scalars().first()
    return user


def send_email(to_email: str, subject: str, body: str):
    msg = MIMEMultipart()
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(
        MIMEText(body, "html")
    )  # logger.error(f"Failed to send email to {to_email}: {str(e)}")

    try:
        with smtplib.SMTP(
            settings.SMTP_SERVER, settings.SMTP_PORT, timeout=10
        ) as server:
            print("checking login")
            server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAIL_FROM, to_email, msg.as_string())
    except (smtplib.SMTPException, ConnectionError, TimeoutError) as e:
        print(f"Failed to send email to {to_email}: {str(e)}")
        raise EmailException(f"Failed to send email: {str(e)}")


async def send_invitation_email(
    db: AsyncSession, to_email: str, token: str, expiration_time: str
):
    get_user = await get_user_by_email(db, to_email)
    if not get_user:
        invitation_link = f"{settings.FRONTEND_URL}/accept/{token}"
    else:
        invitation_link = f"{settings.FRONTEND_URL}/accept-exists/{token}"
    message = MessageSchema(
        subject="Email Verification",
        recipients=[to_email],
        template_body={
            "email": to_email,
            "token": token,
            "expiration_time": expiration_time,
            "invitation_link": invitation_link,
        },
        subtype="html",
    )

    fm = FastMail(conf)
    await fm.send_message(message, template_name="email_invitation.html")


async def send_verification_email(to_email: str, token: str, expiration_time: str):
    invitation_link = f"{settings.FRONTEND_URL}/verify-email/{token}"
    message = MessageSchema(
        subject="Email Verification StockEvent",
        recipients=[to_email],
        template_body={
            "email": to_email,
            "token": token,
            "expiration_time": expiration_time,
            "invitation_link": invitation_link,
        },
        subtype="html",
    )

    fm = FastMail(conf)
    await fm.send_message(message, template_name="email_verification.html")


async def send_password_reset_email(to_email: str, token: str, expiration_time: str):
    reset_link = f"{settings.FRONTEND_URL}/reset-password/{token}"
    message = MessageSchema(
        subject="Password Reset - StockEvent",
        recipients=[to_email],
        template_body={
            "email": to_email,
            "token": token,
            "expiration_time": expiration_time,
            "reset_link": reset_link,
        },
        subtype="html",
    )
    fm = FastMail(conf)
    await fm.send_message(message, template_name="password_reset.html")


async def send_welcome_email(to_email: str, password: str):
    login_link = f"{settings.FRONTEND_URL}/signin"
    message = MessageSchema(
        subject="Welcome to StockEvent!",
        recipients=[to_email],
        template_body={
            "email": to_email,
            "password": password,
            "login_link": login_link,
        },
        subtype="html",
    )
    fm = FastMail(conf)
    await fm.send_message(message, template_name="welcome.html")


async def send_email_alert(email: EmailStr, subject: str, body: str):
    message = MessageSchema(
        subject=subject, recipients=[email], body=body, subtype=MessageType.plain
    )

    fm = FastMail(conf)
    await fm.send_message(message)
    return {"status": "Email sent successfully"}


async def send_property_email(to_email: str, property_details: dict):
    """
    Sends an email with a property summary as a PDF attachment generated from a Jinja2 HTML template.

    :param to_email: Recipient's email address
    :param property_details: Dictionary containing property details
    """
    try:
        # 1. Load Jinja2 template
        template_loader = jinja2.FileSystemLoader(conf.TEMPLATE_FOLDER)
        env = jinja2.Environment(loader=template_loader)
        template = env.get_template("property_summary.html")

        # 2. Render template with property details
        rendered_html = template.render(
            title="Property Summary",
            brand_name="StockEvent",
            property=property_details,
            now=datetime.now(),
        )

        # 3. Generate PDF from the rendered HTML
        pdf_options = {
            "encoding": "UTF-8",
            "enable-local-file-access": True,  # Required for loading local assets like images
        }
        pdf_data = pdfkit.from_string(rendered_html, False, options=pdf_options)

        # 4. Save the PDF to a temporary file
        with NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(pdf_data)
            temp_file_path = temp_file.name

        # 5. Create email message with PDF attachment
        message = MessageSchema(
            subject="Property Summary",
            recipients=[to_email],
            body="Please find attached the property summary.",
            subtype="html",
            attachments=[temp_file_path],
        )

        # 6. Send email using FastAPI-Mail
        fm = FastMail(conf)
        await fm.send_message(message)
        logging.info(f"Property summary email sent to {to_email}")

    except jinja2.TemplateNotFound as e:
        logging.error(f"Template not found: {e}")
        raise EmailException(f"Template not found: {e}")
    except Exception as e:
        logging.error(f"Failed to send property email to {to_email}: {str(e)}")
        raise EmailException(f"Failed to send property email: {str(e)}")
    finally:
        # 7. Clean up temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


# async def send_property_email(to_email: str, property_details: dict):
#     """
#     Sends an email with a property summary as a PDF attachment.
#     """

#     # 1. Generate HTML content for the property summary
#     html_content = f"""
#     <html>
#       <head><meta charset="utf-8"></head>
#       <body>
#         <h1>Property Summary</h1>
#         <p><strong>SKU:</strong> {property_details.get('sku', 'N/A')}</p>
#         <p><strong>Type:</strong> {property_details.get('type', 'N/A')}</p>
#         <p><strong>City:</strong> {property_details.get('city', 'N/A')}</p>
#         <p><strong>Price:</strong> {property_details.get('price', 'N/A')}</p>
#         <p><strong>Description:</strong> {property_details.get('description', 'N/A')}</p>
#       </body>
#     </html>
#     """

#     # 2. Generate PDF from HTML content
#     pdf_data = pdfkit.from_string(html_content, False)  # Returns PDF as bytes

#     # 3. Create email message schema
#     message = MessageSchema(
#         subject="Property Summary",
#         recipients=[to_email],
#         body="Please find attached the property summary.",
#         subtype="html",
#         attachments=[("Property_Summary.pdf", pdf_data, "application/pdf")],
#     )

#     # 4. Send email using FastAPI-Mail
#     fm = FastMail(conf)
#     await fm.send_message(message)