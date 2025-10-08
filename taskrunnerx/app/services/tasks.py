from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime, timedelta
import hashlib
import json
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import Task, TaskDeadLetter, TaskInbox, TaskOutbox
from ..schemas import TaskCreate

"""
Implements a task management system
"""

SETTINGS = get_settings()


def _normalize_payload(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def compute_payload_hash(payload: dict[str, Any]) -> str:
    normalized = _normalize_payload(payload)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _window_candidates(scheduled_at: datetime) -> list[datetime]:
    window_ms = SETTINGS.dedupe_window_ms
    skew = SETTINGS.clock_skew_ms
    epoch_ms = int(scheduled_at.timestamp() * 1000)

    def _align(ms: int) -> datetime:
        bucket = ms // window_ms
        aligned = bucket * window_ms
        return datetime.fromtimestamp(aligned / 1000, tz=UTC)

    base = _align(epoch_ms)
    candidates = {base}
    if skew:
        candidates.add(_align(epoch_ms + skew))
        candidates.add(_align(epoch_ms - skew))
    ordered = [base]
    for candidate in sorted(candidates - {base}):
        ordered.append(candidate)
    return ordered


def compute_execution_key(name: str, payload_hash: str, window_start: datetime) -> str:
    return f"{name}:{payload_hash}:{int(window_start.timestamp() * 1000)}"


def _existing_task(
    db: Session, name: str, payload_hash: str, candidate_windows: Iterable[datetime]
) -> Task | None:
    stmt = (
        select(Task)
        .where(
            and_(
                Task.name == name,
                Task.payload_hash == payload_hash,
                Task.scheduled_window_start.in_(list(candidate_windows)),
            )
        )
        .limit(1)
    )
    return db.scalar(stmt)


def create_task(db: Session, data: TaskCreate) -> tuple[Task, bool]:
    payload: dict[str, Any] = data.payload or {}
    payload_hash = compute_payload_hash(payload)
    scheduled_at = data.scheduled_at or datetime.now(tz=UTC)
    candidate_windows = _window_candidates(scheduled_at)
    existing = _existing_task(db, data.name, payload_hash, candidate_windows)
    if existing:
        return existing, False

    window_start = candidate_windows[0]
    execution_key = compute_execution_key(data.name, payload_hash, window_start)
    task = Task(
        name=data.name,
        payload=payload,
        payload_hash=payload_hash,
        status="queued",
        scheduled_at=scheduled_at,
        scheduled_window_start=window_start,
        execution_key=execution_key,
    )
    db.add(task)
    db.flush()
    outbox = TaskOutbox(
        task_id=task.id,
        stream=SETTINGS.redis_stream,
        execution_key=execution_key,
        payload=payload,
        available_at=scheduled_at,
    )
    db.add(outbox)
    return task, True


def set_task_started(db: Session, task_id: int, execution_key: str) -> Task | None:
    q = select(Task).where(Task.id == task_id)
    task = db.scalar(q)
    if not task:
        return None
    if task.execution_key != execution_key:
        return None
    if task.inbox and task.inbox.processed_at:
        return None
    task.status = "running"
    task.started_at = datetime.now(tz=UTC)
    task.attempts += 1
    db.add(task)
    inbox = task.inbox or TaskInbox(task_id=task.id, execution_key=task.execution_key)
    if inbox.attempts is None:
        inbox.attempts = 0
    inbox.attempts += 1
    inbox.last_seen_at = datetime.now(tz=UTC)
    task.inbox = inbox
    return task


def set_task_finished(
    db: Session, task_id: int, execution_key: str, error: str | None = None
) -> Task | None:
    q = select(Task).where(Task.id == task_id)
    task = db.scalar(q)
    if not task:
        return None
    if task.execution_key != execution_key:
        return None

    task.status = "failed" if error else "done"
    task.finished_at = datetime.now(tz=UTC)
    if error:
        task.last_error = error
    if task.inbox:
        if error is None:
            task.inbox.processed_at = task.finished_at
        task.inbox.last_seen_at = task.finished_at
    db.add(task)
    return task


def mark_task_retry(
    db: Session,
    task_id: int,
    execution_key: str,
    delay: timedelta,
    error: str,
    max_attempts: int,
) -> tuple[bool, int]:
    task = db.get(Task, task_id)
    if not task:
        return False, 0
    if task.execution_key != execution_key:
        return False, task.attempts

    attempts = task.attempts
    if attempts >= max_attempts:
        return False, attempts

    next_run = datetime.now(tz=UTC) + delay
    task.status = "retrying"
    task.last_error = error
    task.scheduled_at = next_run
    task.scheduled_window_start = _window_candidates(next_run)[0]
    if task.outbox:
        task.outbox.sent_at = None
        task.outbox.stream_id = None
        task.outbox.available_at = next_run
    db.add(task)
    return True, attempts


def move_to_dead_letter(
    db: Session, task_id: int, execution_key: str, name: str, payload: dict[str, Any], error: str
) -> TaskDeadLetter:
    task = db.get(Task, task_id)
    failed_at = datetime.now(tz=UTC)
    if task:
        task.status = "dead_letter"
        task.last_error = error
        task.finished_at = failed_at
        db.add(task)
    dlq = TaskDeadLetter(
        task_id=task_id,
        execution_key=execution_key,
        name=name,
        payload=payload,
        error=error,
        failed_at=failed_at,
    )
    db.add(dlq)
    return dlq


def get_task(db: Session, task_id: int) -> Task | None:
    return db.get(Task, task_id)


def list_tasks(db: Session, limit: int = 50, offset: int = 0) -> list[Task]:
    stmt = select(Task).order_by(Task.id.desc()).offset(offset).limit(limit)
    return list(db.scalars(stmt).all())
