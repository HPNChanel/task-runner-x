from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    payload: dict[str, Any] | None = None


class TaskRead(BaseModel):
    id: int
    name: str
    status: str
    payload: dict[str, Any] | None = None
    attempts: int
    last_error: str | None = None
    created_at: datetime
    updated_at: datetime | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None

    class Config:
        from_attributes = True


class EnqueueResult(BaseModel):
    task_id: int
    stream_id: str
