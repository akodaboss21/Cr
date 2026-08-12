from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from packages.core.identity.billing.models import Subscription, UsageLimit
from packages.core.identity.billing.plans import get_plan_by_id

UNLIMITED_VALUE = -1


def get_active_subscription(db: Session, organization_id: str) -> Optional[Subscription]:
    return db.query(Subscription).filter(
        Subscription.organization_id == organization_id,
        Subscription.status.in_(["active", "trialing"]),
    ).order_by(Subscription.created_at.desc()).first()


def get_plan_for_organization(db: Session, organization_id: str) -> Dict[str, object]:
    subscription = get_active_subscription(db, organization_id)
    if subscription:
        plan = get_plan_by_id(subscription.plan_id)
        if plan:
            return plan
    free_plan = get_plan_by_id("free")
    if free_plan:
        sync_usage_limits_for_plan(db, organization_id, free_plan["plan_id"])
        return free_plan
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Unable to resolve billing plan for organization",
    )


def create_subscription_record(
    db: Session,
    organization_id: str,
    plan_id: str,
    status: str = "pending",
    start_date: Optional[datetime] = None,
    renewal_date: Optional[datetime] = None,
    provider_customer_id: Optional[str] = None,
    provider_subscription_id: Optional[str] = None,
) -> Subscription:
    subscription = Subscription(
        id=str(uuid4()),
        organization_id=organization_id,
        plan_id=plan_id,
        status=status,
        start_date=start_date or datetime.utcnow(),
        renewal_date=renewal_date,
        provider_customer_id=provider_customer_id,
        provider_subscription_id=provider_subscription_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    sync_usage_limits_for_plan(db, organization_id, plan_id)
    return subscription


def sync_usage_limits_for_plan(db: Session, organization_id: str, plan_id: str) -> List[UsageLimit]:
    plan = get_plan_by_id(plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unknown billing plan",
        )

    limits = []
    for feature, limit_value in plan["limits"].items():
        usage_limit = db.query(UsageLimit).filter(
            UsageLimit.organization_id == organization_id,
            UsageLimit.feature == feature,
        ).first()
        if usage_limit:
            usage_limit.limit = limit_value
            usage_limit.updated_at = datetime.utcnow()
        else:
            usage_limit = UsageLimit(
                id=str(uuid4()),
                organization_id=organization_id,
                feature=feature,
                limit=limit_value,
                current_usage=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(usage_limit)

        limits.append(usage_limit)

    db.commit()
    return limits


def get_usage_limits_for_organization(db: Session, organization_id: str) -> List[UsageLimit]:
    return db.query(UsageLimit).filter(
        UsageLimit.organization_id == organization_id
    ).all()


def ensure_usage_allowed(db: Session, organization_id: str, feature: str, amount: int = 1) -> None:
    usage_limit = db.query(UsageLimit).filter(
        UsageLimit.organization_id == organization_id,
        UsageLimit.feature == feature,
    ).first()

    if not usage_limit:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Usage record not found for feature '{feature}'.",
        )

    if usage_limit.limit != UNLIMITED_VALUE and usage_limit.current_usage + amount > usage_limit.limit:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=(
                f"Usage limit reached for '{feature}'. "
                f"Current: {usage_limit.current_usage}, limit: {usage_limit.limit}."
            ),
        )


def increment_usage(db: Session, organization_id: str, feature: str, amount: int = 1) -> UsageLimit:
    usage_limit = db.query(UsageLimit).filter(
        UsageLimit.organization_id == organization_id,
        UsageLimit.feature == feature,
    ).first()

    if not usage_limit:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Usage limit record for '{feature}' not found."
        )

    if usage_limit.limit != UNLIMITED_VALUE and usage_limit.current_usage + amount > usage_limit.limit:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=(
                f"Usage limit reached for '{feature}'. "
                f"Current: {usage_limit.current_usage}, limit: {usage_limit.limit}."
            ),
        )

    usage_limit.current_usage += amount
    usage_limit.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(usage_limit)
    return usage_limit


def mark_subscription_cancelled(db: Session, subscription: Subscription) -> Subscription:
    subscription.status = "cancelled"
    subscription.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(subscription)
    return subscription
