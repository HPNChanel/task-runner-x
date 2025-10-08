"""Asynchronous worker that consumes Redis stream tasks."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Mapping
from datetime import timedelta
import json
from typing import Any, cast
from uuid import uuid4

from redis import asyncio as aioredis
from sqlalchemy import func, select

from ..app.config import get_settings
from ..app.deps import db_session
from ..metrics import metrics
from ..app.services.queue import queue
from ..app.services.tasks import (
    mark_task_retry,
    move_to_dead_letter,
    set_task_finished,
    set_task_started,
)
from ..app.models import Task, TaskDeadLetter
from .config import get_worker_settings
from .logging import reset_trace_context, set_trace_context, setup_logging
from .metrics import Timer

WCFG = get_worker_settings()
SETTINGS = get_settings()
log = setup_logging(SETTINGS.log_level)


async def ensure_group(r: aioredis.Redis) -> None:
    streams = await r.xinfo_groups(WCFG.stream)
    if any(group.get("name") == WCFG.group for group in streams):
        return

    try:
        await r.xgroup_create(WCFG.stream, WCFG.group, id="$", mkstream=True)
    except Exception as exc:  # pragma: no cover - defensive
        if "BUSYGROUP" not in str(exc):
            raise
    else:
        log.info("Created consumer group %s", WCFG.group)


TaskHandler = Callable[[dict[str, Any]], Awaitable[None]]


async def _handle_heartbeat(_: dict[str, Any]) -> None:
    await asyncio.sleep(0.1)


async def _handle_echo(payload: dict[str, Any]) -> None:
    await asyncio.sleep(0.05)
    log.info("ECHO: %s", payload)


async def _handle_sha256(payload: dict[str, Any]) -> None:
    import hashlib

    data = (payload.get("text") or "").encode("utf-8")
    hashlib.sha256(data).hexdigest()


HANDLERS: dict[str, TaskHandler] = {
    "heartbeat": _handle_heartbeat,
    "echo": _handle_echo,
    "sha256": _handle_sha256,
}


def _retry_delay_seconds(attempts: int) -> float:
    base = SETTINGS.retry_backoff_ms / 1000
    multiplier = SETTINGS.retry_backoff_multiplier ** max(attempts - 1, 0)
    return base * multiplier


async def _dispatch_task(name: str, payload: dict[str, Any]) -> None:
    handler = HANDLERS.get(name)
    if handler is None:
        msg = f"Unknown task name: {name}"
        raise ValueError(msg)
    await handler(payload)


async def handle_message(r: aioredis.Redis, msg_id: str, data: Mapping[str, Any]) -> None:
    task_id: int | None = None
    execution_key = str(data.get("execution_key", ""))
    trace_token: tuple[Any, Any] | None = None
    typed_payload: dict[str, Any] = {}
    try:
        trace_id = uuid4().hex
        span_id = uuid4().hex[:16]
        trace_token = set_trace_context(trace_id, span_id)

        task_id = int(data.get("task_id", 0))
        name = data.get("name", "")
        payload_raw = data.get("payload") or "{}"
        payload = json.loads(payload_raw)
        if not isinstance(payload, dict):
            payload = {}
        typed_payload = {str(key): value for key, value in payload.items()}

        with db_session() as db:
            task = set_task_started(db, task_id, execution_key)
            if task is None:
                metrics.increment("tasks_skipped")
                log.info(
                    "Skipping duplicate task execution task_id=%s key=%s",
                    task_id,
                    execution_key,
                )
                return

        with Timer() as timer:
            await _dispatch_task(name, typed_payload)

        with db_session() as db:
            set_task_finished(db, task_id, execution_key, error=None)

        metrics.timer("task_duration", timer.elapsed)
        metrics.increment("tasks_success")
        log.info(
            "Processed %s task_id=%s name=%s in %.3fs",
            msg_id,
            task_id,
            name,
            timer.elapsed,
        )
    except Exception as exc:  # noqa: BLE001 - intentional broad catch for task safety
        metrics.increment("tasks_failure")
        failing_task = task_id if task_id is not None else 0
        log.error("Error processing %s: %s", msg_id, exc, exc_info=True)
        if failing_task and execution_key:
            delay_seconds = 0.0
            attempts = 0
            with db_session() as db:
                set_task_finished(db, failing_task, execution_key, error=str(exc))
                task_obj = db.get(Task, failing_task)
                current_attempts = task_obj.attempts if task_obj else 0
                delay_seconds = _retry_delay_seconds(current_attempts)
                should_retry, attempts = mark_task_retry(
                    db,
                    failing_task,
                    execution_key,
                    delay=timedelta(seconds=delay_seconds),
                    error=str(exc),
                    max_attempts=SETTINGS.max_task_attempts,
                )
            if should_retry:
                asyncio.create_task(queue.requeue_with_delay(failing_task, delay_seconds))
                log.info(
                    "Scheduled retry task_id=%s after %.2fs attempts=%s",
                    failing_task,
                    delay_seconds,
                    attempts,
                )
            else:
                with db_session() as db:
                    record = move_to_dead_letter(
                        db,
                        failing_task,
                        execution_key,
                        name=data.get("name", ""),
                        payload=typed_payload,
                        error=str(exc),
                    )
                    total = db.scalar(select(func.count()).select_from(TaskDeadLetter)) or 0
                await queue.publish_dead_letter(record)
                metrics.set_gauge("dlq_size", float(total))
        else:
            with db_session() as db:
                set_task_finished(db, failing_task, execution_key, error=str(exc))
    finally:
        if trace_token:
            reset_trace_context(trace_token)
        await r.xack(WCFG.stream, WCFG.group, msg_id)


async def worker_loop() -> None:
    redis_factory: Any = aioredis.from_url
    redis_client = cast(
        aioredis.Redis,
        redis_factory(WCFG.redis_url, decode_responses=True),
    )
    await ensure_group(redis_client)
    while True:
        try:
            resp = await redis_client.xreadgroup(
                groupname=WCFG.group,
                consumername=WCFG.consumer,
                streams={WCFG.stream: ">"},
                count=10,
                block=WCFG.block_ms,
            )
            if not resp:
                continue

            for _, entries in resp:
                for entry_id, fields in entries:
                    await handle_message(redis_client, entry_id, fields)
        except Exception as exc:  # pragma: no cover - defensive loop guard
            log.error("Loop error: %s", exc, exc_info=True)
            await asyncio.sleep(1)


if __name__ == "__main__":  # pragma: no cover - manual execution
    asyncio.run(worker_loop())
