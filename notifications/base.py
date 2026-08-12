from abc import ABC, abstractmethod
from typing import Any, Dict

class NotificationProvider(ABC):
    def __init__(self, provider_name: str):
        self.provider_name = provider_name

    @abstractmethod
    def send(self, recipient: str, subject: str, body: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send a notification through this provider."""
        raise NotImplementedError
