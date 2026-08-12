from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime

@dataclass
class UnifiedMessage:
    organization_id: str
    channel: str
    customer_id: str
    conversation_id: str
    content: str
    metadata: Dict[str, Any]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    def to_dict(self):
        return {
            'organization_id': self.organization_id,
            'channel': self.channel,
            'customer_id': self.customer_id,
            'conversation_id': self.conversation_id,
            'content': self.content,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        return cls(
            organization_id=data['organization_id'],
            channel=data['channel'],
            customer_id=data['customer_id'],
            conversation_id=data['conversation_id'],
            content=data['content'],
            metadata=data.get('metadata', {}),
            timestamp=timestamp
        )