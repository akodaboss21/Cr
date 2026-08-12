import json
import logging
from typing import Any, Dict, List, Optional

from notifications.base import NotificationProvider
from notifications.email.provider import EmailProvider
from notifications.push.provider import PushProvider
from notifications.sms.provider import SMSProvider
from notifications.templates.manager import TemplateManager
from notifications.whatsapp.provider import WhatsAppProvider

logger = logging.getLogger(__name__)

DEFAULT_CHANNELS = {
    "new_lead": ["email", "sms", "whatsapp"],
    "new_booking": ["email", "whatsapp", "push"],
    "booking_reminder": ["email", "sms", "push"],
    "customer_message": ["email", "whatsapp"],
    "human_takeover": ["email", "push"],
    "payment_event": ["email", "sms"],
}

class NotificationEngine:
    def __init__(self, providers: Optional[Dict[str, NotificationProvider]] = None):
        self.template_manager = TemplateManager()
        self.providers = providers or {
            "email": EmailProvider(),
            "sms": SMSProvider(),
            "whatsapp": WhatsAppProvider(),
            "push": PushProvider(),
        }

    def get_channels_for_event(self, event_type: str) -> List[str]:
        return DEFAULT_CHANNELS.get(event_type, ["email"])

    def send_event_notification(
        self,
        event_type: str,
        recipient: Dict[str, str],
        payload: Dict[str, Any],
        channels: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        channels = channels or self.get_channels_for_event(event_type)
        results = []

        for channel in channels:
            template = self.template_manager.get_template(event_type, channel)
            if not template:
                logger.warning("No template found for event %s on channel %s", event_type, channel)
                continue

            subject = template.get("subject", "")
            body = template.get("body", "")
            rendered_subject = self.template_manager.render(subject, payload)
            rendered_body = self.template_manager.render(body, payload)

            provider = self.providers.get(channel)
            if not provider:
                logger.warning("No provider configured for channel %s", channel)
                results.append({"channel": channel, "status": "skipped", "reason": "no provider"})
                continue

            destination = recipient.get(channel) or recipient.get("default") or recipient.get("email")
            if not destination:
                logger.warning("No destination found for channel %s", channel)
                results.append({"channel": channel, "status": "skipped", "reason": "no destination"})
                continue

            result = provider.send(destination, rendered_subject, rendered_body, payload)
            result_data = {
                "channel": channel,
                "recipient": destination,
                "status": result.get("status", "failed"),
                "details": result,
            }
            results.append(result_data)

        return results

    def render_template(self, event_type: str, channel: str, payload: Dict[str, Any]) -> Dict[str, str]:
        template = self.template_manager.get_template(event_type, channel)
        subject = self.template_manager.render(template.get("subject", ""), payload)
        body = self.template_manager.render(template.get("body", ""), payload)
        return {"subject": subject, "body": body}
