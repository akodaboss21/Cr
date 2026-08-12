"""
Background Workers Module - Pydantic Schemas
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class BackgroundWorkerBase(BaseModel):
    name: str
    type: str  # 'pyrunner', 'celery', etc.
    config: Optional[str] = None  # JSON data
    is_active: bool = True

class BackgroundWorkerCreate(BackgroundWorkerBase):
    pass

class BackgroundWorkerUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    config: Optional[str] = None
    is_active: Optional[bool] = None
    status: Optional[str] = None

class BackgroundWorkerResponse(BackgroundWorkerBase):
    id: str
    organization_id: str
    status: str
    tasks_processed: int
    tasks_failed: int
    last_task_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class BackgroundJobBase(BaseModel):
    task_type: str
    task_data: Optional[str] = None  # JSON data
    status: str = "pending"  # 'pending', 'running', 'completed', 'failed', 'retried'
    retry_count: int = 0
    max_retries: int = 3
    scheduled_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[str] = None  # JSON data
    error: Optional[str] = None

class BackgroundJobCreate(BackgroundJobBase):
    pass

class BackgroundJobUpdate(BaseModel):
    task_type: Optional[str] = None
    task_data: Optional[str] = None
    status: Optional[str] = None
    retry_count: Optional[int] = None
    max_retries: Optional[int] = None
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[str] = None
    error: Optional[str] = None

class BackgroundJobResponse(BackgroundJobBase):
    id: str
    organization_id: str
    worker_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True