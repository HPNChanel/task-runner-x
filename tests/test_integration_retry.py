from __future__ import annotations

import asyncio
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Any

import pytest

from taskrunnerx.app.models import Task, TaskDeadLetter
from taskrunnerx.app.schemas import TaskCreate
from taskrunnerx.app.services import tasks as tasks_service
from taskrunnerx.worker import worker as worker_module


class FakeRedis:
    def __init__(self) -> None:
        self.entries: list[tuple[str, dict[str, Any]]] = []
        self.acks: list[tuple[str, str, str]] = []

    async def xadd(self, stream: str, fields: dict[str, Any], **_: Any) -> str:
        entry_id = f"{len(self.entries)}-0"
        self.entries.append((entry_id, fields))
        return entry_id

    async def xack(self, stream: str, group: str, msg_id: str) -> None:
        self.acks.append((stream, group, msg_id))

    async def xinfo_groups(self, stream: str) -> list[dict[str, Any]]:  # pragma: no cover - unused
        return []

    async def xgroup_create(
        self, stream: str, group: str, id: str = "$", mkstream: bool = True
    ) -> None:  # pragma: no cover - unused
        return None


@pytest.mark.anyio("asyncio")
async def test_retry_flow_is_idempotent(session_factory, queue) -> None:
    fake_redis = FakeRedis()

    async def fake_connect() -> None:
        queue._redis = fake_redis

    queue.connect = fake_connect  # type: ignore[assignment]
    queue._redis = fake_redis
    original_queue = worker_module.queue
    worker_module.queue = queue
    worker_module.SETTINGS.retry_backoff_ms = 0
    original_db_session = worker_module.db_session

    @contextmanager
    def worker_session() -> Any:
        session = session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    worker_module.db_session = worker_session

    call_count = 0

    async def flaky_task(payload: dict[str, Any]) -> None:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("boom")

    original_handler = worker_module.HANDLERS.get("flaky")
    worker_module.HANDLERS["flaky"] = flaky_task

    scheduled_at = datetime.now(tz=UTC)
    with session_factory() as session:
        task, _ = tasks_service.create_task(
            session, TaskCreate(name="flaky", payload={"n": 1}, scheduled_at=scheduled_at)
        )
        session.commit()
        task_id = task.id

    await queue.dispatch_task(task_id)
    assert len(fake_redis.entries) == 1
    entry_id, fields = fake_redis.entries[0]

    try:
        await worker_module.handle_message(fake_redis, entry_id, fields)
        await asyncio.sleep(0.01)
        assert call_count == 1
        assert len(fake_redis.entries) >= 2

        retry_entry_id, retry_fields = fake_redis.entries[-1]
        await worker_module.handle_message(fake_redis, retry_entry_id, retry_fields)

        assert call_count == 2
        assert len(fake_redis.acks) == 2

        with session_factory() as session:
            db_task = session.get(Task, task_id)
            assert db_task is not None
            assert db_task.status == "done"
            assert db_task.attempts == 2
            assert db_task.inbox is not None
            assert db_task.inbox.processed_at is not None
            assert session.query(TaskDeadLetter).count() == 0
    finally:
        if original_handler is not None:
            worker_module.HANDLERS["flaky"] = original_handler
        else:
            worker_module.HANDLERS.pop("flaky", None)
        worker_module.queue = original_queue
        worker_module.db_session = original_db_session
