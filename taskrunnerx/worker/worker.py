import asyncio
from collections.abc import Awaitable, Callable, Mapping
import json
from typing import Any, cast

from redis import asyncio as aioredis

from ..app.config import get_settings
from ..app.deps import db_session
from ..app.services.tasks import set_task_finished, set_task_started
from .config import get_worker_settings
from .logging import setup_logging
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
    except Exception as exc:
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


async def _dispatch_task(name: str, payload: dict[str, Any]) -> None:
    handler = HANDLERS.get(name)
    if handler is None:
        msg = f"Unknown task name: {name}"
        raise ValueError(msg)
    await handler(payload)


async def handle_message(r: aioredis.Redis, msg_id: str, data: Mapping[str, Any]) -> None:
    task_id: int | None = None
    try:
        task_id = int(data.get("task_id", 0))
        name = data.get("name", "")
        payload_raw = data.get("payload") or "{}"
        payload = json.loads(payload_raw)
        if not isinstance(payload, dict):
            payload = {}
        typed_payload: dict[str, Any] = {str(key): value for key, value in payload.items()}

        with db_session() as db:
            set_task_started(db, task_id)

        with Timer() as timer:
            await _dispatch_task(name, typed_payload)

        with db_session() as db:
            set_task_finished(db, task_id, error=None)
        log.info(
            "Processed %s task_id=%s name=%s in %.3fs",
            msg_id,
            task_id,
            name,
            timer.elapsed,
        )
        await r.xack(WCFG.stream, WCFG.group, msg_id)
    except Exception as exc:
        failing_task = task_id if task_id is not None else 0
        with db_session() as db:
            set_task_finished(db, failing_task, error=str(exc))
        log.error("Error processing %s: %s", msg_id, exc, exc_info=True)
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
        except Exception as exc:
            log.error("Loop error: %s", exc, exc_info=True)
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(worker_loop())
