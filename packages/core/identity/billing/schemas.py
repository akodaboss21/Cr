"""
Billing Module - Pydantic Schemas
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class BillingBase(BaseModel):
    invoice_id: str
    description: str
    amount: str
    currency: str = "USD"
    status: str = "pending"  # 'pending', 'paid', 'failed', 'refunded'
    due_date: datetime
    metadata: Optional[str] = None

class BillingCreate(BillingBase):
    pass

class BillingUpdate(BaseModel):
    invoice_id: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[str] = None
    currency: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[datetime] = None
    stripe_payment_intent_id: Optional[str] = None
    stripe_invoice_id: Optional[str] = None
    stripe_charge_id: Optional[str] = None
    paid_at: Optional[datetime] = None
    metadata: Optional[str] = None

class BillingResponse(BillingBase):
    id: str
    organization_id: str
    customer_id: str
    business_id: str
    stripe_payment_intent_id: Optional[str] = None
    stripe_invoice_id: Optional[str] = None
    stripe_charge_id: Optional[str] = None
    paid_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True


class SubscriptionCreate(BaseModel):
    plan_id: str
    success_url: str
    cancel_url: str


class SubscriptionResponse(BaseModel):
    id: str
    organization_id: str
    plan_id: str
    status: str
    start_date: datetime
    renewal_date: Optional[datetime] = None
    provider_customer_id: Optional[str] = None
    provider_subscription_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class UsageLimitResponse(BaseModel):
    feature: str
    limit: int
    current_usage: int

    class Config:
        orm_mode = True