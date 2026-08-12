"""
Background Workers Module - Data Models
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from packages.core.database import Base

class BackgroundWorker(Base):
    __tablename__ = 'background_workers'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey('organizations.id'), nullable=False)
    
    # Worker Details
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)  # 'pyrunner', 'celery', etc.
    
    # Configuration
    config = Column(Text)  # JSON data
    is_active = Column(Boolean, default=True)
    
    # Status
    status = Column(String(20), default='idle')  # 'idle', 'running', 'error', 'stopped'
    
    # Performance
    tasks_processed = Column(Integer, default=0)
    tasks_failed = Column(Integer, default=0)
    last_task_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship('Organization', back_populates='background_workers')
    jobs = relationship('BackgroundJob', back_populates='worker')

class BackgroundJob(Base):
    __tablename__ = 'background_jobs'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey('organizations.id'), nullable=False)
    worker_id = Column(String(36), ForeignKey('background_workers.id'))
    
    # Job Details
    task_type = Column(String(100), nullable=False)
    task_data = Column(Text)  # JSON data
    
    # Status
    status = Column(String(20), default='pending')  # 'pending', 'running', 'completed', 'failed', 'retried'
    
    # Retry
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Timing
    scheduled_at = Column(DateTime, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Result
    result = Column(Text)  # JSON data
    error = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship('Organization', back_populates='background_jobs')
    worker = relationship('BackgroundWorker', back_populates='jobs')