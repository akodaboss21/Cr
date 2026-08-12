"""
Billing Module - Controller
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from typing import List, Optional
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime

from packages.core.database import get_db
from packages.core.security import get_current_user
from packages.core.identity.billing.models import Billing
from packages.core.identity.billing.models import Subscription
from packages.core.identity.billing.payment_provider import get_payment_provider
from packages.core.identity.billing.plans import get_available_plans, get_plan_by_id, resolve_provider_price_id
from packages.core.identity.billing.services import (
    create_subscription_record,
    get_active_subscription,
    get_usage_limits_for_organization,
    mark_subscription_cancelled,
    sync_usage_limits_for_plan,
)
from packages.core.identity.billing.schemas import (
    BillingCreate, BillingUpdate, BillingResponse,
    SubscriptionCreate, SubscriptionResponse, UsageLimitResponse,
)

router = APIRouter(tags=["billing"])


@router.get("/plans/", response_model=List[dict])
async def list_plans():
    return get_available_plans()


@router.get("/subscriptions/active", response_model=Optional[SubscriptionResponse])
async def get_active_subscription_endpoint(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    subscription = get_active_subscription(db, current_user["organization_id"])
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )
    return SubscriptionResponse.from_orm(subscription)


@router.post("/subscriptions/checkout", response_model=dict)
async def create_subscription_checkout(
    subscription_create: SubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    plan = get_plan_by_id(subscription_create.plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Plan not found"
        )

    if plan["price"] == 0.0:
        subscription = create_subscription_record(
            db=db,
            organization_id=current_user["organization_id"],
            plan_id=plan["plan_id"],
            status="active",
            start_date=datetime.utcnow(),
            renewal_date=datetime.utcnow(),
        )
        return {
            "subscription_id": subscription.id,
            "status": subscription.status,
            "plan_id": subscription.plan_id,
        }

    price_id = resolve_provider_price_id(plan)
    if not price_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Payment provider setup incomplete"
        )

    provider = get_payment_provider()
    customer = provider.create_customer(
        email=current_user.get("email", ""),
        name=current_user.get("name", ""),
        metadata={"organization_id": current_user["organization_id"], "plan_id": plan["plan_id"]},
    )

    checkout = provider.create_checkout(
        customer_id=customer["id"],
        price_id=price_id,
        success_url=subscription_create.success_url,
        cancel_url=subscription_create.cancel_url,
        metadata={"organization_id": current_user["organization_id"], "plan_id": plan["plan_id"]},
    )

    subscription = create_subscription_record(
        db=db,
        organization_id=current_user["organization_id"],
        plan_id=plan["plan_id"],
        status="pending",
        start_date=datetime.utcnow(),
        renewal_date=None,
        provider_customer_id=customer["id"],
    )

    return {
        "subscription_id": subscription.id,
        "checkout_url": checkout["url"],
        "checkout_session_id": checkout["id"],
        "status": subscription.status,
    }


@router.post("/subscriptions/{subscription_id}/cancel", response_model=SubscriptionResponse)
async def cancel_subscription(
    subscription_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    subscription = db.query(Subscription).filter(
        Subscription.id == subscription_id,
        Subscription.organization_id == current_user["organization_id"],
    ).first()
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )

    provider = get_payment_provider()
    provider.cancel_subscription(subscription.provider_subscription_id)
    subscription.status = "cancelled"
    subscription.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(subscription)
    return SubscriptionResponse.from_orm(subscription)


@router.get("/usage/limits", response_model=List[UsageLimitResponse])
async def list_usage_limits(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    limits = get_usage_limits_for_organization(db, current_user["organization_id"])
    return [UsageLimitResponse.from_orm(limit) for limit in limits]


@router.post("/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    provider = get_payment_provider()

    try:
        event = provider.verify_payment(payload, sig_header)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "checkout.session.completed":
        organization_id = data.get("metadata", {}).get("organization_id")
        plan_id = data.get("metadata", {}).get("plan_id")
        customer_id = data.get("customer")
        subscription_id = data.get("subscription")

        if organization_id and subscription_id:
            subscription = db.query(Subscription).filter(
                Subscription.organization_id == organization_id,
                Subscription.provider_customer_id == customer_id,
                Subscription.status == "pending",
            ).order_by(Subscription.created_at.desc()).first()
            if subscription:
                subscription.status = "active"
                subscription.provider_subscription_id = subscription_id
                subscription.renewal_date = datetime.fromtimestamp(data.get("current_period_end", datetime.utcnow().timestamp()))
                subscription.updated_at = datetime.utcnow()
                db.commit()
                db.refresh(subscription)

    elif event_type in {"customer.subscription.updated", "invoice.payment_succeeded"}:
        provider_sub_id = data.get("id")
        subscription = db.query(Subscription).filter(
            Subscription.provider_subscription_id == provider_sub_id
        ).first()
        if subscription:
            subscription.status = data.get("status", subscription.status)
            subscription.renewal_date = datetime.fromtimestamp(data.get("current_period_end", subscription.renewal_date.timestamp() if subscription.renewal_date else datetime.utcnow().timestamp()))
            subscription.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(subscription)

    elif event_type in {"invoice.payment_failed", "customer.subscription.deleted"}:
        provider_sub_id = data.get("id")
        subscription = db.query(Subscription).filter(
            Subscription.provider_subscription_id == provider_sub_id
        ).first()
        if subscription:
            subscription.status = "past_due" if event_type == "invoice.payment_failed" else "cancelled"
            subscription.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(subscription)

    return {"received": True}

@router.post("/", response_model=BillingResponse)
async def create_billing(
    billing_create: BillingCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new billing entry"""
    # Verify user has permission to create billing entry
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Create billing entry
    db_billing = Billing(
        id=str(uuid4()),
        organization_id=current_user["organization_id"],
        customer_id=current_user["user_id"],
        business_id=billing_create.business_id,
        invoice_id=billing_create.invoice_id,
        description=billing_create.description,
        amount=billing_create.amount,
        currency=billing_create.currency,
        status=billing_create.status,
        due_date=billing_create.due_date,
        stripe_payment_intent_id=billing_create.stripe_payment_intent_id,
        stripe_invoice_id=billing_create.stripe_invoice_id,
        stripe_charge_id=billing_create.stripe_charge_id,
        paid_at=billing_create.paid_at,
        metadata=billing_create.metadata,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(db_billing)
    db.commit()
    db.refresh(db_billing)
    
    return BillingResponse.from_orm(db_billing)

@router.get("/", response_model=List[BillingResponse])
async def get_billing(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """Get a list of billing entries"""
    # Verify user has permission
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    billing_entries = db.query(Billing).filter(
        Billing.organization_id == current_user["organization_id"]
    ).offset(skip).limit(limit).all()
    
    return [BillingResponse.from_orm(billing) for billing in billing_entries]

@router.get("/{billing_id}", response_model=BillingResponse)
async def get_billing_entry(
    billing_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific billing entry"""
    # Verify user has permission
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    billing = db.query(Billing).filter(
        Billing.id == billing_id,
        Billing.organization_id == current_user["organization_id"]
    ).first()
    
    if not billing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Billing entry not found"
        )
    
    return BillingResponse.from_orm(billing)

@router.put("/{billing_id}", response_model=BillingResponse)
async def update_billing(
    billing_id: str,
    billing_update: BillingUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a billing entry"""
    # Verify user has permission
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    billing = db.query(Billing).filter(
        Billing.id == billing_id,
        Billing.organization_id == current_user["organization_id"]
    ).first()
    
    if not billing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Billing entry not found"
        )
    
    # Update fields
    for field, value in billing_update.dict(exclude_unset=True).items():
        setattr(billing, field, value)
    
    billing.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(billing)
    
    return BillingResponse.from_orm(billing)

@router.delete("/{billing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_billing(
    billing_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a billing entry"""
    # Verify user has permission
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    billing = db.query(Billing).filter(
        Billing.id == billing_id,
        Billing.organization_id == current_user["organization_id"]
    ).first()
    
    if not billing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Billing entry not found"
        )
    
    db.delete(billing)
    db.commit()
    
    return None