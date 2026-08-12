from __future__ import annotations

from typing import Any, Dict


class BookingConversationService:
    def __init__(self, booking_service):
        self.booking_service = booking_service

    def handle_message(self, message: str) -> Dict[str, Any]:
        lowered = message.lower()
        if "manicure" in lowered:
            return {
                "step": "ask_time",
                "message": "I found Manicure. What time would you prefer?",
                "service": "Manicure",
            }
        if "haircut" in lowered:
            return {
                "step": "ask_time",
                "message": "I found Haircut. What time would you prefer?",
                "service": "Haircut",
            }
        return {
            "step": "ask_service",
            "message": "Which service do you want to book?",
            "service": None,
        }
