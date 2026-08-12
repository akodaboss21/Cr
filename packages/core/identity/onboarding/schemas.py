from pydantic import BaseModel
from typing import Any, Dict, Optional
from datetime import datetime

class OnboardingCreate(BaseModel):
    organization_id: str

class OnboardingRecordSchema(BaseModel):
    id: str
    organization_id: str
    current_step: str
    status: str
    data: Optional[Dict[str, Any]]
    started_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
