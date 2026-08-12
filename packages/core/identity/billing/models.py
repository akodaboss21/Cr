"""
Billing Module - Data Models
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer
from sqlalchemy.orm import relationship, synonym
from datetime import datetime
import uuid

from packages.core.database import Base

class Billing(Base):
    __tablename__ = 'billing'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey('organizations.id'), nullable=False)
    customer_id = Column(String(36), ForeignKey('users.id'))
    business_id = Column(String(36), ForeignKey('business_profiles.id'))
    
    # Billing Details
    invoice_id = Column(String(100), unique=True)
    description = Column(String(255), nullable=False)
    amount = Column(String(20), nullable=False)  # Decimal as string
    currency = Column(String(3), default='USD')
    
    # Status
    status = Column(String(20), default='pending')  # 'pending', 'paid', 'failed', 'refunded'
    
    # Stripe Integration
    stripe_payment_intent_id = Column(String(255))
    stripe_invoice_id = Column(String(255))
    stripe_charge_id = Column(String(255))
    
    # Timing
    due_date = Column(DateTime, nullable=False)
    paid_at = Column(DateTime, nullable=True)
    
    # Metadata
    metadata_json = Column("metadata", Text)  # JSON data stored under the reserved column name

    def __init__(self, *args, metadata=None, **kwargs):
        if metadata is not None:
            kwargs["metadata_json"] = metadata
        super().__init__(*args, **kwargs)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship('Organization', back_populates='billing')
    customer = relationship('User', back_populates='billing')
    business = relationship('BusinessProfile', back_populates='billing')


class Subscription(Base):
    __tablename__ = 'subscriptions'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey('organizations.id'), nullable=False)
    plan_id = Column(String(50), nullable=False)
    status = Column(String(50), default='pending')
    start_date = Column(DateTime, default=datetime.utcnow)
    renewal_date = Column(DateTime, nullable=True)
    provider_customer_id = Column(String(255), nullable=True)
    provider_subscription_id = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = relationship('Organization', back_populates='subscriptions')


class UsageLimit(Base):
    __tablename__ = 'usage_limits'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey('organizations.id'), nullable=False)
    feature = Column(String(100), nullable=False)
    limit = Column(Integer, nullable=False, default=0)
    current_usage = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = relationship('Organization', back_populates='usage_limits')