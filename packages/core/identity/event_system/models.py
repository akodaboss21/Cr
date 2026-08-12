"""
Event System - Data Models
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from packages.core.database import Base

class Event(Base):
    __tablename__ = 'events'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey('organizations.id'), nullable=False)
    
    # Event Details
    name = Column(String(100), nullable=False)
    event_type = Column(String(50), nullable=False)  # 'lead_created', 'appointment_scheduled', etc.
    description = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship('Organization', back_populates='events')
    event_subscribers = relationship('EventSubscriber', back_populates='event')
    event_triggers = relationship('EventTrigger', back_populates='event')

class EventSubscriber(Base):
    __tablename__ = 'event_subscribers'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String(36), ForeignKey('events.id'), nullable=False)
    user_id = Column(String(36), ForeignKey('users.id'))
    organization_id = Column(String(36), ForeignKey('organizations.id'), nullable=False)
    
    # Subscription Details
    role = Column(String(50))  # 'admin', 'manager', 'agent', etc.
    notification_preferences = Column(Text)  # JSON data
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    event = relationship('Event', back_populates='event_subscribers')
    user = relationship('User', back_populates='event_subscriptions')
    organization = relationship('Organization', back_populates='event_subscribers')

class EventTrigger(Base):
    __tablename__ = 'event_triggers'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String(36), ForeignKey('events.id'), nullable=False)
    
    # Trigger Details
    name = Column(String(100), nullable=False)
    condition = Column(Text)  # JSON data or simple expression
    action = Column(String(100), nullable=False)  # 'send_email', 'update_crm', etc.
    parameters = Column(Text)  # JSON data
    
    # Status
    is_active = Column(Boolean, default=True)
    last_triggered_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    event = relationship('Event', back_populates='event_triggers')