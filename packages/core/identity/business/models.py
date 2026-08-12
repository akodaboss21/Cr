"""
Business Profile Module - Data Models
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from packages.core.database import Base

class BusinessProfile(Base):
    __tablename__ = 'business_profiles'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey('organizations.id'), nullable=False)
    owner_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    
    # Business Information
    business_name = Column(String(255), nullable=False)
    business_type = Column(String(100))
    
    # Contact Information
    address = Column(Text)
    phone = Column(String(20))
    email = Column(String(255))
    website = Column(String(255))
    
    # Business Details
    hours = Column(Text)
    services = Column(Text)
    pricing = Column(Text)
    staff_count = Column(Integer)
    
    # Social Media
    facebook = Column(String(255))
    twitter = Column(String(255))
    instagram = Column(String(255))
    linkedin = Column(String(255))
    
    # Branding
    logo_url = Column(String(255))
    primary_color = Column(String(7))
    secondary_color = Column(String(7))
    
    # Policies
    cancellation_policy = Column(Text)
    privacy_policy = Column(Text)
    terms_of_service = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship('Organization', back_populates='business_profile')
    owner = relationship('User', back_populates='business_profile')
    conversations = relationship('Conversation', back_populates='business')
    bookings = relationship('Booking', back_populates='business')
    crm_data = relationship('CRM', back_populates='business')
    notifications = relationship('Notification', back_populates='business')
    analytics = relationship('Analytics', back_populates='business')
    billing = relationship('Billing', back_populates='business')


class BusinessPolicy(Base):
    __tablename__ = 'business_policies'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey('organizations.id'), nullable=False)
    name = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = relationship('Organization')


class Service(Base):
    __tablename__ = 'services'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey('organizations.id'), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    price = Column(String(50))
    duration = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = relationship('Organization')


class Product(Base):
    __tablename__ = 'products'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey('organizations.id'), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    price = Column(String(50))
    sku = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = relationship('Organization')