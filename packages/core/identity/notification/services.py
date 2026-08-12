import logging
from typing import Any, Dict, List, Optional

from notifications.engine import NotificationEngine

logger = logging.getLogger(__name__)

class NotificationService:
    _engine = NotificationEngine()

    @classmethod
    def send_event_notification(
        cls,
        event_type: str,
        recipient: Dict[str, str],
        payload: Dict[str, Any],
        channels: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        logger.info("Dispatching notification event %s", event_type)
        return cls._engine.send_event_notification(
            event_type=event_type,
            recipient=recipient,
            payload=payload,
            channels=channels,
        )
