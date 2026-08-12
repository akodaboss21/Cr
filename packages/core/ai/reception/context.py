"""
Conversation Context Engine

Manages conversation context for the reception agent.
Maintains customer information, previous messages, current goal, business information, and available tools.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class Message:
    """Represents a single message in the conversation"""
    id: str = field(default_factory=lambda: str(uuid4()))
    role: str = "user"  # user, assistant, system
    content: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    intent: Optional[str] = None
    tools_used: List[str] = field(default_factory=list)


@dataclass
class CustomerInfo:
    """Customer information stored in context"""
    id: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    preferences: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict[str, Any]] = field(default_factory=list)
    last_interaction: Optional[datetime] = None


@dataclass
class BusinessInfo:
    """Business information for context"""
    id: str = ""
    name: str = ""
    industry: str = ""
    services: List[Dict[str, Any]] = field(default_factory=list)
    products: List[Dict[str, Any]] = field(default_factory=list)
    policies: Dict[str, str] = field(default_factory=dict)
    hours: Dict[str, str] = field(default_factory=dict)
    location: Dict[str, str] = field(default_factory=dict)
    brand_voice: Dict[str, Any] = field(default_factory=dict)


class ConversationContext:
    """
    Manages conversation context for the reception agent.
    
    Maintains:
    - Customer information
    - Previous messages
    - Current goal
    - Business information
    - Available tools
    - Context window management
    """
    
    MAX_CONTEXT_MESSAGES = 20
    MAX_CONTEXT_TOKENS = 4000
    
    def __init__(
        self,
        conversation_id: str,
        customer_id: Optional[str] = None,
        business_info: Optional[BusinessInfo] = None
    ):
        self.conversation_id = conversation_id
        self.customer_id = customer_id
        self.messages: List[Message] = []
        self.customer_info = CustomerInfo(id=customer_id) if customer_id else CustomerInfo()
        self.business_info = business_info or BusinessInfo()
        self.current_goal: Optional[str] = None
        self.available_tools: List[str] = []
        self.metadata: Dict[str, Any] = {}
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def add_message(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        intent: Optional[str] = None,
        tools_used: Optional[List[str]] = None
    ) -> Message:
        """Add a message to the conversation history"""
        message = Message(
            role=role,
            content=content,
            metadata=metadata or {},
            intent=intent,
            tools_used=tools_used or []
        )
        self.messages.append(message)
        self.updated_at = datetime.utcnow()
        self._trim_context()
        return message
    
    def get_recent_messages(self, count: int = 10) -> List[Message]:
        """Get the most recent messages"""
        return self.messages[-count:]
    
    def get_messages_for_llm(self, max_tokens: int = 3000) -> List[Dict[str, str]]:
        """Get messages formatted for LLM consumption"""
        # Simple token estimation: 1 token ≈ 4 characters
        messages = []
        current_tokens = 0
        
        for msg in reversed(self.messages):
            msg_tokens = len(msg.content) // 4
            if current_tokens + msg_tokens > max_tokens:
                break
            messages.insert(0, {
                "role": msg.role,
                "content": msg.content
            })
            current_tokens += msg_tokens
        
        return messages
    
    def set_customer_info(self, info: Dict[str, Any]):
        """Update customer information"""
        for key, value in info.items():
            if hasattr(self.customer_info, key):
                setattr(self.customer_info, key, value)
        self.updated_at = datetime.utcnow()
    
    def set_business_info(self, info: BusinessInfo):
        """Update business information"""
        self.business_info = info
        self.updated_at = datetime.utcnow()
    
    def set_current_goal(self, goal: str):
        """Set the current conversation goal"""
        self.current_goal = goal
        self.updated_at = datetime.utcnow()
    
    def set_available_tools(self, tools: List[str]):
        """Set available tools for this conversation"""
        self.available_tools = tools
        self.updated_at = datetime.utcnow()
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get a summary of the current context"""
        return {
            "conversation_id": self.conversation_id,
            "customer_id": self.customer_id,
            "message_count": len(self.messages),
            "current_goal": self.current_goal,
            "customer_name": self.customer_info.name,
            "business_name": self.business_info.name,
            "available_tools": self.available_tools,
            "last_message": self.messages[-1].content if self.messages else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    def _trim_context(self):
        """Trim context to stay within limits"""
        # Trim by message count
        if len(self.messages) > self.MAX_CONTEXT_MESSAGES:
            self.messages = self.messages[-self.MAX_CONTEXT_MESSAGES:]
        
        # Trim by token count (approximate)
        total_chars = sum(len(msg.content) for msg in self.messages)
        if total_chars > self.MAX_CONTEXT_TOKENS * 4:
            # Remove oldest messages until under limit
            while total_chars > self.MAX_CONTEXT_TOKENS * 4 and len(self.messages) > 5:
                removed = self.messages.pop(0)
                total_chars -= len(removed.content)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize context to dictionary"""
        return {
            "conversation_id": self.conversation_id,
            "customer_id": self.customer_id,
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": msg.metadata,
                    "intent": msg.intent,
                    "tools_used": msg.tools_used
                }
                for msg in self.messages
            ],
            "customer_info": {
                "id": self.customer_info.id,
                "name": self.customer_info.name,
                "phone": self.customer_info.phone,
                "email": self.customer_info.email,
                "preferences": self.customer_info.preferences,
                "history": self.customer_info.history,
                "last_interaction": self.customer_info.last_interaction.isoformat() if self.customer_info.last_interaction else None
            },
            "business_info": {
                "id": self.business_info.id,
                "name": self.business_info.name,
                "industry": self.business_info.industry,
                "services": self.business_info.services,
                "products": self.business_info.products,
                "policies": self.business_info.policies,
                "hours": self.business_info.hours,
                "location": self.business_info.location,
                "brand_voice": self.business_info.brand_voice
            },
            "current_goal": self.current_goal,
            "available_tools": self.available_tools,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationContext':
        """Deserialize context from dictionary"""
        context = cls(
            conversation_id=data["conversation_id"],
            customer_id=data.get("customer_id")
        )
        
        # Restore messages
        context.messages = [
            Message(
                id=msg["id"],
                role=msg["role"],
                content=msg["content"],
                timestamp=datetime.fromisoformat(msg["timestamp"]),
                metadata=msg.get("metadata", {}),
                intent=msg.get("intent"),
                tools_used=msg.get("tools_used", [])
            )
            for msg in data.get("messages", [])
        ]
        
        # Restore customer info
        cust_data = data.get("customer_info", {})
        context.customer_info = CustomerInfo(
            id=cust_data.get("id"),
            name=cust_data.get("name"),
            phone=cust_data.get("phone"),
            email=cust_data.get("email"),
            preferences=cust_data.get("preferences", {}),
            history=cust_data.get("history", []),
            last_interaction=datetime.fromisoformat(cust_data["last_interaction"]) if cust_data.get("last_interaction") else None
        )
        
        # Restore business info
        bus_data = data.get("business_info", {})
        context.business_info = BusinessInfo(
            id=bus_data.get("id", ""),
            name=bus_data.get("name", ""),
            industry=bus_data.get("industry", ""),
            services=bus_data.get("services", []),
            products=bus_data.get("products", []),
            policies=bus_data.get("policies", {}),
            hours=bus_data.get("hours", {}),
            location=bus_data.get("location", {}),
            brand_voice=bus_data.get("brand_voice", {})
        )
        
        context.current_goal = data.get("current_goal")
        context.available_tools = data.get("available_tools", [])
        context.metadata = data.get("metadata", {})
        context.created_at = datetime.fromisoformat(data["created_at"])
        context.updated_at = datetime.fromisoformat(data["updated_at"])
        
        return context