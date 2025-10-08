import asyncio
import signal

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from taskrunnerx.app.deps import db_session
from taskrunnerx.app.schemas import TaskCreate
from taskrunnerx.app.services.queue import queue
from taskrunnerx.app.services.tasks import create_task


async def enqueue_heartbeat() -> None:
    with db_session() as db:
        task, _ = create_task(
            db,
            TaskCreate(name="heartbeat", payload={"source": "scheduler"}),
        )
    await queue.dispatch_task(task.id)


async def flush_due_tasks() -> None:
    await queue.flush_due()


async def main() -> None:
    await queue.connect()
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(enqueue_heartbeat, trigger=IntervalTrigger(minutes=1))
    scheduler.add_job(flush_due_tasks, trigger=IntervalTrigger(seconds=5))
    scheduler.start()

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)
    await stop.wait()
    scheduler.shutdown(wait=False)
    await queue.close()


if __name__ == "__main__":
    asyncio.run(main())
