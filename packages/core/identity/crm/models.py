from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from packages.core.database import Base

class CRM(Base):
    __tablename__ = 'crm'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey('organizations.id'), nullable=False)
    customer_id = Column(String(36), ForeignKey('users.id'))
    business_id = Column(String(36), ForeignKey('business_profiles.id'))

    # CRM Data
    name = Column(String(255), nullable=False)
    email = Column(String(255))
    phone = Column(String(20))
    company = Column(String(255))

    # Lead Information
    source = Column(String(100))  # 'website', 'phone', 'referral', etc.
    status = Column(String(50), default='lead')  # 'lead', 'customer', 'prospect', 'lost'
    score = Column(Integer, default=0)

    # Notes and Tags
    notes = Column(Text)
    tags = Column(Text)  # JSON array

    # Assignment
    assigned_to = Column(String(36), ForeignKey('users.id'))

    # Pipeline
    pipeline_stage = Column(String(100))
    next_followup = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    organization = relationship('Organization', back_populates='crm_data')
    customer = relationship('User', back_populates='crm_data', foreign_keys=[customer_id])
    business = relationship('BusinessProfile', back_populates='crm_data')
    assignee = relationship('User', foreign_keys=[assigned_to])

    # Customer Profile Fields
    first_interaction = Column(DateTime, nullable=True)
    last_interaction = Column(DateTime, nullable=True)
    total_conversations = Column(Integer, default=0)
    services_requested = Column(Text)  # JSON array
    bookings = Column(Text)  # JSON array

    # AI Memory
    preferences = Column(Text)  # JSON object
    notes_history = Column(Text)  # JSON array
    important_details = Column(Text)  # JSON object