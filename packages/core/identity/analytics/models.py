"""
Analytics Module - Data Models

This module defines the data models for tracking customer analytics, lead metrics,
pipeline metrics, and engagement metrics for the Carai CRM system.
"""
from sqlalchemy import Column, Integer, DateTime, ForeignKey, String, func
from sqlalchemy.orm import relationship
from packages.core.database import Base

class Analytics(Base):
    __tablename__ = 'analytics'

    id = Column(Integer, primary_key=True)
    organization_id = Column(String(36), ForeignKey('organizations.id'), nullable=True)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=True)
    business_id = Column(String(36), ForeignKey('business_profiles.id'), nullable=True)
    total_customers = Column(Integer, default=0)
    new_leads = Column(Integer, default=0)
    conversion_rate = Column(Integer, default=0)
    repeat_customers = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    organization = relationship('Organization', back_populates='analytics')
    user = relationship('User', back_populates='analytics')
    business = relationship('BusinessProfile', back_populates='analytics')

class LeadMetrics(Base):
    __tablename__ = 'lead_metrics'

    id = Column(Integer, primary_key=True)
    total_leads = Column(Integer, default=0)
    qualified_leads = Column(Integer, default=0)
    conversion_velocity = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class PipelineMetrics(Base):
    __tablename__ = 'pipeline_metrics'

    id = Column(Integer, primary_key=True)
    lead_to_customer_ratio = Column(Integer, default=0)
    average_lead_age = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class EngagementMetrics(Base):
    __tablename__ = 'engagement_metrics'

    id = Column(Integer, primary_key=True)
    active_customers = Column(Integer, default=0)
    returning_customers = Column(Integer, default=0)
    last_interaction_date = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())