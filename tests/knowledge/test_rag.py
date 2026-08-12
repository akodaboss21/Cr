import json
from types import SimpleNamespace

import pytest

from packages.core.ai.reception.agent import ReceptionAgent, IntentResult, IntentType
from packages.core.ai.reception.context import ConversationContext
from packages.core.ai.reception.tools import ToolExecutor
from packages.core.ai.retrieval import KnowledgeSearchEngine


class FakeEmbeddingGateway:
    async def embed(self, texts, model=None, user=None, organization_id=None):
        embeddings = []
        for text in texts:
            lower = text.lower()
            if "hours" in lower:
                embeddings.append([1.0, 0.0, 0.0])
            elif "pricing" in lower:
                embeddings.append([0.0, 1.0, 0.0])
            else:
                embeddings.append([0.0, 0.0, 1.0])
        return SimpleNamespace(
            embeddings=embeddings,
            model=model or "text-embedding-3-small",
            prompt_tokens=0,
            total_tokens=0,
        )


class DummyMemoryManager:
    pass


class DummyToolExecutor:
    pass


class DummyPromptManager:
    def build_response_prompt(self, **kwargs):
        return ""

    def get_intent_classification_prompt(self, *args, **kwargs):
        return ""


class DummyEvaluator:
    async def evaluate_interaction(self, *args, **kwargs):
        return None


@pytest.mark.asyncio
async def test_agent_retrieves_matching_knowledge_using_embeddings():
    agent = ReceptionAgent(
        organization_id="org-1",
        llm_gateway=FakeEmbeddingGateway(),
        memory_manager=DummyMemoryManager(),
        tool_executor=DummyToolExecutor(),
        prompt_manager=DummyPromptManager(),
        evaluator=DummyEvaluator(),
        business_context={
            "knowledge_base": [
                {
                    "id": "kb-hours",
                    "title": "Hours",
                    "content": "We are open Monday through Friday from 9am to 5pm.",
                    "embedding_vector": json.dumps([1.0, 0.0, 0.0]),
                },
                {
                    "id": "kb-pricing",
                    "title": "Pricing",
                    "content": "Our service costs $75 for a standard visit.",
                    "embedding_vector": json.dumps([0.0, 1.0, 0.0]),
                },
            ]
        },
    )

    result = await agent._retrieve_knowledge(
        "What are your hours?",
        IntentResult(intent=IntentType.GENERAL_QUESTION, confidence=1.0),
        SimpleNamespace(),
    )

    assert result
    assert result[0]["id"] == "kb-hours"
    assert result[0]["score"] >= 0.9


@pytest.mark.asyncio
async def test_knowledge_search_engine_returns_ranked_results():
    engine = KnowledgeSearchEngine(llm_gateway=FakeEmbeddingGateway())
    results = await engine.search(
        query="What are your hours?",
        knowledge_entries=[
            {
                "id": "kb-1",
                "title": "Hours",
                "content": "We are open Monday through Friday from 9am to 5pm.",
                "embedding_vector": json.dumps([1.0, 0.0, 0.0]),
            },
            {
                "id": "kb-2",
                "title": "Pricing",
                "content": "Our service costs $75 for a standard visit.",
                "embedding_vector": json.dumps([0.0, 1.0, 0.0]),
            },
        ],
        organization_id="org-1",
        top_k=3,
    )

    assert results
    assert results[0]["id"] == "kb-1"
    assert results[0]["score"] >= 0.9


class FakeCRMService:
    def __init__(self):
        self.leads = []

    async def create_or_update_lead(self, lead_data, organization_id, customer_id=None):
        self.leads.append({"organization_id": organization_id, "customer_id": customer_id, **lead_data})
        return {"id": "lead-1", "organization_id": organization_id}

    async def update_customer_profile(self, customer_id, profile_update, organization_id):
        self.profile_updates.append({"customer_id": customer_id, "organization_id": organization_id, **profile_update})
        return {"ok": True}


class FakeBookingService:
    def __init__(self):
        self.bookings = []

    async def create_booking(self, booking_data, organization_id, customer_id=None):
        self.bookings.append({"organization_id": organization_id, "customer_id": customer_id, **booking_data})
        return {"id": "booking-1", "organization_id": organization_id}


class FakeKnowledgeService:
    async def search(self, query, organization_id, top_k=5):
        return [{"id": "kb-hours", "title": "Hours", "content": "We are open daily", "score": 0.99}]


class FakeBusinessService:
    async def get_business_hours(self, organization_id):
        return {"hours": "9am-5pm"}

    async def get_location(self, organization_id):
        return {"address": "123 Main St"}


class FakeMemoryManager:
    def __init__(self):
        self.contexts = {}

    async def get_conversation_context(self, conversation_id, customer_id=None):
        if conversation_id not in self.contexts:
            self.contexts[conversation_id] = ConversationContext(conversation_id, customer_id=customer_id)
        return self.contexts[conversation_id]

    async def update_conversation(self, conversation_id, context, response):
        self.contexts[conversation_id] = context
        self.last_response = response


class FakeGateway:
    async def complete(self, *args, **kwargs):
        return SimpleNamespace(content="booking_request")

    async def stream(self, *args, **kwargs):
        if False:
            yield SimpleNamespace(content="")


@pytest.mark.asyncio
async def test_booking_message_creates_lead_and_booking_record():
    crm_service = FakeCRMService()
    booking_service = FakeBookingService()
    knowledge_service = FakeKnowledgeService()
    business_service = FakeBusinessService()
    memory_manager = FakeMemoryManager()

    tool_executor = ToolExecutor(
        crm_service=crm_service,
        booking_service=booking_service,
        knowledge_service=knowledge_service,
        business_service=business_service,
    )
    agent = ReceptionAgent(
        organization_id="org-1",
        llm_gateway=FakeGateway(),
        memory_manager=memory_manager,
        tool_executor=tool_executor,
        prompt_manager=DummyPromptManager(),
        evaluator=DummyEvaluator(),
        business_context={
            "knowledge_base": [
                {"id": "kb-hours", "title": "Hours", "content": "We are open daily"}
            ]
        },
    )

    response = await agent.process_message(
        "I want to book a haircut tomorrow",
        conversation_id="conv-1",
        customer_id="cust-1",
    )

    assert crm_service.leads
    assert booking_service.bookings
    assert response.metadata.get("tool_calls")
