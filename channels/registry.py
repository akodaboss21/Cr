from channels.base import ChannelRegistry

# Channel implementations
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

# Channel registry
registry = ChannelRegistry()
registry.register_channel('website', WebsiteChannel)

# Future channel placeholders
class WhatsAppChannel(Channel):
    def receive_message(self, raw_message):
        pass

    def send_message(self, unified_message):
        pass

    def validate_request(self, request_data):
        pass

    def get_customer_identity(self, request_data):
        pass

class InstagramChannel(Channel):
    def receive_message(self, raw_message):
        pass

    def send_message(self, unified_message):
        pass

    def validate_request(self, request_data):
        pass

    def get_customer_identity(self, request_data):
        pass

class MessengerChannel(Channel):
    def receive_message(self, raw_message):
        pass

    def send_message(self, unified_message):
        pass

    def validate_request(self, request_data):
        pass

    def get_customer_identity(self, request_data):
        pass

class EmailChannel(Channel):
    def receive_message(self, raw_message):
        pass

    def send_message(self, unified_message):
        pass

    def validate_request(self, request_data):
        pass

    def get_customer_identity(self, request_data):
        pass

# Register future channels
registry.register_channel('whatsapp', WhatsAppChannel)
registry.register_channel('instagram', InstagramChannel)
registry.register_channel('messenger', MessengerChannel)
registry.register_channel('email', EmailChannel)