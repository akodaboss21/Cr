from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from uuid import uuid4

from packages.core.config import settings


class PaymentProvider(ABC):
    """Abstract payment provider interface."""

    @abstractmethod
    def create_customer(self, email: str, name: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        raise NotImplementedError()

    @abstractmethod
    def create_checkout(
        self,
        customer_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        raise NotImplementedError()

    @abstractmethod
    def verify_payment(self, payload: bytes, sig_header: str, webhook_secret: Optional[str] = None) -> Any:
        raise NotImplementedError()

    @abstractmethod
    def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        raise NotImplementedError()

    @abstractmethod
    def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        raise NotImplementedError()


class StripePaymentProvider(PaymentProvider):
    def __init__(self):
        try:
            import stripe
        except ImportError as exc:
            raise RuntimeError("Stripe is not installed") from exc

        if not settings.STRIPE_SECRET_KEY:
            raise RuntimeError("Stripe secret key is not configured")

        self.stripe = stripe
        self.stripe.api_key = settings.STRIPE_SECRET_KEY

    def create_customer(self, email: str, name: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        customer = self.stripe.Customer.create(
            email=email,
            name=name,
            metadata=metadata or {}
        )
        return {
            "id": customer.id,
            "email": customer.email,
            "name": customer.name,
            "metadata": dict(customer.metadata or {}),
        }

    def create_checkout(
        self,
        customer_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not price_id:
            raise ValueError("Price ID is required for Stripe checkout")

        session = self.stripe.checkout.Session.create(
            customer=customer_id,
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
            subscription_data={"metadata": metadata or {}},
            payment_method_types=["card"],
        )
        return {
            "id": session.id,
            "url": session.url,
            "status": session.status,
        }

    def verify_payment(self, payload: bytes, sig_header: str, webhook_secret: Optional[str] = None) -> Any:
        webhook_secret = webhook_secret or settings.STRIPE_WEBHOOK_SECRET
        if not webhook_secret:
            raise RuntimeError("Stripe webhook secret is not configured")
        return self.stripe.Webhook.construct_event(payload, sig_header, webhook_secret)

    def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        subscription = self.stripe.Subscription.delete(subscription_id)
        return {"id": subscription.id, "status": subscription.status}

    def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        subscription = self.stripe.Subscription.retrieve(subscription_id)
        return {
            "id": subscription.id,
            "status": subscription.status,
            "current_period_end": subscription.current_period_end,
            "current_period_start": subscription.current_period_start,
            "customer": subscription.customer,
            "plan": getattr(subscription, "plan", None),
        }


class DummyPaymentProvider(PaymentProvider):
    def create_customer(self, email: str, name: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return {
            "id": f"dummy-{uuid4()}",
            "email": email,
            "name": name,
            "metadata": metadata or {},
        }

    def create_checkout(
        self,
        customer_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return {
            "id": f"dummy-checkout-{uuid4()}",
            "url": success_url,
            "status": "open",
        }

    def verify_payment(self, payload: bytes, sig_header: str, webhook_secret: Optional[str] = None) -> Any:
        return {
            "type": "payment.mocked",
            "data": {"object": {"id": "dummy-checkout", "status": "success"}},
        }

    def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        return {"id": subscription_id, "status": "canceled"}

    def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        return {"id": subscription_id, "status": "canceled"}


def get_payment_provider() -> PaymentProvider:
    if settings.STRIPE_SECRET_KEY:
        return StripePaymentProvider()
    return DummyPaymentProvider()
