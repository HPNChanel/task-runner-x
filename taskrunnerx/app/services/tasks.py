from datetime import datetime, UTC
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Task
from ..schemas import TaskCreate

"""
Implements a task management system
"""


def create_task(db: Session, data: TaskCreate) -> Task:
    payload: dict[str, Any] = data.payload or {}
    task = Task(name=data.name, payload=payload, status="queued")
    db.add(task)
    db.flush()
    return task


def set_task_started(db: Session, task_id: int) -> Task | None:
    q = select(Task).where(Task.id == task_id)
    task = db.scalar(q)
    if not task:
        return None
    task.status = "running"
    task.started_at = datetime.now(tz=UTC)
    task.attempts += 1
    db.add(task)
    return task


def set_task_finished(db: Session, task_id: int, error: str | None = None) -> Task | None:
    q = select(Task).where(Task.id == task_id)
    task = db.scalar(q)
    if not task:
        return None

    task.status = "failed" if error else "done"
    task.finished_at = datetime.now(tz=UTC)
    if error:
        task.last_error = error
    db.add(task)
    return task


def get_task(db: Session, task_id: int) -> Task | None:
    return db.get(Task, task_id)


def list_tasks(db: Session, limit: int = 50, offset: int = 0) -> list[Task]:
    stmt = select(Task).order_by(Task.id.desc()).offset(offset).limit(limit)
    return list(db.scalars(stmt).all())
