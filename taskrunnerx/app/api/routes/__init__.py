from typing import Any

from fastapi import APIRouter, HTTPException

from ...deps import db_session
from ...metrics import metrics
from ...schemas import EnqueueResult, TaskCreate, TaskRead
from ...services.queue import queue
from ...services.tasks import create_task, get_task, list_tasks

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    """Simple liveness endpoint for the API."""

    return {"status": "ok"}


@router.post("/tasks", response_model=EnqueueResult, status_code=201)
async def submit_task(payload: TaskCreate) -> EnqueueResult:
    """Persist a task and enqueue it for workers."""

    with db_session() as db:
        task, _ = create_task(db, payload)
    stream_id = await queue.dispatch_task(task.id)
    return EnqueueResult(task_id=task.id, stream_id=stream_id)


@router.get("/tasks/{task_id}", response_model=TaskRead)
def read_task(task_id: int) -> TaskRead:
    """Fetch a task by primary key."""

    with db_session() as db:
        t = get_task(db, task_id)
        if not t:
            raise HTTPException(status_code=404, detail="Task not found")
        return TaskRead.model_validate(t)


@router.get("/tasks", response_model=list[TaskRead])
def read_tasks(limit: int = 50, offset: int = 0) -> list[TaskRead]:
    """List tasks with pagination controls."""

    with db_session() as db:
        tasks = list_tasks(db, limit=limit, offset=offset)
    return [TaskRead.model_validate(task) for task in tasks]


@router.get("/metrics")
def read_metrics() -> dict[str, Any]:
    """Expose in-memory task execution metrics."""

    return metrics.get_stats()
