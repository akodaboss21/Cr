"""
Prompt Management System

Centralized prompt management for the AI Receptionist.
Prompts are organized by category and stored in the database.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from sqlalchemy.orm import Session
from .gateway.base import ModelInfo

class PromptManager:
    """
    Centralized prompt management system
    
    Manages:
    - Prompt templates organized by category
    - Variable substitution
    - Context-aware prompt selection
    - Version control for prompts
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_prompt_template(self, category: str, name: str, version: str = "latest") -> str:
        """
        Get a prompt template by category and name
        
        Args:
            category: Prompt category (receptionist, extraction, summarization, classification)
            name: Template name
            version: Version (default: "latest")
            
        Returns:
            Prompt template string
            
        Raises:
            ValueError: If template not found
        """
        # This would query the database for prompt templates
        # For now, return a placeholder
        templates = {
            "receptionist": {
                "welcome": "You are Carai, an AI receptionist. Greet the customer warmly and ask how you can help them today.",
                "goodbye": "Thank you for contacting Carai! Have a wonderful day!",
                "escalate": "I'm having trouble with this request. Let me connect you with a human agent."
            },
            "extraction": {
                "customer_info": "Extract the following customer information from the message: name, phone, email, company, reason for contact.",
                "appointment_details": "Extract appointment details: date, time, service type, customer name."
            },
            "summarization": {
                "conversation": "Summarize the key points from this conversation in 3 bullet points.",
                "issue": "Summarize the customer's issue in one clear sentence."
            },
            "classification": {
                "intent": "Classify the customer's intent as: booking, information, support, complaint, or general.",
                "urgency": "Determine the urgency level: high, medium, or low."
            }
        }
        
        if category not in templates:
            raise ValueError(f"Unknown prompt category: {category}")
        
        if name not in templates[category]:
            raise ValueError(f"Unknown prompt name '{name}' in category '{category}'")
        
        return templates[category][name]
    
    def format_prompt(self, template: str, variables: Dict[str, Any]) -> str:
        """
        Format a prompt template with variables
        
        Args:
            template: Prompt template with {variable} placeholders
            variables: Dictionary of variable values
            
        Returns:
            Formatted prompt
        """
        try:
            return template.format(**variables)
        except KeyError as e:
            # Handle missing variables gracefully
            missing_var = str(e).strip("'\"")
            return template.replace(f"{{{missing_var}}}", f"[{missing_var} not provided]")
    
    def get_context_aware_prompt(
        self,
        category: str,
        name: str,
        context: Dict[str, Any],
        variables: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Get a context-aware prompt
        
        Args:
            category: Prompt category
            name: Template name
            context: Context information (customer, conversation, etc.)
            variables: Additional variables
            
        Returns:
            Context-aware prompt
        """
        template = self.get_prompt_template(category, name)
        
        # Merge context and variables
        all_vars = {}
        if variables:
            all_vars.update(variables)
        all_vars.update(context)
        
        return self.format_prompt(template, all_vars)
    
    def get_receptionist_prompts(self) -> Dict[str, str]:
        """
        Get all receptionist prompts
        
        Returns:
            Dictionary of receptionist prompt names to templates
        """
        return {
            "welcome": self.get_prompt_template("receptionist", "welcome"),
            "goodbye": self.get_prompt_template("receptionist", "goodbye"),
            "escalate": self.get_prompt_template("receptionist", "escalate")
        }
    
    def get_extraction_prompts(self) -> Dict[str, str]:
        """
        Get all extraction prompts
        
        Returns:
            Dictionary of extraction prompt names to templates
        """
        return {
            "customer_info": self.get_prompt_template("extraction", "customer_info"),
            "appointment_details": self.get_prompt_template("extraction", "appointment_details")
        }
    
    def get_summarization_prompts(self) -> Dict[str, str]:
        """
        Get all summarization prompts
        
        Returns:
            Dictionary of summarization prompt names to templates
        """
        return {
            "conversation": self.get_prompt_template("summarization", "conversation"),
            "issue": self.get_prompt_template("summarization", "issue")
        }
    
    def get_classification_prompts(self) -> Dict[str, str]:
        """
        Get all classification prompts
        
        Returns:
            Dictionary of classification prompt names to templates
        """
        return {
            "intent": self.get_prompt_template("classification", "intent"),
            "urgency": self.get_prompt_template("classification", "urgency")
        }


# Global prompt manager instance
prompt_manager = None

def get_prompt_manager(db: Session) -> PromptManager:
    """Get or create prompt manager instance"""
    global prompt_manager
    if prompt_manager is None:
        prompt_manager = PromptManager(db)
    return prompt_manager