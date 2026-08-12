"""
Reception Agent Core

Main agent class that orchestrates the reception agent pipeline.
"""
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime
from uuid import uuid4
from dataclasses import dataclass, field
from enum import Enum

from .context import ConversationContext
from .planner import ReceptionPlanner as Planner
from .tools import ToolExecutor
from ..memory import MemoryManager
from .prompts import PromptManager
from .evaluator import Evaluator
from ..gateway import LLMGateway
from ..retrieval import KnowledgeSearchEngine
from .tools import CRMService, BookingService, KnowledgeService, BusinessService


class IntentType(str, Enum):
    """Supported intent types"""
    GENERAL_QUESTION = "general_question"
    PRICE_QUERY = "price_query"
    SERVICE_QUERY = "service_query"
    PRODUCT_QUERY = "product_query"
    BOOKING_REQUEST = "booking_request"
    AVAILABILITY_CHECK = "availability_check"
    LOCATION_QUERY = "location_query"
    HOURS_QUERY = "hours_query"
    COMPLAINT = "complaint"
    HUMAN_REQUEST = "human_request"
    FOLLOW_UP = "follow_up"
    BUYING_INTENT = "buying_intent"  # NEW: For lead detection


@dataclass
class IntentResult:
    """Intent classification result"""
    intent: IntentType
    confidence: float
    entities: Dict[str, Any] = field(default_factory=dict)
    reasoning: str = ""


@dataclass
class AgentResponse:
    """Agent response with metadata"""
    content: str
    intent: IntentType
    tools_used: List[str] = field(default_factory=list)
    knowledge_used: List[str] = field(default_factory=list)
    confidence: float = 1.0
    requires_human: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class ReceptionAgent:
    """
    Main Reception Agent class

    Orchestrates the complete message pipeline:
    1. Incoming Message
    2. Conversation Context
    3. Intent Classification
    4. Knowledge Retrieval
    5. Planning
    6. Tool Execution
    7. Response Generation
    8. Memory Update
    9. Analytics
    """

    def __init__(
        self,
        organization_id: str,
        llm_gateway: LLMGateway,
        memory_manager: MemoryManager,
        tool_executor: ToolExecutor,
        prompt_manager: PromptManager,
        evaluator: Evaluator,
        business_context: Dict[str, Any],
        crm_service: Optional[CRMService] = None,
        booking_service: Optional[BookingService] = None,
        knowledge_service: Optional[KnowledgeService] = None,
        business_service: Optional[BusinessService] = None,
    ):
        self.organization_id = organization_id
        self.llm_gateway = llm_gateway
        self.memory_manager = memory_manager
        self.tool_executor = tool_executor
        self.prompt_manager = prompt_manager
        self.evaluator = evaluator
        self.business_context = business_context
        self.crm_service = crm_service or getattr(tool_executor, "crm_service", None)
        self.booking_service = booking_service or getattr(tool_executor, "booking_service", None)
        self.knowledge_service = knowledge_service or getattr(tool_executor, "knowledge_service", None)
        self.business_service = business_service or getattr(tool_executor, "business_service", None)
        self.planner = Planner(business_context, business_context.get("knowledge_base", {}))
        self.retrieval_engine = KnowledgeSearchEngine(llm_gateway=llm_gateway)
        
    async def process_message(
        self,
        message: str,
        conversation_id: str,
        customer_id: Optional[str] = None,
        stream: bool = False
    ) -> AgentResponse:
        """
        Process an incoming customer message through the full pipeline
        
        Args:
            message: Customer message
            conversation_id: Conversation identifier
            customer_id: Optional customer identifier
            stream: Whether to stream response
            
        Returns:
            AgentResponse with generated content and metadata
        """
        # 1. Get or create conversation context
        context = await self.memory_manager.get_conversation_context(
            conversation_id, customer_id
        )
        context.metadata["last_user_message"] = message
        
        # 2. Add incoming message to context
        context.add_message("user", message)
        
        # 3. Intent Classification
        intent_result = await self._classify_intent(message, context)
        
        # 4. Knowledge Retrieval
        knowledge_results = await self._retrieve_knowledge(message, intent_result, context)
        
        # 5. Planning
        plan = self.planner.create_plan(
            message, intent_result, knowledge_results, context
        )
        
        # 6. Tool Execution
        tool_results = await self.tool_executor.execute_plan(
            plan, context, self.organization_id
        )
        
        # 7. Response Generation
        response = await self._generate_response(
            message, intent_result, knowledge_results, tool_results, context
        )
        response.metadata["tool_calls"] = [item.get("tool") for item in tool_results]
        response.metadata["tool_results"] = tool_results
        
        # 8. Memory Update
        await self.memory_manager.update_conversation(
            conversation_id, context, response
        )
        
        # 9. Analytics/Evaluation
        await self.evaluator.evaluate_interaction(
            message, response, context, self.organization_id
        )
        
        # 10. AI Lead Detection
        await self._detect_and_create_lead(message, intent_result, customer_id, context)
        
        return response
    
    async def process_message_stream(
        self,
        message: str,
        conversation_id: str,
        customer_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Process message with streaming response
        
        Args:
            message: Customer message
            conversation_id: Conversation identifier
            customer_id: Optional customer identifier
            
        Yields:
            Streaming response chunks
        """
        # Get context
        context = await self.memory_manager.get_conversation_context(
            conversation_id, customer_id
        )
        context.add_message("user", message)
        
        # Intent classification
        intent_result = await self._classify_intent(message, context)
        
        # Knowledge retrieval
        knowledge_results = await self._retrieve_knowledge(message, intent_result, context)
        
        # Planning
        plan = self.planner.create_plan(
            message, intent_result, knowledge_results, context
        )
        
        # Tool execution
        tool_results = await self.tool_executor.execute_plan(
            plan, context, self.organization_id
        )
        
        # Stream response generation
        async for chunk in self._generate_response_stream(
            message, intent_result, knowledge_results, tool_results, context
        ):
            yield chunk
        
        # Memory update and evaluation (after streaming)
        # Note: In production, these would be handled differently for streaming
        # For now, we'll do a simplified version
        final_response = AgentResponse(
            content="",  # Would be accumulated from chunks
            intent=intent_result.intent,
            tools_used=[r.tool_name for r in tool_results],
            knowledge_used=[k.get('id', '') for k in knowledge_results]
        )
        
        await self.memory_manager.update_conversation(
            conversation_id, context, final_response
        )
        
        # AI Lead Detection (after processing)
        await self._detect_and_create_lead(message, intent_result, customer_id, context)
    
    async def _classify_intent(
        self,
        message: str,
        context: ConversationContext
    ) -> IntentResult:
        """Classify the intent of the incoming message"""
        # Use LLM for intent classification
        prompt = self.prompt_manager.get_intent_classification_prompt(
            message, context, self.business_context
        )
        
        response = await self.llm_gateway.complete(
            messages=[{"role": "user", "content": prompt}],
            model=self.business_context.get('llm_model', 'gpt-3.5-turbo'),
            temperature=0.1
        )
        
        # Parse intent from response
        # In production, this would use structured output
        intent = self._parse_intent(response.content)
        
        return IntentResult(
            intent=intent,
            confidence=0.9,  # Would be extracted from LLM response
            entities=self._extract_entities(message, intent)
        )
    
    async def _retrieve_knowledge(
        self,
        message: str,
        intent_result: IntentResult,
        context: ConversationContext
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant knowledge for the message using embeddings and cosine similarity."""
        knowledge_base = self.business_context.get("knowledge_base") or []
        if self.knowledge_service is not None:
            try:
                return await self.knowledge_service.search(
                    query=message,
                    organization_id=self.organization_id,
                    top_k=5,
                )
            except Exception:
                pass

        if not knowledge_base:
            return []

        return await self.retrieval_engine.search(
            query=message,
            knowledge_entries=knowledge_base,
            organization_id=self.organization_id,
            top_k=5,
        )
    
    async def _generate_response(
        self,
        message: str,
        intent_result: IntentResult,
        knowledge_results: List[Dict[str, Any]],
        tool_results: List[Any],
        context: ConversationContext
    ) -> AgentResponse:
        """Generate final response using LLM"""
        # Build prompt with all context
        prompt = self.prompt_manager.build_response_prompt(
            message=message,
            intent=intent_result.intent,
            knowledge=knowledge_results,
            tools=tool_results,
            context=context,
            business_context=self.business_context
        )
        
        response = await self.llm_gateway.complete(
            messages=[{"role": "user", "content": prompt}],
            model=self.business_context.get('llm_model', 'gpt-3.5-turbo'),
            temperature=0.7
        )
        
        tools_used = []
        for item in tool_results:
            if hasattr(item, "tool_name"):
                tools_used.append(item.tool_name)
            elif isinstance(item, dict):
                tool_name = item.get("tool") or item.get("tool_name")
                if tool_name:
                    tools_used.append(tool_name)

        return AgentResponse(
            content=response.content,
            intent=intent_result.intent,
            tools_used=tools_used,
            knowledge_used=[k.get('id', '') for k in knowledge_results],
            confidence=0.9,
            metadata={"tool_calls": []}
        )
    
    async def _generate_response_stream(
        self,
        message: str,
        intent_result: IntentResult,
        knowledge_results: List[Dict[str, Any]],
        tool_results: List[Any],
        context: ConversationContext
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response"""
        prompt = self.prompt_manager.build_response_prompt(
            message=message,
            intent=intent_result.intent,
            knowledge=knowledge_results,
            tools=tool_results,
            context=context,
            business_context=self.business_context
        )
        
        async for chunk in self.llm_gateway.stream(
            messages=[{"role": "user", "content": prompt}],
            model=self.business_context.get('llm_model', 'gpt-3.5-turbo'),
            temperature=0.7
        ):
            yield chunk.content
    
    def _parse_intent(self, response: str) -> IntentType:
        """Parse intent from LLM response"""
        # Simple keyword-based parsing for now
        # In production, use structured output
        response_lower = response.lower()
        
        # Check for buying intent first (highest priority)
        buying_keywords = ['buy', 'purchase', 'order', 'book', 'schedule', 'reserve', 'want to buy', 'interested in buying', 'purchase now', 'buy now', 'order now', 'schedule appointment', 'make appointment', 'book appointment', 'need', 'looking for', 'searching for', 'want to', 'need to', 'require', 'want to get', 'want to purchase', 'want to buy', 'want to order']
        if any(kw in response_lower for kw in buying_keywords):
            return IntentType.BUYING_INTENT
        
        if any(kw in response_lower for kw in ['book', 'appointment', 'schedule']):
            return IntentType.BOOKING_REQUEST
        elif any(kw in response_lower for kw in ['price', 'cost', 'how much']):
            return IntentType.PRICE_QUERY
        elif any(kw in response_lower for kw in ['service', 'offer', 'provide']):
            return IntentType.SERVICE_QUERY
        elif any(kw in response_lower for kw in ['product', 'sell', 'buy']):
            return IntentType.PRODUCT_QUERY
        elif any(kw in response_lower for kw in ['available', 'availability', 'open']):
            return IntentType.AVAILABILITY_CHECK
        elif any(kw in response_lower for kw in ['where', 'location', 'address']):
            return IntentType.LOCATION_QUERY
        elif any(kw in response_lower for kw in ['hours', 'open', 'close', 'time']):
            return IntentType.HOURS_QUERY
        elif any(kw in response_lower for kw in ['complaint', 'problem', 'issue', 'wrong']):
            return IntentType.COMPLAINT
        elif any(kw in response_lower for kw in ['human', 'person', 'agent', 'representative']):
            return IntentType.HUMAN_REQUEST
        elif any(kw in response_lower for kw in ['follow', 'also', 'another', 'more']):
            return IntentType.FOLLOW_UP
        else:
            return IntentType.GENERAL_QUESTION
    
    def _extract_entities(self, message: str, intent: IntentType) -> Dict[str, Any]:
        """Extract entities from message based on intent"""
        entities = {}
        
        # Simple entity extraction
        # In production, use NER or structured extraction
        if intent == IntentType.BOOKING_REQUEST:
            entities['service_type'] = None
            entities['preferred_time'] = None
        elif intent == IntentType.PRICE_QUERY:
            entities['item'] = None
        elif intent == IntentType.SERVICE_QUERY:
            entities['service'] = None
        
        return entities
    
    async def _detect_and_create_lead(
        self,
        message: str,
        intent_result: IntentResult,
        customer_id: Optional[str],
        context: ConversationContext
    ):
        """
        Detect buying intent and create/update lead in CRM
        
        This method checks for buying intent in the message and creates/updates
        a lead in the CRM system. It also updates the customer's profile with
        interaction data.
        """
        # Create a lead for explicit booking requests and buying-intent messages.
        if intent_result.intent in {IntentType.BUYING_INTENT, IntentType.BOOKING_REQUEST}:
            # Extract lead information from message
            lead_data = {
                'name': getattr(context.customer_info, 'name', None) or 'Unknown',
                'email': getattr(context.customer_info, 'email', None),
                'phone': getattr(context.customer_info, 'phone', None),
                'source': 'website',  # Default source
                'status': 'NEW',
                'score': 50,  # Initial score for buying intent
                'notes': f'Buying intent detected: {message[:100]}...',
                'tags': ['buying_intent', 'new_lead'],
                'assigned_to': None,
                'pipeline_stage': 'NEW',
                'next_followup': datetime.utcnow(),
                'first_interaction': getattr(context, 'created_at', datetime.utcnow()),
                'last_interaction': datetime.utcnow(),
                'total_conversations': len(context.messages) + 1,
                'services_requested': [intent_result.intent.value],
                'bookings': [],
                'preferences': {},
                'notes_history': [],
                'important_details': {}
            }

            # Create or update lead in CRM
            await self._create_or_update_lead(lead_data, customer_id, context)

            # Update customer profile
            await self._update_customer_profile(customer_id, lead_data, context)

    async def _create_or_update_lead(
        self,
        lead_data: Dict[str, Any],
        customer_id: Optional[str],
        context: ConversationContext
    ):
        """Create or update a lead in the CRM system using the injected CRM service."""
        try:
            if self.crm_service is None:
                raise RuntimeError("CRM service is not configured")
            result = await self.tool_executor.execute_tool(
                "create_or_update_lead",
                args={
                    **lead_data,
                    "customer_id": customer_id,
                    "organization_id": self.organization_id,
                },
                organization_id=self.organization_id,
                context=context,
            )
            context.lead_created = True
            context.lead_score = lead_data.get("score", 0)
            context.lead_stage = lead_data.get("status", "lead")
            context.metadata["last_lead_result"] = result
        except Exception as exc:
            context.metadata["lead_error"] = str(exc)
            context.lead_created = False
    
    async def _update_customer_profile(
        self,
        customer_id: Optional[str],
        lead_data: Dict[str, Any],
        context: ConversationContext
    ):
        """
        Update customer profile with interaction data
        
        This method updates the customer profile with information from the
        current interaction, including conversation history and preferences.
        """
        if not customer_id:
            return
        
        # Update customer profile with interaction data
        profile_update = {
            'last_interaction': datetime.utcnow(),
            'total_conversations': len(context.messages) + 1,
            'services_requested': lead_data['services_requested'],
            'notes_history': [{
                'timestamp': datetime.utcnow(),
                'note': lead_data['notes'],
                'author': 'AI',
                'type': 'lead_detection'
            }]
        }
        
        try:
            if self.crm_service is None:
                return
            await self.tool_executor.execute_tool(
                "create_or_update_lead",
                args={
                    "customer_id": customer_id,
                    "organization_id": self.organization_id,
                    **profile_update,
                },
                organization_id=self.organization_id,
                context=context,
            )
        except Exception as exc:
            context.metadata["profile_update_error"] = str(exc)