import json
from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import Column, String, create_engine
from sqlalchemy.orm import relationship, sessionmaker

from packages.core.database import Base
from packages.core.identity.billing.models import Subscription, UsageLimit
from packages.core.identity.billing.payment_provider import DummyPaymentProvider
from packages.core.identity.billing.plans import get_plan_by_id

class Organization(Base):
    __tablename__ = 'organizations'
    id = Column(String(36), primary_key=True)
    billing = relationship('Billing', back_populates='organization')
    subscriptions = relationship('Subscription', back_populates='organization')
    usage_limits = relationship('UsageLimit', back_populates='organization')

class User(Base):
    __tablename__ = 'users'
    id = Column(String(36), primary_key=True)
    billing = relationship('Billing', back_populates='customer')

class BusinessProfile(Base):
    __tablename__ = 'business_profiles'
    id = Column(String(36), primary_key=True)
    billing = relationship('Billing', back_populates='business')
from packages.core.identity.billing.services import (
    create_subscription_record,
    ensure_usage_allowed,
    get_active_subscription,
    increment_usage,
    sync_usage_limits_for_plan,
)


@pytest.fixture
def memory_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    return Session()


def test_plan_definitions_exist():
    starter = get_plan_by_id("starter")
    assert starter is not None
    assert starter["name"] == "Starter"
    assert starter["price"] == 29.0


def test_dummy_payment_provider_checkout():
    provider = DummyPaymentProvider()
    customer = provider.create_customer("test@example.com", "Test Owner")
    assert customer["email"] == "test@example.com"

    checkout = provider.create_checkout(
        customer_id=customer["id"],
        price_id="price_123",
        success_url="https://example.com/success",
        cancel_url="https://example.com/cancel",
    )
    assert checkout["status"] == "open"
    assert checkout["url"] == "https://example.com/success"


def test_create_subscription_creates_usage_limits(memory_db):
    organization_id = str(uuid4())
    subscription = create_subscription_record(
        db=memory_db,
        organization_id=organization_id,
        plan_id="starter",
        status="active",
        renewal_date=datetime.utcnow() + timedelta(days=30),
        provider_customer_id="cust_123",
        provider_subscription_id="sub_123",
    )

    assert subscription.organization_id == organization_id
    assert subscription.plan_id == "starter"

    usage_limits = memory_db.query(UsageLimit).filter(UsageLimit.organization_id == organization_id).all()
    assert len(usage_limits) == 3
    assert any(limit.feature == "ai_requests" for limit in usage_limits)


def test_usage_limit_reached_raises(memory_db):
    organization_id = str(uuid4())
    usage_limit = UsageLimit(
        id=str(uuid4()),
        organization_id=organization_id,
        feature="ai_requests",
        limit=1,
        current_usage=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    memory_db.add(usage_limit)
    memory_db.commit()

    with pytest.raises(HTTPException) as exc_info:
        ensure_usage_allowed(memory_db, organization_id, "ai_requests", amount=1)

    assert exc_info.value.status_code == 402


def test_expired_subscription_returns_none(memory_db):
    organization_id = str(uuid4())
    subscription = Subscription(
        id=str(uuid4()),
        organization_id=organization_id,
        plan_id="pro",
        status="cancelled",
        start_date=datetime.utcnow() - timedelta(days=60),
        renewal_date=datetime.utcnow() - timedelta(days=30),
        provider_customer_id="cust_123",
        provider_subscription_id="sub_123",
        created_at=datetime.utcnow() - timedelta(days=60),
        updated_at=datetime.utcnow() - timedelta(days=30),
    )
    memory_db.add(subscription)
    memory_db.commit()

    active = get_active_subscription(memory_db, organization_id)
    assert active is None


def test_increment_usage_updates_current_usage(memory_db):
    organization_id = str(uuid4())
    usage_limit = UsageLimit(
        id=str(uuid4()),
        organization_id=organization_id,
        feature="ai_tokens",
        limit=100,
        current_usage=20,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    memory_db.add(usage_limit)
    memory_db.commit()

    updated_limit = increment_usage(memory_db, organization_id, "ai_tokens", amount=10)
    assert updated_limit.current_usage == 30
