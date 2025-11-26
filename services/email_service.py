import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import logging

logger = logging.getLogger(__name__)


def send_email(to_email: str, subject: str, body: str):
    """
    Send an email using SMTP credentials from environment variables.
    Falls back to logging if credentials are not set.
    """
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT", "587")
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    if not all([smtp_host, smtp_user, smtp_password]):
        logger.warning(f"SMTP credentials missing. Mocking email send to {to_email}")
        print(
            f"--- MOCK EMAIL ---\nTo: {to_email}\nSubject: {subject}\nBody: {body}\n------------------"
        )
        return True

    try:
        msg = MIMEMultipart()
        msg["From"] = smtp_user
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(smtp_host, int(smtp_port)) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)

        logger.info(f"Email sent to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False
