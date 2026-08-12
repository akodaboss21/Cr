# Carai Customer Timeline System

## Executive Summary
This document defines the Customer Timeline system for Carai CRM, which tracks all customer interactions in chronological order. The timeline provides a complete history of customer engagements, enabling better context for follow-ups and personalized service.

## Key Components

### 1. Timeline Data Structure
```python
class CustomerTimeline:
    def __init__(self, customer_id):
        self.customer_id = customer_id
        self.events = []  # List of timeline events

    def add_event(self, event_type, timestamp, details):
        self.events.append({
            'id': str(uuid4()),
            'type': event_type,
            'timestamp': timestamp,
            'details': details
        })

    def get_timeline(self):
        return sorted(self.events, key=lambda x: x['timestamp'])
```

### 2. Event Types
- **Message**: From channels layer (website, WhatsApp, etc.)
- **Booking**: From booking system
- **Lead Event**: Created/updated leads
- **Note**: AI or staff notes
- **Human Interaction**: Staff-customer interactions

### 3. Integration Points
- **Channels Layer**: Emits message events when messages are received
- **Booking System**: Emits booking events
- **Notes System**: Adds note events
- **Reception Agent**: Adds human interaction events

### 4. Data Model Example
```json
{
    "customer_id": "C123",
    "events": [
        {
            "id": "E1",
            "type": "message",
            "timestamp": "2026-08-01T10:00:00Z",
            "details": {
                "channel": "website",
                "content": "How much is a haircut?"
            }
        },
        {
            "id": "E2",
            "type": "booking",
            "timestamp": "2026-08-02T14:30:00Z",
            "details": {
                "service": "haircut",
                "status": "booked"
            }
        }
    ]
}
```

## Benefits
- Complete interaction history for better context
- Enables proactive follow-ups
- Supports AI-driven recommendations based on history
- Improves customer service consistency

## Integration Requirements
1. Modify CustomerProfile to include timeline
2. Add event emitters in Channels layer
3. Connect Booking system to timeline
4. Implement note system integration
5. Add human interaction tracking

## Next Steps
1. Extend CustomerProfile with timeline attribute
2. Implement event emitter in channels/base.py
3. Connect Booking system to timeline
4. Develop note system integration
5. Create API endpoint for timeline access