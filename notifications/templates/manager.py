import re
from typing import Any, Dict, Optional

TEMPLATES = {
    "new_lead": {
        "email": {
            "subject": "New lead from {{ business_name }}",
            "body": "A new lead has been created for {{ business_name }}: {{ lead_name }} ({{ lead_email }}).",
        },
        "sms": {
            "subject": "",
            "body": "New lead: {{ lead_name }} ({{ lead_phone }}).",
        },
        "whatsapp": {
            "subject": "",
            "body": "New lead alert for {{ business_name }}: {{ lead_name }}. Contact: {{ lead_phone }}.",
        },
        "push": {
            "subject": "New lead received",
            "body": "{{ business_name }} has a new lead: {{ lead_name }}.",
        },
    },
    "new_booking": {
        "email": {
            "subject": "New booking for {{ business_name }}",
            "body": "A new booking has been scheduled for {{ business_name }} on {{ booking_date }} at {{ booking_time }}.",
        },
        "sms": {
            "subject": "",
            "body": "New booking: {{ booking_date }} at {{ booking_time }}.",
        },
        "whatsapp": {
            "subject": "",
            "body": "New booking: {{ booking_date }} at {{ booking_time }} for {{ customer_name }}.",
        },
        "push": {
            "subject": "New booking received",
            "body": "Booking for {{ booking_date }} at {{ booking_time }}.",
        },
    },
    "booking_reminder": {
        "email": {
            "subject": "Booking reminder for {{ customer_name }}",
            "body": "This is a reminder for your booking on {{ booking_date }} at {{ booking_time }}.",
        },
        "sms": {
            "subject": "",
            "body": "Reminder: booking on {{ booking_date }} at {{ booking_time }}.",
        },
        "whatsapp": {
            "subject": "",
            "body": "Reminder: your booking is scheduled for {{ booking_date }} at {{ booking_time }}.",
        },
        "push": {
            "subject": "Booking Reminder",
            "body": "You have a booking on {{ booking_date }} at {{ booking_time }}.",
        },
    },
    "customer_message": {
        "email": {
            "subject": "New customer message from {{ customer_name }}",
            "body": "{{ customer_name }} sent a new message: {{ message_summary }}.",
        },
        "sms": {
            "subject": "",
            "body": "New message from {{ customer_name }}: {{ message_summary }}.",
        },
        "whatsapp": {
            "subject": "",
            "body": "New message from {{ customer_name }}: {{ message_summary }}.",
        },
        "push": {
            "subject": "New customer message",
            "body": "{{ customer_name }} sent a message.",
        },
    },
    "human_takeover": {
        "email": {
            "subject": "Human takeover required",
            "body": "A customer requires human takeover: {{ customer_name }}.",
        },
        "sms": {
            "subject": "",
            "body": "Human takeover required for {{ customer_name }}.",
        },
        "whatsapp": {
            "subject": "",
            "body": "Human takeover requested by {{ customer_name }}.",
        },
        "push": {
            "subject": "Human takeover alert",
            "body": "{{ customer_name }} needs human assistance.",
        },
    },
    "payment_event": {
        "email": {
            "subject": "Payment update for {{ business_name }}",
            "body": "Payment event detected: {{ payment_status }} for {{ amount }}.",
        },
        "sms": {
            "subject": "",
            "body": "Payment {{ payment_status }}: {{ amount }}.",
        },
        "whatsapp": {
            "subject": "",
            "body": "Payment {{ payment_status }} for {{ amount }}.",
        },
        "push": {
            "subject": "Payment event",
            "body": "{{ payment_status }}: {{ amount }}.",
        },
    },
}

class TemplateManager:
    def __init__(self, templates: Optional[Dict[str, Any]] = None):
        self.templates = templates or TEMPLATES

    def get_template(self, event_type: str, channel: str) -> Optional[Dict[str, str]]:
        return self.templates.get(event_type, {}).get(channel)

    def render(self, template: str, payload: Dict[str, Any]) -> str:
        rendered = template
        for key, value in payload.items():
            rendered = re.sub(r"{{\s*%s\s*}}" % re.escape(key), str(value), rendered)
        rendered = re.sub(r"{{\s*[\w_]+\s*}}", "", rendered)
        return rendered

    def register_template(self, event_type: str, channel: str, subject: str, body: str) -> None:
        if event_type not in self.templates:
            self.templates[event_type] = {}
        self.templates[event_type][channel] = {"subject": subject, "body": body}
