from pydantic import BaseModel
from datetime import datetime

class AnalyticsSchema(BaseModel):
    id: str
    organization_id: str
    user_id: str | None
    business_id: str | None
    event_type: str
    event_data: dict
    value: int
    duration_ms: int
    source: str
    user_agent: str | None
    ip_address: str | None
    timestamp: datetime
    created_at: datetime
    organization: dict | None
    user: dict | None
    business: dict | None

class LeadMetricsSchema(BaseModel):
    id: int
    total_leads: int
    qualified_leads: int
    conversion_velocity: int
    created_at: datetime
    updated_at: datetime

class PipelineMetricsSchema(BaseModel):
    id: int
    lead_to_customer_ratio: int
    average_lead_age: int
    created_at: datetime
    updated_at: datetime

class EngagementMetricsSchema(BaseModel):
    id: int
    active_customers: int
    returning_customers: int
    last_interaction_date: datetime | None
    created_at: datetime
    updated_at: datetime