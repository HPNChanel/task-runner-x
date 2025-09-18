
import asyncio
import json
from datetime import datetime
from redis import asyncio as aioredis

from .config import get_worker_settings
from .logging import setup_logging
from .metrics import Timer

from ..app.config import get_settings
from ..app.deps import db_session
from ..app.services.tasks import set_task_started, set_task_finished


WCFG = get_worker_settings()
SETTINGS = get_settings()
log = setup_logging(SETTINGS.log_level)


async def ensure_group(r: aioredis.Redis):
    streams = await r.xinfo_groups(WCFG.stream)
    if not any(g.get("name") == WCFG.group for g in streams):
        try:
            await r.xgroup_create(WCFG.stream, WCFG.group, id="$", mkstream=True)
            log.info(f"Created consumer group {WCFG.group}")
        except Exception as e:
            if "BUSYGROUP" in str(e):
                pass
            else:
                raise


async def handle_message(r: aioredis.Redis, msg_id: str, data: dict):
    try:
        task_id = int(data.get("task_id"))
        name = data.get("name")
        payload = json.loads(data.get("payload") or "{}")
    
        with db_session() as db:
            set_task_started(db, task_id)
        
        with Timer() as t:
            #* Task handlers
            if name == "heartbeat":
                await asyncio.sleep(0.1)
            elif name == "echo":
                await asyncio.sleep(0.05)
                log.info(f"ECHO: {payload}")
            elif name == "sha256":
                import hashlib
                s = (payload.get("text") or "").encode("utf-8")
                hashlib.sha256(s).hexdigest()
            else:
                raise ValueError(f"Unknown task name: {name}")
    
        with db_session() as db:
            set_task_finished(db, task_id, error=None)
        log.info(f"Processed {msg_id} task_id={task_id} name={name} in {t.elapsed:.3f}s")
        await r.xack(WCFG.stream, WCFG.group, msg_id)
    except Exception as e:
        with db_session() as db:
            set_task_finished(db, task_id if "task_id" in locals() else 0, error=str(e))
        log.error(f"Error processing {msg_id}: {e}", exc_info=True)
        await r.xack(WCFG.stream, WCFG.group, msg_id)


async def worker_loop():
    r = aioredis.from_url(WCFG.redis_url, decode_responses=True)
    await ensure_group(r)
    while True:
        try:
            resp = await r.xreadgroup(
                groupname=WCFG.group,
                consumername=WCFG.consumer,
                streams={WCFG.stream: '>'},
                count=10,
                block=WCFG.block_ms
            )
            if not resp:
                continue
                
            for _, entries in resp:
                for msg_id, fields in entries:
                    await handle_message(r, msg_id, fields)
        except Exception as e:
            log.error(f"Loop error: {e}", exc_info=True)
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(worker_loop())
        