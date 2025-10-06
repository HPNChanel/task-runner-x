
import os

from pydantic import BaseModel, Field


class WorkerSettings(BaseModel):
    redis_url: str = Field(default=os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    stream: str = Field(default=os.getenv("REDIS_STREAM", "trx.tasks"))
    group: str = Field(default=os.getenv("REDIS_GROUP", "trx.workers"))
    consumer: str = Field(default=os.getenv("WORKER_NAME", "worker-1"))
    block_ms: int = Field(default=int(os.getenv("WORKER_BLOCK_MS", "5000")))
    
def get_worker_settings() -> WorkerSettings:
    return WorkerSettings()
