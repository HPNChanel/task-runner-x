"""Domain entities."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class JobEntity:
    """Job domain entity."""
    id: str
    task_name: str
    args: Dict[str, Any]
    kwargs: Dict[str, Any]
    status: str
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


@dataclass
class ScheduleEntity:
    """Schedule domain entity."""
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
