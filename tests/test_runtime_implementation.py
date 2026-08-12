import pytest
from types import SimpleNamespace

from packages.core.branding.onboarding_service import OnboardingService
from packages.core.ai.reception.agent import ReceptionAgent, IntentResult, IntentType


class MemoryDB:
    def __init__(self):
        self.data = {}

    def save(self, collection, record):
        self.data.setdefault(collection, []).append(record)

    def query(self, collection, **filters):
        rows = self.data.get(collection, [])
        for key, value in filters.items():
            rows = [row for row in rows if row.get(key) == value]
        return rows


class DummyGateway:
    async def complete(self, *args, **kwargs):
        return SimpleNamespace(content="")


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
async def test_onboarding_service_persists_records():
    service = OnboardingService(MemoryDB())

    onboarding = service.start_onboarding("org-1")
    stored = service._get_onboarding(onboarding["id"])

    assert stored is not None
    assert stored["organization_id"] == "org-1"

    updated = service.submit_step(onboarding["id"], 1, {"business_name": "Test Co"})
    assert updated["data"]["step_1"]["business_name"] == "Test Co"
    assert updated["current_step"] == 2


@pytest.mark.asyncio
async def test_agent_retrieves_matching_knowledge():
    agent = ReceptionAgent(
        organization_id="org-1",
        llm_gateway=DummyGateway(),
        memory_manager=DummyMemoryManager(),
        tool_executor=DummyToolExecutor(),
        prompt_manager=DummyPromptManager(),
        evaluator=DummyEvaluator(),
        business_context={
            "knowledge_base": [
                {
                    "id": "kb-1",
                    "title": "Hours",
                    "content": "We are open Monday through Friday from 9am to 5pm.",
                }
            ]
        },
    )

    result = await agent._retrieve_knowledge(
        "What are your hours?",
        IntentResult(intent=IntentType.GENERAL_QUESTION, confidence=1.0),
        SimpleNamespace(),
    )

    assert result
    assert result[0]["id"] == "kb-1"
