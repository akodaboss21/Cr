from __future__ import annotations

from typing import Any, Dict


class ReminderService:
    def schedule_reminder(self, organization_id: str, recipient_id: str, channel: str, message: str) -> Dict[str, Any]:
        return {
            "organization_id": organization_id,
            "recipient_id": recipient_id,
            "channel": channel,
            "message": message,
            "status": "queued",
        }
