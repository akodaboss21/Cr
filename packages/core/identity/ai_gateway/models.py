"""
AI Gateway Module - Data Models
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Boolean
from sqlalchemy.orm import relationship, backref
from datetime import datetime
import uuid

from packages.core.database import Base

class AIProvider(Base):
    __tablename__ = 'ai_providers'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(String(36), ForeignKey('organizations.id'), nullable=False)
    name = Column(String(100), nullable=False)
    api_url = Column(String(255), nullable=False)
    api_key = Column(String(255))
    model = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = relationship('Organization', back_populates='ai_providers')

class PromptTemplate(Base):
    __tablename__ = 'prompt_templates'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey('organizations.id'), nullable=False)
    
    # Template Details
    name = Column(String(255), nullable=False)
    description = Column(Text)
    template = Column(Text, nullable=False)
    variables = Column(Text)  # JSON array of variable names
    
    # Metadata
    category = Column(String(100))
    version = Column(String(20), default='1.0')
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship('Organization', back_populates='prompt_templates')

class AIUsage(Base):
    __tablename__ = 'ai_usage'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey('organizations.id'), nullable=False)
    conversation_id = Column(String(36), ForeignKey('conversations.id'))
    
    # Usage Details
    provider = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    
    # Cost
    cost_usd = Column(String(20))  # Decimal as string
    
    # Metadata
    request_id = Column(String(100))
    response_time_ms = Column(Integer)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    organization = relationship('Organization', back_populates='ai_usage')
    conversation = relationship('Conversation', backref=backref('ai_usage', lazy='select'))