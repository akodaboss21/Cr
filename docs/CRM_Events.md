# Carai CRM Events System

## Executive Summary
This document defines the CRM Events system for Carai CRM, which implements an event-driven architecture for tracking and responding to customer-related events. The system enables real-time event processing and integration with other systems.

## Event Types

### 1. Lead Events
- **lead.created**: When a new lead is created
- **lead.updated**: When a lead is updated
- **lead.converted**: When a lead is converted to a customer
- **lead.lost**: When a lead is marked as lost

### 2. Customer Events
- **customer.created**: When a new customer is created
- **customer.updated**: When a customer profile is updated
- **customer.returned**: When a customer makes a repeat purchase

### 3. Booking Events
- **booking.created**: When a new booking is created
- **booking.completed**: When a booking is completed
- **booking.cancelled**: When a booking is cancelled

## Event System Features

### 1. Event Creation
- **Automatic**: Events created by system actions (e.g., lead creation)
- **Manual**: Events created by user actions (e.g., manual note addition)

### 2. Event Processing
- **Synchronous**: Immediate event processing
- **Asynchronous**: Background event processing
- **Event Handlers**: Event handlers for different event types

### 3. Integration Points
- **CRM**: Events stored and processed in CRM
- **Analytics**: Events sent to analytics system
- **Notifications**: Events trigger notifications
- **Webhooks**: Events sent to external systems

## Event Data Model
```python
class CRMEvent:
    def __init__(self, event_id):
        self.event_id = event_id
        self.event_type = None
        self.customer_id = None
        self.lead_id = None
        self.booking_id = None
        self.timestamp = datetime.utcnow()
        self.data = {}
        self.processed = False
```

## Event Handlers

### 1. Lead Event Handler
```python
class LeadEventHandler:
    def handle_lead_created(self, event):
        # Create lead in CRM
        # Send notifications
        # Update analytics
        pass
    
    def handle_lead_updated(self, event):
        # Update lead in CRM
        # Send notifications
        # Update analytics
        pass
```

### 2. Customer Event Handler
```python
class CustomerEventHandler:
    def handle_customer_created(self, event):
        # Create customer in CRM
        # Send welcome email
        # Update analytics
        pass
    
    def handle_customer_returned(self, event):
        # Update customer loyalty score
        # Send loyalty rewards
        # Update analytics
        pass
```

## Integration Requirements
1. Create event model in CRM module
2. Implement event handlers for each event type
3. Create event processing service
4. Implement event publishing/subscribing
5. Create event API endpoints

## Benefits
- Real-time event tracking
- Enables event-driven architecture
- Improves system responsiveness
- Enables integration with external systems
- Supports complex business logic

## Next Steps
1. Create event model in CRM module
2. Implement event handlers
3. Create event processing service
4. Implement event publishing/subscribing
5. Create event API endpoints