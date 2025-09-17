
from pydantic import BaseModel, Field
from typing import Any, Optional
from datetime import datetime


class TaskCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    payload: Optional[dict[str, Any]] = None


class TaskRead(BaseModel):
    id: int
    name: str
    status: str
    payload: Optional[dict] = None
    attempts: int
    last_error: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class EnqueueResult(BaseModel):
    task_id: int
    stream_id: str
    
