from abc import ABC, abstractmethod

class Channel(ABC):
    @abstractmethod
    def receive_message(self, raw_message):
        """Receive raw message from channel and return UnifiedMessage"""
        pass

    @abstractmethod
    def send_message(self, unified_message):
        """Send UnifiedMessage through channel"""
        pass

    @abstractmethod
    def validate_request(self, request_data):
        """Validate incoming request data"""
        pass

    @abstractmethod
    def get_customer_identity(self, request_data):
        """Extract customer identity from request"""
        pass

class WebsiteChannel(Channel):
    def receive_message(self, raw_message):
        # Parse website-specific messages (e.g., form submissions, chat inputs)
        return {
            'organization_id': 'default',
            'channel': 'website',
            'customer_id': 'temp',
            'conversation_id': 'temp',
            'content': raw_message,
            'metadata': {}
        }

    def send_message(self, unified_message):
        # Send response via website UI
        pass

    def validate_request(self, request_data):
        # Basic validation for website requests
        return True

    def get_customer_identity(self, request_data):
        # Extract customer ID from cookies/session
        return 'anonymous'

class ChannelRegistry:
    def __init__(self):
        self.channels = {}

    def register_channel(self, channel_name, channel_class):
        self.channels[channel_name] = channel_class()

    def get_channel(self, channel_name):
        return self.channels.get(channel_name)