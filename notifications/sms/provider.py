import logging
from typing import Any, Dict

from packages.core.config import settings

logger = logging.getLogger(__name__)

class SMSProvider:
    def __init__(self):
        self.provider = settings.SMS_PROVIDER
        self.twilio_account_sid = settings.TWILIO_ACCOUNT_SID
        self.twilio_auth_token = settings.TWILIO_AUTH_TOKEN
        self.twilio_from_number = settings.TWILIO_FROM_NUMBER

    def send(self, recipient: str, subject: str, body: str, data: Dict[str, Any]) -> Dict[str, Any]:
        if not recipient:
            return {"status": "failed", "reason": "missing recipient"}

        if self.provider == "twilio" and self.twilio_account_sid and self.twilio_auth_token:
            logger.info("Sending SMS via Twilio to %s", recipient)
            # Placeholder: integrate Twilio SDK or HTTP API here.
            return {"status": "sent", "provider": "twilio", "recipient": recipient}

        logger.warning("SMS provider not configured; SMS skipped")
        return {"status": "skipped", "reason": "sms provider not configured"}
