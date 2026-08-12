import logging
import os
import smtplib
from email.message import EmailMessage
from typing import Any, Dict

from packages.core.config import settings

logger = logging.getLogger(__name__)

class EmailProvider:
    def __init__(self):
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.user = settings.SMTP_USER
        self.password = settings.SMTP_PASSWORD
        self.use_tls = settings.SMTP_TLS
        self.from_email = settings.EMAILS_FROM_EMAIL

    def send(self, recipient: str, subject: str, body: str, data: Dict[str, Any]) -> Dict[str, Any]:
        if not recipient:
            return {"status": "failed", "reason": "missing recipient"}

        if not self.host:
            logger.warning("SMTP host is not configured; email skipped")
            return {"status": "skipped", "reason": "smtp not configured"}

        message = EmailMessage()
        message["Subject"] = subject or "Carai Notification"
        message["From"] = self.from_email
        message["To"] = recipient
        message.set_content(body)

        try:
            with smtplib.SMTP(self.host, self.port, timeout=10) as smtp:
                if self.use_tls:
                    smtp.starttls()
                if self.user and self.password:
                    smtp.login(self.user, self.password)
                smtp.send_message(message)

            return {"status": "sent", "provider": "smtp", "recipient": recipient}
        except Exception as exc:
            logger.exception("Failed to send email notification")
            return {"status": "failed", "provider": "smtp", "reason": str(exc)}
