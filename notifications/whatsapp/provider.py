import logging
from typing import Any, Dict

from packages.core.config import settings

logger = logging.getLogger(__name__)

class WhatsAppProvider:
    def __init__(self):
        self.api_url = settings.WHATSAPP_API_URL
        self.api_token = settings.WHATSAPP_API_TOKEN
        self.from_number = settings.WHATSAPP_PHONE_NUMBER

    def send(self, recipient: str, subject: str, body: str, data: Dict[str, Any]) -> Dict[str, Any]:
        if not recipient:
            return {"status": "failed", "reason": "missing recipient"}

        if self.api_url and self.api_token and self.from_number:
            logger.info("Sending WhatsApp message to %s", recipient)
            # Placeholder: integrate WhatsApp Business API here.
            return {"status": "sent", "provider": "whatsapp", "recipient": recipient}

        logger.warning("WhatsApp provider not configured; message skipped")
        return {"status": "skipped", "reason": "whatsapp provider not configured"}
