"""
Prompts Module

Contains all prompt templates used by the reception agent.
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

@dataclass
class PromptTemplate:
    """Template for generating prompts"""
    name: str
    system: str = ""
    user: str = ""
    instructions: str = ""
    examples: List[str] = field(default_factory=list)
    variables: List[str] = field(default_factory=list)

class PromptManager:
    """
    Manages prompt templates for the reception agent
    
    Provides:
    - Prompt templates for each stage of the pipeline
    - Dynamic variable substitution
    - Prompt versioning
    """
    
    def __init__(self):
        self.templates: Dict[str, PromptTemplate] = {}
        self.register_default_templates()
    
    def register_template(self, name: str, template: PromptTemplate):
        """Register a new prompt template"""
        self.templates[name] = template
    
    def get_template(self, name: str) -> PromptTemplate:
        """Get a registered template"""
        if name not in self.templates:
            raise ValueError(f"Template '{name}' not found")
        return self.templates[name]
    
    def substitute_variables(self, template: PromptTemplate, variables: Dict[str, Any]) -> str:
        """Substitute variables into a template"""
        content = template.system + "\n\n" + template.user
        
        # Substitute variables
        for var in template.variables:
            if var in variables:
                content = content.replace(f"{{{var}}}", variables[var])
        
        return content
    
    def register_default_templates(self):
        """Register default prompt templates"""
        # Intent Classification Template
        intent_template = PromptTemplate(
            name="intent_classification",
            system="You are a helpful assistant that classifies customer intents.",
            user="Classify the following customer message into one of these intents:\n{intents}\n\nMessage: {message}\nClassification:",
            variables=["intents", "message"]
        )
        self.register_template("intent_classification", intent_template)
        
        # Knowledge Retrieval Template
        knowledge_template = PromptTemplate(
            name="knowledge_retrieval",
            system="You are a knowledge retrieval assistant.",
            user="Retrieve relevant information from the knowledge base for the following query:\n\nQuery: {query}\nKnowledge Base: {knowledge}\nRelevant Information:",
            variables=["query", "knowledge"]
        )
        self.register_template("knowledge_retrieval", knowledge_template)
        
        # Response Generation Template
        response_template = PromptTemplate(
            name="response_generation",
            system="You are a helpful receptionist assistant generating responses.",
            user="Generate a helpful, professional response to the following customer message:\n\nMessage: {message}\nContext: {context}\nKnowledge: {knowledge}\nResponse:",
            variables=["message", "context", "knowledge"]
        )
        self.register_template("response_generation", response_template)
        
        # Escalation Template
        escalation_template = PromptTemplate(
            name="escalation",
            system="You are a helpful assistant that determines when to escalate to a human.",
            user="Determine if the following customer interaction requires human escalation:\n\nMessage: {message}\nContext: {context}\nTools Used: {tools}\nResponse: Should escalate: {should_escalate}\nReason: {reason}",
            variables=["message", "context", "tools", "should_escalate", "reason"]
        )
        self.register_template("escalation", escalation_template)
    
    def get_pipeline_prompts(self) -> Dict[str, PromptTemplate]:
        """Get all pipeline prompt templates"""
        return self.templates


# Global prompt manager instance
prompt_manager = PromptManager()


def get_prompt_manager() -> PromptManager:
    """Get or create prompt manager instance"""
    return prompt_manager