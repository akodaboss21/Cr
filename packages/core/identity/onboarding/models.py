from sqlalchemy import Column, String, DateTime, Text
from packages.core.database import Base
from datetime import datetime
import uuid

class OnboardingRecord(Base):
    __tablename__ = 'onboardings'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), nullable=False)
    current_step = Column(String(16), default='1')
    status = Column(String(32), default='in_progress')
    data = Column(Text)  # JSON-encoded data
    started_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
