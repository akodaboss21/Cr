from __future__ import annotations

from typing import Any, Dict


class GoogleCalendarAdapter:
    def publish(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {"provider": "google", "status": "pending", "payload": payload}


class OutlookCalendarAdapter:
    def publish(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {"provider": "outlook", "status": "pending", "payload": payload}
