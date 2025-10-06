
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Task
from ..schemas import TaskCreate

"""
Implements a task management system
"""

def create_task(db: Session, data: TaskCreate) -> Task:
    task = Task(name=data.name, payload=data.payload or {}, status="queued")
    db.add(task)
    db.flush()
    return task

def set_task_started(db: Session, task_id: int):
    q = select(Task).where(Task.id == task_id)
    task = db.scalar(q)
    if not task:
        return None
    task.status = "running"
    task.started_at = datetime.utcnow()  #* Newest format
    task.attempts += 1
    db.add(task)
    return task

def set_task_finished(db: Session, task_id: int, error: str | None = None):
    q = select(Task).where(Task.id == task_id)
    task = db.scalar(q)
    if not task:
        return None
    
    task.status = "failed" if error else "done"
    task.finished_at = datetime.utcnow()
    if error:
        task.last_error = error
    db.add(task)
    return task

def get_task(db: Session, task_id: int) -> Task | None:
    return db.get(Task, task_id)

def list_tasks(db: Session, limit: int = 50, offset: int = 0):
    stmt = select(Task).order_by(Task.id.desc()).offset(offset).limit(limit)
    return db.scalars(stmt).all()
