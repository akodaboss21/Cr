from typing import Dict, List, Optional

from packages.core.config import settings

PLAN_DEFINITIONS: List[Dict[str, object]] = [
    {
        "plan_id": "free",
        "name": "Free",
        "price": 0.0,
        "billing_period": "monthly",
        "features": [
            "Limited conversations",
            "Limited AI messages",
            "Basic support"
        ],
        "limits": {
            "conversations": 1000,
            "ai_requests": 1000,
            "ai_tokens": 50000
        },
        "provider_price_env": None,
    },
    {
        "plan_id": "starter",
        "name": "Starter",
        "price": 29.0,
        "billing_period": "monthly",
        "features": [
            "More conversations",
            "Basic analytics",
            "Priority email support"
        ],
        "limits": {
            "conversations": 5000,
            "ai_requests": 5000,
            "ai_tokens": 200000
        },
        "provider_price_env": "STRIPE_PRICE_ID_STARTER",
    },
    {
        "plan_id": "pro",
        "name": "Pro",
        "price": 99.0,
        "billing_period": "monthly",
        "features": [
            "Advanced AI",
            "More integrations",
            "Advanced analytics"
        ],
        "limits": {
            "conversations": 20000,
            "ai_requests": 20000,
            "ai_tokens": 1000000
        },
        "provider_price_env": "STRIPE_PRICE_ID_PRO",
    },
    {
        "plan_id": "business",
        "name": "Business",
        "price": 299.0,
        "billing_period": "monthly",
        "features": [
            "Multiple locations",
            "Advanced features",
            "Dedicated support"
        ],
        "limits": {
            "conversations": -1,
            "ai_requests": -1,
            "ai_tokens": -1
        },
        "provider_price_env": "STRIPE_PRICE_ID_BUSINESS",
    },
]

def get_available_plans() -> List[Dict[str, object]]:
    return [plan.copy() for plan in PLAN_DEFINITIONS]


def get_plan_by_id(plan_id: str) -> Optional[Dict[str, object]]:
    for plan in PLAN_DEFINITIONS:
        if plan["plan_id"] == plan_id:
            return plan.copy()
    return None


def resolve_provider_price_id(plan: Dict[str, object]) -> Optional[str]:
    provider_price_env = plan.get("provider_price_env")
    if provider_price_env:
        return getattr(settings, provider_price_env, None)
    return None
