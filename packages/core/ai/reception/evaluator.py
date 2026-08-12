"""
AI Quality Evaluator

Evaluates the quality of reception agent responses.
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import json
import logging
from datetime import datetime
from uuid import uuid4

from ..gateway import LLMGateway
from ..memory import MemoryManager


@dataclass
class EvaluationResult:
    """Result of an evaluation"""
    score: float  # 0.0 to 1.0
    accuracy: float
    helpfulness: float
    hallucination_risk: float
    confidence: float
    metrics: Dict[str, float]
    feedback: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    evaluation_id: str = field(default_factory=lambda: str(uuid4()))


class Evaluator:
    """
    Evaluates reception agent interactions for quality.
    
    Measures:
    - Accuracy of information
    - Helpfulness of response
    - Risk of hallucination
    - Confidence in response
    - Tool usage correctness
    """
    
    def __init__(self, llm_gateway: LLMGateway, memory_manager: MemoryManager):
        self.llm_gateway = llm_gateway
        self.memory_manager = memory_manager
        self.logger = logging.getLogger("evaluator")
        self.logger.setLevel(logging.INFO)
        
        # Default evaluation criteria weights
        self.weights = {
            "accuracy": 0.4,
            "helpfulness": 0.3,
            "hallucination_risk": 0.2,
            "confidence": 0.1
        }
    
    def evaluate_response(
        self,
        message: str,
        response: str,
        context: Dict[str, Any],
        tool_usage: Optional[Dict[str, Any]] = None,
        expected_intent: Optional[str] = None
    ) -> EvaluationResult:
        """
        Evaluate a reception agent response
        
        Args:
            message: Original customer message
            response: Generated response
            context: Conversation context
            tool_usage: Details of tool usage (if any)
            expected_intent: Expected intent (for accuracy check)
            
        Returns:
            EvaluationResult with scoring and feedback
        """
        # 1. Check accuracy
        accuracy_score = self._check_accuracy(message, response, context, expected_intent)
        
        # 2. Check helpfulness
        helpfulness_score = self._check_helpfulness(response, context)
        
        # 3. Check hallucination risk
        hallucination_score = self._check_hallucination(response, context)
        
        # 4. Check confidence
        confidence_score = self._check_confidence(response, context)
        
        # 5. Check tool usage (if provided)
        tool_correctness = 1.0
        if tool_usage:
            tool_correctness = self._check_tool_usage(tool_usage, context)
        
        # Calculate weighted score
        weighted_score = (
            self.weights["accuracy"] * accuracy_score +
            self.weights["helpfulness"] * helpfulness_score +
            self.weights["hallucination_risk"] * (1 - hallucination_score) +
            self.weights["confidence"] * confidence_score
        )
        
        # Generate feedback
        feedback = self._generate_feedback(
            accuracy_score, helpfulness_score, hallucination_score, confidence_score
        )
        
        return EvaluationResult(
            score=weighted_score,
            accuracy=accuracy_score,
            helpfulness=helpfulness_score,
            hallucination_risk=hallucination_score,
            confidence=confidence_score,
            metrics={
                "accuracy": accuracy_score,
                "helpfulness": helpfulness_score,
                "hallucination_risk": hallucination_score,
                "confidence": confidence_score,
                "tool_correctness": tool_correctness
            },
            feedback=feedback,
            evaluation_id=str(uuid4())
        )
    
    def _check_accuracy(self, message: str, response: str, context: Dict[str, Any], expected_intent: Optional[str]) -> float:
        """Check if response accurately addresses the customer's intent"""
        # In production, this would use LLM-based verification
        # For now, use heuristic approaches
        
        # Simple keyword matching for common cases
        lower_msg = message.lower()
        lower_resp = response.lower()
        
        # If expected intent is provided, check if response addresses it
        if expected_intent:
            if expected_intent == "price_query" and ("price" in lower_resp or "cost" in lower_resp):
                return 1.0
            elif expected_intent == "booking_request" and ("book" in lower_resp or "appointment" in lower_resp):
                return 1.0
            # Add more mappings as needed
        
        # General accuracy check
        # Response should contain relevant information based on message content
        if "price" in msg and "price" in resp:
            return 1.0
        # This is a simplified check - real implementation would be more sophisticated
        return 0.7  # Default accuracy score
    
    def _check_helpfulness(self, response: str, context: Dict[str, Any]) -> float:
        """Check if response is helpful and addresses customer needs"""
        # Check for helpful response patterns
        helpful_patterns = [
            "how can I help",
            "I'd be happy to",
            "let me assist",
            "please let me know",
            "I can provide",
            "you might want to"
        ]
        
        lower_resp = response.lower()
        if any(pattern in lower_resp for pattern in helpful_patterns):
            return 1.0
        elif len(response.strip()) > 20:  # Non-empty response
            return 0.8
        else:
            return 0.3
    
    def _check_hallucination(self, response: str, context: Dict[str, Any]) -> float:
        """Check for potential hallucinations (made-up facts)"""
        # Look for made-up statistics, names, or references
        # This is a simplified check
        
        # In production, this would use LLM-based verification
        # For now, simple heuristic checks
        hallucination_indicators = [
            "according to recent studies",  # Made-up studies
            "research shows",  # Generic reference
            "experts agree",  # Vague reference
            "data indicates",  # Unexplained data
            "it is well known"  # Unexplained consensus
        ]
        
        lower_resp = response.lower()
        if any(indicator in lower_resp for indicator in hallucination_indicators):
            return 0.3  # High hallucination risk
        else:
            return 0.9  # Low hallucination risk
    
    def _check_confidence(self, response: str, context: Dict[str, Any]) -> float:
        """Check confidence level of the response"""
        # Look for confidence markers
        confidence_markers = [
            "I think", "maybe", "perhaps", "possibly", "I'm not sure",
            "in my opinion", "it appears"
        ]
        
        lower_resp = response.lower()
        if any(marker in lower_resp for marker in confidence_markers):
            return 0.6  # Lower confidence
        else:
            return 0.9  # High confidence
    
    def _check_tool_usage(self, tool_usage: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Check if tool usage was appropriate and correct"""
        # Validate that tool usage matches the planned action
        # This would integrate with the planner
        # For now, return 1.0 (assume correct)
        return 1.0
    
    def _generate_feedback(self, accuracy: float, helpfulness: float, 
                          hallucination_risk: float, confidence: float) -> str:
        """Generate human-readable feedback"""
        feedback_parts = []
        if accuracy < 0.7:
            feedback_parts.append("Inaccuracy detected in response")
        if helpfulness < 0.7:
            feedback_parts.append("Response lacks helpfulness")
        if hallucination_risk > 0.7:
            feedback_parts.append("Potential hallucination in response")
        if confidence < 0.7:
            feedback_parts.append("Low confidence in response")
        
        if not feedback_parts:
            feedback_parts.append("Response appears appropriate and helpful")
        
        return " | ".join(feedback_parts)
    
    def log_evaluation(self, evaluation: EvaluationResult):
        """Log evaluation result for auditing"""
        self.logger.info(f"Evaluation {evaluation.evaluation_id}: Score={evaluation.score:.3f}")
        self.logger.debug(f"Metrics: {json.dumps(evaluation.metrics)}")
        return evaluation


# Global evaluator instance
evaluator = Evaluator


def get_evaluator(llm_gateway: LLMGateway, memory_manager: MemoryManager) -> Evaluator:
    """Get or create evaluator instance"""
    return evaluator(llm_gateway, memory_manager)