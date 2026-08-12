"""
Knowledge Module - Data Models
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from packages.core.database import Base

class Knowledge(Base):
    __tablename__ = 'knowledge'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey('organizations.id'), nullable=False)
    
    # Knowledge Content
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    content_type = Column(String(50))  # 'text', 'pdf', 'html', 'url'
    
    # Metadata
    source_url = Column(String(255))
    tags = Column(Text)
    category = Column(String(100))
    embedding_vector = Column(Text)  # JSON array
    processed = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship('Organization')
    embedding = relationship('KnowledgeEmbedding', back_populates='knowledge', cascade='all, delete-orphan')

class KnowledgeEmbedding(Base):
    __tablename__ = 'knowledge_embeddings'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    knowledge_id = Column(String(36), ForeignKey('knowledge.id'), nullable=False)
    embedding_vector = Column(Text, nullable=False)
    
    knowledge = relationship('Knowledge', back_populates='embedding')