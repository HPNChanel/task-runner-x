import asyncio
import signal

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from taskrunnerx.app.services.queue import queue


async def enqueue_heartbeat() -> None:
    await queue.enqueue(task_id=0, name="heartbeat", payload={"source": "scheduler"})


async def main() -> None:
    await queue.connect()
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(enqueue_heartbeat, trigger=IntervalTrigger(minutes=1))
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
