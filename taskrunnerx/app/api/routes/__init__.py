
from typing import List

from fastapi import APIRouter, HTTPException

from ...deps import db_session
from ...schemas import EnqueueResult, TaskCreate, TaskRead
from ...services.queue import queue
from ...services.tasks import create_task, get_task, list_tasks

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok"}

@router.post("/tasks", response_model=EnqueueResult, status_code=201)
async def submit_task(payload: TaskCreate):
    with db_session() as db:
        task = create_task(db, payload)
    stream_id = await queue.enqueue(task.id, task.name, task.payload)
    return EnqueueResult(task_id=task.id, stream_id=stream_id)


@router.get("/tasks/{task_id}", response_model=TaskRead)
def read_task(task_id: int):
    with db_session() as db:
        t = get_task(db, task_id)
        if not t:
            raise HTTPException(status_code=404, detail="Task not found")
        return t

@router.get("/tasks", response_model=List[TaskRead])
def read_tasks(limit: int = 50, offset: int = 0):
    with db_session() as db:
        return list_tasks(db, limit=limit, offset=offset)
