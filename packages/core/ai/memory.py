"""
AI Memory Abstraction Layer

This module implements a unified memory system for the AI Receptionist.
It provides abstractions for:
- Short-term memory (current conversation)
- Long-term memory (user preferences)
- Business memory (policies, services, brand voice)
"""
from typing import List, Dict, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session
from uuid import uuid4
import json

from packages.core.database import SessionLocal
from packages.core.identity.conversation.models import Conversation, Message
from packages.core.identity.models import Organization, User as Customer
from packages.core.identity.business.models import BusinessPolicy, Service, Product
from packages.core.identity.crm.models import CRM
from packages.core.ai.gateway.base import ModelInfo
from packages.core.ai.reception.context import ConversationContext


class MemoryError(Exception):
    """Base exception for memory operations"""
    pass


class ShortTermMemory:
    """
    Short-term memory - conversation history within a session
    
    Manages:
    - Current conversation messages
    - Context window management
    - Message relevance scoring
    """
    
    MAX_CONTEXT_TOKENS = 8192
    
    def __init__(self, conversation_id: str, db: Session, organization_id: Optional[str] = None):
        self.conversation_id = conversation_id
        self.db = db
        self.organization_id = organization_id
        self.messages: List[Dict[str, Any]] = []
        self.load_conversation()
    
    def load_conversation(self):
        """Load conversation history from database"""
        query = self.db.query(Conversation).filter(
            Conversation.id == self.conversation_id
        )
        if self.organization_id:
            query = query.filter(Conversation.organization_id == self.organization_id)
        conversation = query.first()
        
        if conversation:
            self.messages = conversation.messages or []
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Add a message to conversation history"""
        message = Message(
            id=str(uuid4()),
            conversation_id=self.conversation_id,
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self.messages.append(message)
        self.db.add(message)
        self.db.commit()
        return message
    
    def get_context(self) -> List[Dict]:
        """Get current conversation context"""
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "metadata": msg.metadata
            }
            for msg in self.messages
        ]
    
    def get_relevant_context(self, max_tokens: int = 4096) -> List[Dict]:
        """Get relevant context within token limits"""
        # Simple truncation - keep last N messages
        context = []
        current_tokens = 0
        
        # Process messages in reverse order
        for msg in reversed(self.messages):
            msg_tokens = self._estimate_tokens(msg.content)
            if current_tokens + msg_tokens > max_tokens:
                break
            context.insert(0, {
                "role": msg.role,
                "content": msg.content,
                "metadata": msg.metadata
            })
            current_tokens += msg_tokens
        
        return context
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (simple approximation)"""
        # Rough estimate: 1 token ≈ 4 characters
        return max(1, len(text) // 4)


class LongTermMemory:
    """
    Long-term memory - persistent user and business data
    
    Manages:
    - Customer preferences
    - Interaction history
    - User profiles
    - Business relationships
    """
    
    def __init__(self, customer_id: str, db: Session, organization_id: Optional[str] = None):
        self.customer_id = customer_id
        self.db = db
        self.organization_id = organization_id
        self.customer = self._load_customer()
    
    def _load_customer(self) -> Optional[Customer]:
        """Load customer from database"""
        query = self.db.query(Customer).filter(
            Customer.id == self.customer_id
        )
        if self.organization_id:
            query = query.filter(Customer.organization_id == self.organization_id)
        return query.first()
    
    def get_preferences(self) -> Dict:
        """Get customer preferences"""
        if not self.customer:
            return {}
        return getattr(self.customer, 'preferences', {}) or {}
    
    def save_preference(self, key: str, value: Any):
        """Save a customer preference"""
        if not self.customer:
            return
        preferences = getattr(self.customer, 'preferences', {}) or {}
        preferences[key] = value
        setattr(self.customer, 'preferences', preferences)
        self.db.commit()
    
    def get_conversation_history(self, limit: int = 10) -> List[Dict]:
        """Get recent conversation history"""
        # This would query conversation records
        # For now, return placeholder
        return []


class BusinessMemory:
    """
    Business memory - organizational knowledge and policies
    
    Manages:
    - Service catalogs
    - Product information
    - Brand voice guidelines
    - Operational policies
    """
    
    def __init__(self, organization_id: str, db: Session):
        self.organization_id = organization_id
        self.db = db
        self.services = self._load_services()
        self.products = self._load_products()
        self.policies = self._load_policies()
    
    def _load_services(self) -> Dict[str, Dict]:
        """Load service information"""
        services = self.db.query(Service).filter(
            Service.organization_id == self.organization_id
        ).all()
        return {service.id: {
            "id": service.id,
            "name": service.name,
            "description": service.description,
            "price": service.price,
            "duration": service.duration
        } for service in services}
    
    def _load_products(self) -> Dict[str, Dict]:
        """Load product information"""
        products = self.db.query(Product).filter(
            Product.organization_id == self.organization_id
        ).all()
        return {product.id: {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "sku": product.sku
        } for product in products}
    
    def _load_policies(self) -> Dict[str, str]:
        """Load business policies"""
        policies = self.db.query(BusinessPolicy).filter(
            BusinessPolicy.organization_id == self.organization_id
        ).all()
        return {policy.name: policy.content for policy in policies}
    
    def get_service_details(self, service_id: str) -> Optional[Dict]:
        """Get service details by ID"""
        return self.services.get(service_id)
    
    def get_product_details(self, product_id: str) -> Optional[Dict]:
        """Get product details by ID"""
        return self.products.get(product_id)
    
    def get_policy(self, policy_name: str) -> Optional[str]:
        """Get a specific policy"""
        return self.policies.get(policy_name)


class MemoryManager:
    """
    Unified memory manager for the AI Receptionist
    
    Provides a single interface for accessing different memory types
    """
    
    def __init__(self, db: Session, organization_id: Optional[str] = None):
        self.db = db
        self.organization_id = organization_id
        self.short_term = None
        self.long_term = None
        self.business = None
        self._contexts: Dict[str, ConversationContext] = {}
        
        # Initialize memory components
        self._init_memory_components()
    
    def _init_memory_components(self):
        """Initialize memory components based on current context"""
        # In a real implementation, these would be initialized based on
        # current conversation/user context
        pass
    
    def get_short_term_memory(self, conversation_id: str) -> 'ShortTermMemory':
        """Get or create short-term memory for a conversation"""
        if not self.short_term or self.short_term.conversation_id != conversation_id:
            self.short_term = ShortTermMemory(conversation_id, self.db, self.organization_id)
        return self.short_term
    
    def get_long_term_memory(self, customer_id: str) -> 'LongTermMemory':
        """Get or create long-term memory for a customer"""
        if not self.long_term or self.long_term.customer_id != customer_id:
            self.long_term = LongTermMemory(customer_id, self.db, self.organization_id)
        return self.long_term
    
    def get_business_memory(self) -> 'BusinessMemory':
        """Get business memory instance"""
        if not self.business or self.business.organization_id != self.organization_id:
            self.business = BusinessMemory(self.organization_id or 1, self.db)
        return self.business
    
    async def get_conversation_context(self, conversation_id: str, customer_id: Optional[str] = None) -> ConversationContext:
        """Return or create an in-memory conversation context for the requested conversation."""
        context = self._contexts.get(conversation_id)
        if context is None:
            context = ConversationContext(conversation_id, customer_id=customer_id)
            self._contexts[conversation_id] = context
        elif customer_id and not context.customer_id:
            context.customer_id = customer_id
            context.customer_info.id = customer_id
        return context

    async def update_conversation(self, conversation_id: str, context: ConversationContext, response: Any) -> ConversationContext:
        """Persist the latest conversation context and response metadata."""
        self._contexts[conversation_id] = context
        return context

    def reset_memory(self):
        """Reset all memory components"""
        self.short_term = None
        self.long_term = None
        self.business = None
        self._contexts = {}


# Global memory manager instance
memory_manager = MemoryManager


def get_memory_manager(db: Session, organization_id: Optional[str] = None) -> 'MemoryManager':
    """Get or create memory manager instance"""
    return memory_manager(db, organization_id)