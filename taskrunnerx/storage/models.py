"""SQLAlchemy ORM models."""

from datetime import datetime
from typing import Any, Dict
from uuid import uuid4

from sqlalchemy import Column, String, DateTime, Integer, Text, Boolean, JSON
from sqlalchemy.sql import func

from .db import Base


class Job(Base):
    """Job ORM model."""
    __tablename__ = "jobs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    task_name = Column(String, nullable=False)
    args = Column(JSON, default=dict)
    kwargs = Column(JSON, default=dict)
    status = Column(String, nullable=False, default="pending")
    queue = Column(String, nullable=False, default="default")
    priority = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    retry_count = Column(Integer, default=0)
    timeout = Column(Integer, default=300)
    created_at = Column(DateTime, nullable=False, default=func.now())
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    result = Column(JSON)
    error = Column(Text)


class Schedule(Base):
    """Schedule ORM model."""
    __tablename__ = "schedules"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    name = Column(String, nullable=False, unique=True)
    cron_expression = Column(String, nullable=False)
    task_name = Column(String, nullable=False)
    args = Column(JSON, default=dict)
    kwargs = Column(JSON, default=dict)
    queue = Column(String, nullable=False, default="default")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    last_run_at = Column(DateTime)
    next_run_at = Column(DateTime)


class Execution(Base):
    """Job execution log ORM model."""
    __tablename__ = "executions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    job_id = Column(String, nullable=False)
    worker_id = Column(String, nullable=False)
    started_at = Column(DateTime, nullable=False, default=func.now())
    completed_at = Column(DateTime)
    success = Column(Boolean)
    result = Column(JSON)
    error = Column(Text)
    duration = Column(Integer)  # milliseconds
