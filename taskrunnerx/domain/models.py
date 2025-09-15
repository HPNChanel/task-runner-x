"""Pydantic models for API serialization."""

from datetime import datetime
from typing import Any, Dict, Optional
from enum import Enum

from pydantic import BaseModel


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


class JobCreate(BaseModel):
    task_name: str
    args: Dict[str, Any] = {}
    kwargs: Dict[str, Any] = {}
    queue: str = "default"
    priority: int = 0
    max_retries: int = 3
    timeout: int = 300


class Job(BaseModel):
    id: str
    task_name: str
    args: Dict[str, Any]
    kwargs: Dict[str, Any]
    status: JobStatus
    queue: str
    priority: int
    max_retries: int
    retry_count: int
    timeout: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None


class ScheduleCreate(BaseModel):
    name: str
    cron_expression: str
    task_name: str
    args: Dict[str, Any] = {}
    kwargs: Dict[str, Any] = {}
    queue: str = "default"
    is_active: bool = True


class Schedule(BaseModel):
    id: str
    name: str
    cron_expression: str
    task_name: str
    args: Dict[str, Any]
    kwargs: Dict[str, Any]
    queue: str
    is_active: bool
    created_at: datetime
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None


class ExecutionResult(BaseModel):
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    duration: float
