import os
from typing import Optional
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from application.interfaces.email_sender import EmailSender


class SMTPEmailSender(EmailSender):
    def __init__(
        self,
        smtp_host: str = None,
        smtp_port: int = None,
        username: str = None,
        password: str = None,
        from_email: str = None,
        use_tls: bool = True
    ):
        self.smtp_host = smtp_host or os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = smtp_port or int(os.getenv("SMTP_PORT", "587"))
        self.username = username or os.getenv("SMTP_USERNAME")
        self.password = password or os.getenv("SMTP_PASSWORD")
        self.from_email = from_email or os.getenv("SMTP_FROM_EMAIL", "noreply@proctorwise.com")
        self.use_tls = use_tls

    async def send(self, to_email: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.from_email
            message["To"] = to_email

            text_part = MIMEText(body, "plain")
            message.attach(text_part)

            if html_body:
                html_part = MIMEText(html_body, "html")
                message.attach(html_part)

            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.username,
                password=self.password,
                start_tls=self.use_tls
            )

            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False


class MockEmailSender(EmailSender):
    def __init__(self):
        self.sent_emails = []

    async def send(self, to_email: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
        self.sent_emails.append({
            "to": to_email,
            "subject": subject,
            "body": body,
            "html_body": html_body
        })
        print(f"[MOCK EMAIL] To: {to_email}, Subject: {subject}")
        return True
