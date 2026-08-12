# Carai Customer Profile System

## Executive Summary
This document outlines the design and implementation of the unified customer profile system for Carai CRM. The system consolidates customer data from multiple sources into a single, actionable profile that supports personalized interactions and business intelligence.

## Key Components

### 1. Customer Identity
- **Basic Information**: Name, Email, Phone
- **Business Relationship**:
  - First Interaction (date/time, channel)
  - Last Interaction (date/time, channel)
  - Total Conversations
  - Services Requested
  - Bookings

### 2. AI Memory
- **Preferences**: Service preferences, communication style
- **Notes**: AI-generated and staff-added notes
- **Important Details**: Special requests, allergies, loyalty status

### 3. Data Sources
- **Conversations**: From Channels layer (website, WhatsApp, etc.)
- **Bookings**: From Booking system
- **Business Profiles**: From Branding system
- **Analytics**: Conversion data, engagement metrics

## Data Model
```python
class CustomerProfile:
    def __init__(self, customer_id):
        self.customer_id = customer_id
        self.identity = {
            'name': '',
            'email': '',
            'phone': '',
        }
        self.business_relationship = {
            'first_interaction': {'date': '', 'channel': ''},
            'last_interaction': {'date': '', 'channel': ''},
            'total_conversations': 0,
            'services_requested': set(),
            'bookings': []
        }
        self.ai_memory = {
            'preferences': {
                'service_type': '',
                'communication_style': '',
            },
            'notes': [],
            'important_details': []
        }

    def update_from_conversation(self, conversation_data):
        # Update profile from new conversation
        pass

    def update_from_booking(self, booking_data):
        # Update profile from new booking
        pass

    def add_note(self, note_type, content, author):
        # Add note to AI memory or staff notes
        pass
```

## Integration Points
- **Channels Layer**: Receives messages to update profile
- **Reception Agent**: Detects buying intent to create/update leads
- **Booking System**: Updates booking history
- **Branding System**: Applies preferences to widget

## Benefits
- Single source of truth for customer data
- Enables personalized interactions
- Supports AI-driven recommendations
- Improves lead management

## Next Steps
1. Extend existing CRM models in `packages/core/identity/crm/`
2. Implement data synchronization from Channels and Booking systems
3. Develop AI memory update logic
4. Create API endpoints for profile access