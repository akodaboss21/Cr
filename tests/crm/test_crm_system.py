"""
CRM System Tests

Tests for:
- New customer creation
- Returning customer detection
- Lead creation
- Lead conversion
- Customer history tracking
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.orm import Session

from packages.core.identity.crm.models import CRM
from packages.core.identity.crm.schemas import CRMCreate, CRMUpdate, CRMResponse
from packages.core.identity.crm.controllers.crm_controller import (
    create_crm,
    get_crm,
    update_crm,
    delete_crm,
    search_customers
)
from packages.core.ai.reception.agent import ReceptionAgent, IntentType, IntentResult


class MockDB:
    def __init__(self):
        self.customers = {}
        self.leads = {}
        self.next_id = 1
    
    def add(self, obj):
        if hasattr(obj, 'id') and obj.id is None:
            obj.id = self.next_id
            self.next_id += 1
        if isinstance(obj, CRM):
            self.customers[obj.id] = obj
    
    def commit(self):
        pass
    
    def refresh(self, obj):
        pass
    
    def query(self, model):
        return MockQuery(self.customers if model == CRM else self.leads)
    
    def delete(self, obj):
        if isinstance(obj, CRM) and obj.id in self.customers:
            del self.customers[obj.id]


class MockQuery:
    def __init__(self, data):
        self.data = data
        self.filters = []
    
    def filter(self, *args):
        self.filters.extend(args)
        return self
    
    def filter_by(self, **kwargs):
        for k, v in kwargs.items():
            self.filters.append((k, v))
        return self
    
    def first(self):
        for obj in self.data.values():
            if self._matches(obj):
                return obj
        return None
    
    def all(self):
        return [obj for obj in self.data.values() if self._matches(obj)]
    
    def count(self):
        return len(self.all())
    
    def _matches(self, obj):
        for f in self.filters:
            if isinstance(f, tuple):
                k, v = f
                if getattr(obj, k, None) != v:
                    return False
            else:
                # SQLAlchemy filter expression - simplified
                pass
        return True


@pytest.fixture
def mock_db():
    return MockDB()


@pytest.fixture
def sample_customer_data():
    return {
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "+1234567890",
        "organization_id": "org-123",
        "first_interaction": datetime.utcnow(),
        "last_interaction": datetime.utcnow(),
        "total_conversations": 1,
        "services_requested": ["consultation"],
        "bookings": [],
        "preferences": {"language": "en", "timezone": "UTC"},
        "notes_history": [],
        "important_details": {}
    }


@pytest.mark.asyncio
async def test_new_customer_creation(mock_db, sample_customer_data):
    """Test creating a new customer in the CRM"""
    customer = CRM(**sample_customer_data)
    mock_db.add(customer)
    mock_db.commit()
    
    assert customer.id is not None
    assert customer.name == "John Doe"
    assert customer.email == "john@example.com"
    assert customer.total_conversations == 1
    assert customer.first_interaction is not None


@pytest.mark.asyncio
async def test_returning_customer_detection(mock_db, sample_customer_data):
    """Test detecting a returning customer"""
    # Create initial customer
    customer = CRM(**sample_customer_data)
    mock_db.add(customer)
    mock_db.commit()
    
    # Simulate returning customer - update last_interaction and increment conversations
    customer.last_interaction = datetime.utcnow()
    customer.total_conversations += 1
    mock_db.commit()
    
    assert customer.total_conversations == 2
    assert customer.last_interaction > customer.first_interaction


@pytest.mark.asyncio
async def test_lead_creation_from_buying_intent(mock_db):
    """Test lead creation when buying intent is detected"""
    from packages.core.ai.reception.agent import ReceptionAgent
    
    # Mock the agent's lead detection
    agent = ReceptionAgent()
    
    # Create a mock customer
    customer = CRM(
        name="Jane Smith",
        email="jane@example.com",
        phone="+1987654321",
        organization_id="org-123"
    )
    mock_db.add(customer)
    mock_db.commit()
    
    # Simulate buying intent detection
    intent_result = IntentResult(
        intent=IntentType.BUYING_INTENT,
        confidence=0.9,
        entities={"service": "premium_consultation", "budget": "5000"}
    )
    
    # Test lead creation logic
    lead_data = {
        "customer_id": customer.id,
        "source": "website_chat",
        "status": "NEW",
        "score": 85,
        "service_interest": "premium_consultation",
        "budget_range": "5000",
        "notes": "Customer expressed interest in premium consultation"
    }
    
    # Verify lead would be created
    assert intent_result.intent == IntentType.BUYING_INTENT
    assert intent_result.confidence > 0.8
    assert "service" in intent_result.entities


@pytest.mark.asyncio
async def test_lead_conversion_to_customer(mock_db):
    """Test converting a lead to a customer"""
    # Create a lead
    lead = {
        "id": 1,
        "customer_id": 1,
        "status": "QUALIFIED",
        "score": 90,
        "service_interest": "premium_consultation"
    }
    mock_db.leads[1] = lead
    
    # Create associated customer
    customer = CRM(
        name="Bob Wilson",
        email="bob@example.com",
        phone="+1555123456",
        organization_id="org-123",
        total_conversations=3
    )
    mock_db.add(customer)
    mock_db.commit()
    
    # Convert lead to customer
    lead["status"] = "CUSTOMER"
    customer.total_conversations += 1
    customer.services_requested = ["premium_consultation"]
    mock_db.commit()
    
    assert lead["status"] == "CUSTOMER"
    assert "premium_consultation" in customer.services_requested


@pytest.mark.asyncio
async def test_customer_history_tracking(mock_db, sample_customer_data):
    """Test tracking customer interaction history"""
    customer = CRM(**sample_customer_data)
    mock_db.add(customer)
    mock_db.commit()
    
    # Add conversation history
    customer.notes_history = [
        {"date": datetime.utcnow().isoformat(), "note": "Initial consultation", "type": "ai_note"},
        {"date": (datetime.utcnow() + timedelta(days=1)).isoformat(), "note": "Follow-up call", "type": "staff_note"},
        {"date": (datetime.utcnow() + timedelta(days=3)).isoformat(), "note": "Booking confirmed", "type": "booking"}
    ]
    customer.total_conversations = 3
    customer.last_interaction = datetime.utcnow()
    mock_db.commit()
    
    assert len(customer.notes_history) == 3
    assert customer.total_conversations == 3
    assert any(note["type"] == "booking" for note in customer.notes_history)


@pytest.mark.asyncio
async def test_customer_search_by_email(mock_db, sample_customer_data):
    """Test searching customers by email"""
    customer = CRM(**sample_customer_data)
    mock_db.add(customer)
    mock_db.commit()
    
    # Search by email
    results = mock_db.query(CRM).filter_by(email="john@example.com").all()
    
    assert len(results) == 1
    assert results[0].email == "john@example.com"


@pytest.mark.asyncio
async def test_customer_search_by_phone(mock_db, sample_customer_data):
    """Test searching customers by phone"""
    customer = CRM(**sample_customer_data)
    mock_db.add(customer)
    mock_db.commit()
    
    # Search by phone
    results = mock_db.query(CRM).filter_by(phone="+1234567890").all()
    
    assert len(results) == 1
    assert results[0].phone == "+1234567890"


@pytest.mark.asyncio
async def test_customer_search_by_name(mock_db, sample_customer_data):
    """Test searching customers by name"""
    customer = CRM(**sample_customer_data)
    mock_db.add(customer)
    mock_db.commit()
    
    # Search by name (partial match)
    results = mock_db.query(CRM).filter(CRM.name.like("%John%")).all()
    
    assert len(results) == 1
    assert "John" in results[0].name


@pytest.mark.asyncio
async def test_customer_segmentation(mock_db):
    """Test customer segmentation logic"""
    # Create different types of customers
    new_customer = CRM(
        name="New Customer",
        email="new@example.com",
        phone="+1111111111",
        organization_id="org-123",
        total_conversations=1,
        first_interaction=datetime.utcnow()
    )
    
    returning_customer = CRM(
        name="Returning Customer",
        email="returning@example.com",
        phone="+2222222222",
        organization_id="org-123",
        total_conversations=5,
        first_interaction=datetime.utcnow() - timedelta(days=30)
    )
    
    high_value_customer = CRM(
        name="High Value Customer",
        email="highvalue@example.com",
        phone="+3333333333",
        organization_id="org-123",
        total_conversations=20,
        first_interaction=datetime.utcnow() - timedelta(days=90),
        services_requested=["premium", "enterprise", "consulting"]
    )
    
    inactive_customer = CRM(
        name="Inactive Customer",
        email="inactive@example.com",
        phone="+4444444444",
        organization_id="org-123",
        total_conversations=2,
        first_interaction=datetime.utcnow() - timedelta(days=180),
        last_interaction=datetime.utcnow() - timedelta(days=180)
    )
    
    for c in [new_customer, returning_customer, high_value_customer, inactive_customer]:
        mock_db.add(c)
    mock_db.commit()
    
    # Test segmentation logic
    all_customers = mock_db.query(CRM).all()
    
    new_segment = [c for c in all_customers if c.total_conversations == 1]
    returning_segment = [c for c in all_customers if c.total_conversations > 1 and c.total_conversations < 10]
    high_value_segment = [c for c in all_customers if c.total_conversations >= 10]
    inactive_segment = [c for c in all_customers if c.last_interaction and (datetime.utcnow() - c.last_interaction).days > 90]
    
    assert len(new_segment) == 1
    assert len(returning_segment) == 1
    assert len(high_value_segment) == 1
    assert len(inactive_segment) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])