"""
Integration Module - Data Models
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from packages.core.database import Base

class Integration(Base):
    __tablename__ = 'integrations'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey('organizations.id'), nullable=False)
    
    # Integration Details
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)  # 'google', 'meta', 'stripe', etc.
    
    # Configuration
    config = Column(Text)  # JSON data
    is_active = Column(Boolean, default=True)
    
    # Status
    last_sync = Column(DateTime, nullable=True)
    sync_status = Column(String(20), default='pending')  # 'pending', 'success', 'failed'
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship('Organization', back_populates='integrations')