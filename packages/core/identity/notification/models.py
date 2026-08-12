"""
Notification Module - Data Models
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from packages.core.database import Base

class Notification(Base):
    __tablename__ = 'notifications'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey('organizations.id'), nullable=False)
    business_id = Column(String(36), ForeignKey('business_profiles.id'))
    recipient_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    
    # Notification Details
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), nullable=False)  # 'email', 'sms', 'push', 'webhook'
    
    # Status
    status = Column(String(20), default='pending')  # 'pending', 'sent', 'failed', 'delivered'
    
    # Delivery
    recipient = Column(String(255))
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    
    # Metadata
    data = Column(Text)  # JSON data
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship('Organization', back_populates='notifications')
    business = relationship('BusinessProfile', back_populates='notifications')
    recipient_user = relationship('User', back_populates='notifications')


class NotificationSetting(Base):
    __tablename__ = 'notification_settings'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey('organizations.id'), nullable=False)
    business_id = Column(String(36), ForeignKey('business_profiles.id'))
    event_type = Column(String(100), nullable=False)
    enabled = Column(Boolean, default=True)
    channels = Column(Text)
    schedule = Column(String(100))
    timezone = Column(String(50), default='UTC')
    data = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = relationship('Organization')
    business = relationship('BusinessProfile')