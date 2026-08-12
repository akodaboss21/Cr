import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

class PushProvider:
    def __init__(self):
        self.provider_name = "local_push"

    def send(self, recipient: str, subject: str, body: str, data: Dict[str, Any]) -> Dict[str, Any]:
        if not recipient:
            return {"status": "failed", "reason": "missing recipient"}

        logger.info("Sending push notification to %s", recipient)
        return {"status": "sent", "provider": "push", "recipient": recipient}
