
import asyncio
import signal
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from taskrunnerx.app.config import get_settings
from taskrunnerx.app.services.queue import queue


settings = get_settings()


async def enqueue_heartbeat():
    await queue.enqueue(task_id=0, name="heartbeat", payload={"source": "scheduler"})


async def main():
    await queue.connect()
    sched = AsyncIOScheduler(timezone="UTC")
    sched.add_job(enqueue_heartbeat, trigger=IntervalTrigger(minutes=1))
    sched.start()
    
    stop = asyncio.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        asyncio.get_event_loop().add_signal_handler(sig, stop.set)
    await stop.wait()
    sched.shutdown(wait=False)
    await queue.close()


if __name__ == "__main__":
    asyncio.run(main())
