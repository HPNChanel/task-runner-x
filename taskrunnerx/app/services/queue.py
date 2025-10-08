"""Redis-backed task queue with outbox/inbox safety."""

from __future__ import annotations

import asyncio
from contextlib import contextmanager
from datetime import UTC, datetime
import json
from typing import Any, Callable, cast

from redis import asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db import SessionLocal
from ...metrics import metrics
from ..models import Task, TaskDeadLetter, TaskOutbox

settings = get_settings()


class Queue:
    """Wrapper around Redis streams with transactional outbox dispatch."""

    def __init__(self, session_factory: Callable[[], Session] = SessionLocal) -> None:
        self._redis: aioredis.Redis | None = None
        self.stream = settings.redis_stream
        self.dlq_stream = settings.redis_dlq_stream
        self._session_factory = session_factory

    @contextmanager
    def _session_scope(self) -> Session:
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    async def connect(self) -> None:
        if not self._redis:
            redis_factory: Any = aioredis.from_url
            self._redis = cast(
                aioredis.Redis,
                redis_factory(settings.redis_url, decode_responses=True),
            )

    async def close(self) -> None:
        if self._redis:
            await self._redis.close()
            self._redis = None

    async def _publish(
        self, stream: str, payload: dict[str, str], maxlen: int = 10000
    ) -> str:
        await self.connect()
        redis = self._redis
        if redis is None:
            msg = "Redis connection not established"
            raise RuntimeError(msg)
        fields = cast(dict[Any, Any], payload)
        result = await redis.xadd(stream, fields=fields, maxlen=maxlen, approximate=True)
        return cast(str, result)

    async def dispatch_task(self, task_id: int) -> str:
        """Push a persisted task to Redis if due, respecting idempotency."""

        stream_id = ""
        now = datetime.now(tz=UTC)

        with self._session_scope() as db:
            stmt = (
                select(TaskOutbox, Task)
                .join(Task, Task.id == TaskOutbox.task_id)
                .where(TaskOutbox.task_id == task_id)
                .with_for_update()
            )
            result = db.execute(stmt).one_or_none()
            if not result:
                msg = f"Outbox entry for task {task_id} not found"
                raise LookupError(msg)
            outbox, task = result
            if outbox.stream_id:
                return outbox.stream_id
            available_at = outbox.available_at
            if available_at.tzinfo is None:
                available_at = available_at.replace(tzinfo=UTC)
            if available_at > now:
                return ""

            message = {
                "task_id": str(task_id),
                "name": task.name,
                "payload": json.dumps(task.payload or {}),
                "execution_key": outbox.execution_key,
                "scheduled_at": task.scheduled_at.isoformat(),
                "attempt": str(task.attempts + 1),
            }

            stream_id = await self._publish(self.stream, message)
            outbox.sent_at = datetime.now(tz=UTC)
            outbox.stream_id = stream_id
            outbox.delivery_attempts += 1
            metrics.increment("attempts")
            db.add(outbox)

        return stream_id

    async def flush_due(self, limit: int = 25) -> list[str]:
        """Flush all due outbox entries."""

        dispatched: list[str] = []
        while True:
            now = datetime.now(tz=UTC)
            with self._session_scope() as db:
                stmt = (
                    select(TaskOutbox, Task)
                    .join(Task, Task.id == TaskOutbox.task_id)
                    .where(TaskOutbox.sent_at.is_(None))
                    .with_for_update(skip_locked=True)
                    .limit(limit)
                )
                rows = db.execute(stmt).all()
                if not rows:
                    break
                for outbox, task in rows:
                    available_at = outbox.available_at
                    if available_at.tzinfo is None:
                        available_at = available_at.replace(tzinfo=UTC)
                    if available_at > now:
                        continue
                    message = {
                        "task_id": str(task.id),
                        "name": task.name,
                        "payload": json.dumps(task.payload or {}),
                        "execution_key": outbox.execution_key,
                        "scheduled_at": task.scheduled_at.isoformat(),
                        "attempt": str(task.attempts + 1),
                    }
                    stream_id = await self._publish(self.stream, message)
                    outbox.sent_at = datetime.now(tz=UTC)
                    outbox.stream_id = stream_id
                    outbox.delivery_attempts += 1
                    metrics.increment("attempts")
                    db.add(outbox)
                    dispatched.append(stream_id)
            if len(dispatched) < limit:
                break
        return dispatched

    async def requeue_with_delay(self, task_id: int, delay_seconds: float) -> None:
        await asyncio.sleep(delay_seconds)
        await self.dispatch_task(task_id)

    async def publish_dead_letter(self, record: TaskDeadLetter) -> str:
        payload = {
            "task_id": str(record.task_id),
            "execution_key": record.execution_key,
            "name": record.name,
            "payload": json.dumps(record.payload or {}),
            "error": record.error,
            "failed_at": record.failed_at.isoformat(),
        }
        stream_id = await self._publish(self.dlq_stream, payload)
        return stream_id


queue = Queue()
