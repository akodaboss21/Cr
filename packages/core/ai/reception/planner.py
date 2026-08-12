"""
Reception Planner

Handles the planning logic for the reception agent.
Determines next steps based on intent, knowledge, and available tools.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

if TYPE_CHECKING:
    from packages.core.ai.reception.agent import IntentResult

class PlanningStep(Enum):
    """Planning steps in the execution pipeline"""
    ANALYZE_INTENT = "analyze_intent"
    RETRIEVE_KNOWLEDGE = "retrieve_knowledge"
    GENERATE_PLAN = "generate_plan"
    EXECUTE_TOOL = "execute_tool"
    VALIDATE_RESPONSE = "validate_response"
    UPDATE_CONTEXT = "update_context"
    GENERATE_RESPONSE = "generate_response"


@dataclass
class PlanningStepInfo:
    """Information about a planning step"""
    step: PlanningStep
    description: str
    next_steps: List[str] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)
    output: Any = None


class ReceptionPlanner:
    """
    Plans the execution path for handling customer messages.
    
    Responsibilities:
    - Analyze user intent
    - Retrieve relevant knowledge
    - Generate execution plan
    - Execute tools in sequence
    - Validate responses
    - Update conversation context
    """
    
    def __init__(self, business_context: Dict[str, Any], knowledge_base: Dict[str, Any]):
        self.business_context = business_context
        self.knowledge_base = knowledge_base
        self.execution_path: List[PlanningStepInfo] = []
        self.completed_steps: List[str] = []
        
    def create_plan(self, message: str, intent_result: 'IntentResult', 
                   knowledge_results: List[Dict[str, Any]], 
                   context: 'ConversationContext') -> List[PlanningStepInfo]:
        """
        Create an execution plan based on the current context
        
        Args:
            message: User message
            intent_result: Classified intent
            knowledge_results: Retrieved knowledge
            context: Conversation context
            
        Returns:
            List of planning steps to execute
        """
        steps = []
        
        # Step 1: Analyze intent (already done externally)
        steps.append(PlanningStepInfo(
            step=PlanningStep.ANALYZE_INTENT,
            description="Analyze user intent and extract entities",
            depends_on=[],
            output=intent_result
        ))
        
        # Step 2: Retrieve knowledge
        if knowledge_results:
            steps.append(PlanningStepInfo(
                step=PlanningStep.RETRIEVE_KNOWLEDGE,
                description="Retrieve relevant knowledge base entries",
                depends_on=["analyze_intent"],
                output=knowledge_results
            ))
        
        # Step 3: Generate plan
        steps.append(PlanningStepInfo(
            step=PlanningStep.GENERATE_PLAN,
            description="Create execution plan based on intent and knowledge",
            depends_on=["analyze_intent", "retrieve_knowledge"],
            output=self._generate_execution_plan(message, intent_result, knowledge_results, context)
        ))
        
        # Step 3a: Execute tools (if any)
        # This will be handled dynamically based on the plan
        steps.append(PlanningStepInfo(
            step=PlanningStep.EXECUTE_TOOL,
            description="Execute required tools in sequence",
            depends_on=["generate_plan"],
            output=None
        ))
        
        # Step 4: Validate response
        steps.append(PlanningStepInfo(
            step=PlanningStep.VALIDATE_RESPONSE,
            description="Validate generated response for quality and safety",
            depends_on=["execute_tool"],
            output=None
        ))
        
        # Step 5: Update context
        steps.append(PlanningStepInfo(
            step=PlanningStep.UPDATE_CONTEXT,
            description="Update conversation memory with new information",
            depends_on=["validate_response"],
            output=None
        ))
        
        # Step 6: Generate response
        steps.append(PlanningStepInfo(
            step=PlanningStep.GENERATE_RESPONSE,
            description="Generate final response to user",
            depends_on=["update_context"],
            output=None
        ))
        
        self.execution_path = steps
        self.completed_steps = []
        return steps
    
    def _generate_execution_plan(self, message: str, intent_result: 'IntentResult', 
                               knowledge_results: List[Dict[str, Any]], context: 'ConversationContext') -> Dict[str, Any]:
        """Generate execution plan based on context"""
        # Simple logic: if intent requires tools, plan tool execution
        # This would be more sophisticated in production
        
        plan = {
            'intent': intent_result.intent.value,
            'required_tools': self._get_required_tools(intent_result.intent),
            'knowledge_needed': len(knowledge_results) > 0,
            'context_actions': [],
            'fallback': 'generate_response'
        }
        
        return plan
    
    def _get_required_tools(self, intent: Any) -> List[str]:
        """Determine which tools are needed for a given intent."""
        intent_value = getattr(intent, "value", str(intent))
        tool_mapping = {
            "price_query": ['get_pricing'],
            "service_query": ['list_services'],
            "product_query": ['list_products'],
            "booking_request": ['check_availability', 'create_booking'],
            "availability_check": ['check_availability'],
            "location_query": ['get_location'],
            "hours_query": ['get_hours'],
            "complaint": ['escalate_to_human'],
            "human_request": ['escalate_to_human'],
            "follow_up": ['retrieve_history'],
            "buying_intent": ['check_availability', 'create_booking'],
        }

        return tool_mapping.get(intent_value, [])
    
    def get_execution_path(self) -> List[PlanningStepInfo]:
        """Get the current execution path"""
        return self.execution_path
    
    def mark_step_completed(self, step_name: str):
        """Mark a planning step as completed"""
        if step_name in [si.step.value for si in self.execution_path]:
            self.completed_steps.append(step_name)
    
    def get_completed_steps(self) -> List[str]:
        """Get list of completed steps"""
        return self.completed_steps