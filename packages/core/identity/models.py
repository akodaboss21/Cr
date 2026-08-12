"""
Identity Module - Data Models
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from packages.core.database import Base

# Domain model imports are intentionally omitted here to avoid importing
# many submodules at module-import time which can create mapper ordering
# issues. Relationships reference target class names as strings.

class Organization(Base):
    __tablename__ = 'organizations'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = relationship('User', back_populates='organization')
    business_profile = relationship('BusinessProfile', back_populates='organization')
    conversations = relationship('Conversation', back_populates='organization')
    bookings = relationship('Booking', back_populates='organization')
    crm_data = relationship('CRM', back_populates='organization')
    notifications = relationship('Notification', back_populates='organization')
    analytics = relationship('Analytics', back_populates='organization')
    billing = relationship('Billing', back_populates='organization')
    subscriptions = relationship('Subscription', back_populates='organization')
    usage_limits = relationship('UsageLimit', back_populates='organization')
    background_workers = relationship('BackgroundWorker', back_populates='organization')
    background_jobs = relationship('BackgroundJob', back_populates='organization')
    organization_invitations = relationship('OrganizationInvitation', back_populates='organization')
    integrations = relationship('Integration', back_populates='organization')
    events = relationship('Event', back_populates='organization')
    event_subscribers = relationship('EventSubscriber', back_populates='organization')
    # AI gateway relationships
    ai_providers = relationship('AIProvider', back_populates='organization')
    prompt_templates = relationship('PromptTemplate', back_populates='organization')
    ai_usage = relationship('AIUsage', back_populates='organization')

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

class User(Base):
    __tablename__ = 'users'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey('organizations.id'), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(20))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship('Organization', back_populates='users')
    business_profile = relationship('BusinessProfile', back_populates='owner')
    conversations = relationship('Conversation', back_populates='participant')
    bookings = relationship('Booking', back_populates='customer')
    crm_data = relationship('CRM', back_populates='customer', foreign_keys='CRM.customer_id')
    notifications = relationship('Notification', back_populates='recipient_user')
    analytics = relationship('Analytics', back_populates='user')
    billing = relationship('Billing', back_populates='customer')
    event_subscriptions = relationship('EventSubscriber', back_populates='user')

class AuditLog(Base):
    __tablename__ = 'audit_logs'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey('organizations.id'), nullable=True)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=True)
    request_id = Column(String(128), nullable=False)
    event = Column(String(128), nullable=False)
    path = Column(String(512), nullable=False)
    method = Column(String(16), nullable=False)
    status_code = Column(Integer, nullable=False)
    client_ip = Column(String(45), nullable=True)
    user_agent = Column(String(512), nullable=True)
    details = Column(String(1024), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    organization = relationship('Organization')
    user = relationship('User')

class Role(Base):
    __tablename__ = 'roles'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255))
    
    # Association table
    permissions = relationship('Permission', secondary='role_permissions', back_populates='roles')

class Permission(Base):
    __tablename__ = 'permissions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255))
    
    # Association table
    roles = relationship('Role', secondary='role_permissions', back_populates='permissions')

class RolePermission(Base):
    __tablename__ = 'role_permissions'
    
    role_id = Column(Integer, ForeignKey('roles.id'), primary_key=True)
    permission_id = Column(Integer, ForeignKey('permissions.id'), primary_key=True)

class OrganizationInvitation(Base):
    __tablename__ = 'organization_invitations'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey('organizations.id'), nullable=False)
    email = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)
    token = Column(String(128), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    used = Column(Boolean, default=False)
    
    organization = relationship('Organization', back_populates='organization_invitations')