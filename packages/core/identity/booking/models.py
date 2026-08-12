"""
Booking Module - Data Models
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from packages.core.database import Base

class Booking(Base):
    __tablename__ = 'bookings'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey('organizations.id'), nullable=False)
    business_id = Column(String(36), ForeignKey('business_profiles.id'))
    customer_id = Column(String(36), ForeignKey('users.id'))
    
    # Booking Details
    title = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(50), default='pending')  # 'pending', 'confirmed', 'canceled', 'completed'
    
    # Scheduling
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    timezone = Column(String(50), default='UTC')
    
    # Participants
    attendees = Column(Text)  # JSON array
    
    # Integration
    calendar_event_id = Column(String(255))
    google_calendar_id = Column(String(255))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship('Organization', back_populates='bookings')
    business = relationship('BusinessProfile', back_populates='bookings')
    customer = relationship('User', back_populates='bookings')