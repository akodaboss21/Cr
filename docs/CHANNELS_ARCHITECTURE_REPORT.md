# Carai Channels Layer Architecture Report

## Executive Summary
The Carai Channels Layer provides a provider-agnostic, extensible foundation for connecting the Carai Reception Agent to various communication channels. This architecture enables seamless integration with website chat widgets and future messaging platforms (WhatsApp, Instagram, Messenger, Email) while maintaining a consistent interface and separating concerns.

## Phase 1: Channel Architecture

### Components Created
- **Channel Base Class** (`channels/base.py`): Abstract base class defining the standard channel interface
- **Channel Registry** (`channels/registry.py`): Central registry for managing channel instances and placeholders
- **Message Normalization** (`channels/unified_message.py`): UnifiedMessage dataclass for standardized message format
- **Channel Implementations**: 
  - `channels/website_channel.py`: Website chat widget channel
  - `channels/whatsapp_channel.py`: WhatsApp channel placeholder
  - Similar placeholders for Instagram, Messenger, and Email

### Key Features
- Abstract interface ensuring consistent implementation across channels
- Separation of raw message handling and unified message processing
- Customer identity extraction for personalized interactions
- Channel registration and discovery mechanism

## Phase 2: Channel Interface

### Standard Interface Definition
All channels implement the `Channel` abstract base class with four required methods:

```python
class Channel(ABC):
    @abstractmethod
    def receive_message(self, raw_message):
        """Convert raw channel message to UnifiedMessage"""
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
```

### Implementation Details
- **WebsiteChannel**: Implements full functionality for website interactions
- **PlaceholderChannels**: Provide structure for future platform integrations
- **ChannelRegistry**: Manages channel instantiation and lookup by name

## Phase 3: Message Normalization

### UnifiedMessage Format
All channel communications are normalized to the `UnifiedMessage` format:

```python
@dataclass
class UnifiedMessage:
    organization_id: str
    channel: str
    customer_id: str
    conversation_id: str
    content: str
    metadata: Dict[str, Any]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'organization_id': self.organization_id,
            'channel': self.channel,
            'customer_id': self.customer_id,
            'conversation_id': self.conversation_id,
            'content': self.content,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create from dictionary representation"""
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        return cls(
            organization_id=data['organization_id'],
            channel=data['channel'],
            customer_id=data['customer_id'],
            conversation_id=data['conversation_id'],
            content=data['content'],
            metadata=data.get('metadata', {}),
            timestamp=timestamp
        )
```

### Benefits
- Standardized message structure across all channels
- Consistent metadata handling
- Timestamp tracking for conversation history
- Easy serialization/deserialization
- Future-proof design for adding new message attributes

## Phase 4: Website Chat Widget

### Embeddable Script Implementation
Created complete widget implementation in `apps/widget/`:

- **HTML** (`apps/widget/widget.html`): Widget structure with floating button and chat window
- **CSS** (`apps/widget/widget.css`): Styling with support for:
  - Multiple positions (bottom-right, bottom-left)
  - Light/dark themes
  - Business branding colors
- **JavaScript** (`apps/widget/widget.js`): Full functionality including:
  - Floating button toggle
  - Chat window display/hide
  - Message sending and receiving
  - Streaming responses with typing indicators
  - Branding integration (colors, logo, greeting)
  - Rate limiting and validation
  - WebSocket real-time communication
  - Analytics event tracking

### Key Features
- Responsive design for mobile and desktop
- Brand-aware styling (colors, logo, greeting)
- Message persistence and conversation history
- Typing indicators for natural conversation flow
- Error handling and fallback mechanisms
- Analytics integration for tracking interactions

## Phase 5: Widget Branding

### Automatic Branding Integration
The widget automatically receives branding elements from the Business Profile:

- **Business Logo**: Applied to widget header
- **Brand Colors**: Used for primary UI elements
- **Theme**: Light/dark mode support with custom themes
- **Greeting Message**: Customizable welcome text
- **AI Personality**: Integrated with reception agent personality

### Implementation
- Branding data fetched from `/api/branding/{business_id}` endpoint
- Applied to widget DOM elements during initialization
- Supports dynamic theme switching based on business profile

## Phase 6: Widget Configuration

### Configuration Options
Supports customization through constructor config:

- **Position**: `bottom-right` (default) or `bottom-left`
- **Theme**: `light` or `dark` (respects system preference)
- **Greeting**: Custom welcome message
- **Avatar**: Custom emoji or icon
- **Welcome Text**: Additional branding text

### Settings Panel
Configuration can be updated through:
- URL parameters (`?carai_position=bottom-left`)
- Cookie-based settings
- API calls to update branding profile

## Phase 7: Security

### Security Measures Implemented
- **Public Business Identifier**: Business ID extracted from URL parameters or cookies
- **Rate Limiting**: Client-side and server-side rate limiting (10 messages/minute)
- **Origin Validation**: Checks Origin header for legitimate requests
- **Abuse Protection**: Content filtering for inappropriate messages
- **Secure Endpoints**: All widget communications use `/api/` prefixed secure endpoints
- **No Sensitive Data Exposure**: LLM keys and internal APIs never exposed to client

### Security Best Practices
- Input sanitization for all user messages
- Server-side validation of all incoming requests
- Rate limiting to prevent abuse
- Secure WebSocket connections (wss://)
- Analytics events sent via `navigator.sendBeacon` for security

## Phase 8: Realtime

### Real-time Communication
- **WebSocket Implementation**: Primary method for real-time messaging
- **Fallback**: Long polling could be implemented for basic scenarios
- **Message Streaming**: Partial responses with typing indicators
- **Connection Handling**: Automatic reconnection with exponential backoff

### Features
- Live message streaming from AI responses
- Typing indicators for natural conversation flow
- Connection state management
- Event-based updates for conversation state

## Phase 9: Future Channel Preparation

### Placeholder Channels
Created template implementations for:
- **WhatsAppChannel**: WhatsApp Business API integration pattern
- **InstagramChannel**: Instagram Direct API integration pattern
- **MessengerChannel**: Meta Messenger API integration pattern
- **EmailChannel**: SMTP/IMAP integration pattern

### Architecture
All placeholders inherit from the same `Channel` interface, ensuring consistent behavior and easy future implementation.

## Phase 10: Analytics Events

### Event Tracking System
Implemented comprehensive analytics tracking in JavaScript:

- **Message Received**: `message_received` - When a message is received from a channel
- **Response Generated**: `response_generated` - When AI generates a response
- **Lead Captured**: `lead_captured` - When contact information is collected
- **Booking Created**: `booking_created` - When an appointment is scheduled
- **Human Takeover**: `human_takeover` - When conversation is handed to a human agent
- **WebSocket Events**: Connection open, close, and errors
- **Branding Loaded**: `branding_loaded` - When business branding is applied

### Implementation
- Events sent via `navigator.sendBeacon()` to `/api/analytics/widget`
- Includes business context, timestamps, and event-specific properties
- Designed for minimal performance impact

## Phase 11: Testing

### Testing Strategy
Testing approach includes:

1. **Unit Tests**: For channel interface implementations
2. **Integration Tests**: Between widget and reception agent
3. **End-to-End Tests**: Full widget workflow
4. **Security Tests**: Rate limiting and abuse protection validation

### Test Cases Identified
- Widget loads correctly on various devices
- Messages are properly sent and received
- AI responds appropriately to various inputs
- Brand theme loads correctly from profile
- Rate limiting prevents abuse
- Security validations work as expected

## Phase 12: Final Report

### Documentation
Created comprehensive documentation:
- `docs/FINAL_COMPLETION_REPORT.md` - Summary of all implemented phases
- `docs/CHANNELS_ARCHITECTURE_REPORT.md` - Detailed channel architecture documentation

## Architecture Summary

### Key Design Principles
1. **Separation of Concerns**: Channel handling separated from AI logic
2. **Provider Independence**: Channels don't contain AI-specific logic
3. **Extensibility**: New channels can be added without modifying existing code
4. **Consistency**: Uniform interface across all communication channels
5. **Security First**: Security measures built into every layer
6. **Observability**: Comprehensive analytics and monitoring capabilities

### Integration Points
- **Reception Agent**: Receives UnifiedMessage objects from channels
- **Business Branding**: Supplies branding data to channels
- **Analytics System**: Tracks all channel interactions
- **Database**: Stores conversation history and customer identities

### Future Expansion
- Add new channels by implementing the Channel interface
- Expand analytics with additional event types
- Enhance security with more sophisticated abuse detection
- Add SSE support as alternative to WebSockets

## Success Criteria

### Business Workflow
1. **Create Account**: Business registers and gets branding profile
2. **Configure AI**: Set up channel preferences and branding
3. **Embed Widget**: Add script tag to website
3. **Customer Interaction**: Visitor chats via widget
4. **AI Response**: Reception agent handles conversation
5. **Lead Capture**: Contact info collected and stored
6. **Dashboard Visibility**: Conversation appears in admin dashboard

### Technical Requirements Met
- ✅ Channel-independent reception agent logic
- ✅ No AI logic in channels
- ✅ No modifications to existing frontend pages
- ✅ Channel-specific handling only for receiving/sending messages
- ✅ UnifiedMessage format for all communications
- ✅ Future channels can be added without changing AI logic

## Conclusion
The Carai Channels Layer successfully implements a robust, extensible foundation for multi-channel communication. By adhering to the defined interface and normalization patterns, the architecture ensures that new communication channels can be added with minimal effort while maintaining security, observability, and consistency across all customer interactions.