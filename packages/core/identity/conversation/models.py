"""
Conversation Module - Data Models
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from packages.core.database import Base

class Conversation(Base):
    __tablename__ = 'conversations'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey('organizations.id'), nullable=False)
    business_id = Column(String(36), ForeignKey('business_profiles.id'))
    participant_id = Column(String(36), ForeignKey('users.id'))
    
    # Conversation Details
    title = Column(String(255))
    status = Column(String(50), default='active')  # 'active', 'closed', 'archived'
    channel = Column(String(50), default='web')  # 'web', 'mobile', 'api'
    ai_provider = Column(String(50))
    model = Column(String(100))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_message_at = Column(DateTime, nullable=True)
    
    # Relationships
    organization = relationship('Organization', back_populates='conversations')
    business = relationship('BusinessProfile', back_populates='conversations')
    participant = relationship('User', back_populates='conversations')
    messages = relationship('Message', back_populates='conversation')

class Message(Base):
    __tablename__ = 'messages'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey('conversations.id'), nullable=False)
    
    # Message Content
    content = Column(Text, nullable=False)
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    
    # Metadata
    timestamp = Column(DateTime, default=datetime.utcnow)
    ai_provider = Column(String(50))
    model = Column(String(100))
    tokens_used = Column(Integer)
    
    # Relationships
    conversation = relationship('Conversation', back_populates='messages')