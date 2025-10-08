from functools import lru_cache
import os

from pydantic import BaseModel, Field


class Settings(BaseModel):
    app_name: str = "TaskRunnerX"
    env: str = Field(default=os.getenv("ENV", "dev"))
    host: str = Field(default=os.getenv("HOST", "0.0.0.0"))
    port: int = Field(default=int(os.getenv("PORT", "8000")))

    # * MySQL via pymysql
    mysql_user: str = Field(default=os.getenv("MYSQL_USER", "root"))
    mysql_password: str = Field(default=os.getenv("MYSQL_PASSWORD", "root"))
    mysql_host: str = Field(default=os.getenv("MYSQL_HOST", "localhost"))
    mysql_port: str = Field(default=os.getenv("MYSQL_PORT", "3306"))
    mysql_db: str = Field(default=os.getenv("MYSQL_DB", "taskrunnerx"))

    # * Redis
    redis_url: str = Field(default=os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    redis_stream: str = Field(default=os.getenv("REDIS_STREAM", "trx.tasks"))
    redis_group: str = Field(default=os.getenv("REDIS_GROUP", "trx.workers"))
    redis_dlq_stream: str = Field(default=os.getenv("REDIS_DLQ_STREAM", "trx.tasks.dlq"))

    # * Scheduler
    scheduler_enabled: bool = Field(
        default=os.getenv("SCHEDULER_ENABLED", "true").casefold() == "true"
    )

    # * Task execution safety
    dedupe_window_ms: int = Field(
        default=int(os.getenv("TASK_DEDUPE_WINDOW_MS", "60000")), ge=1
    )
    clock_skew_ms: int = Field(default=int(os.getenv("TASK_CLOCK_SKEW_MS", "500")), ge=0)
    max_task_attempts: int = Field(default=int(os.getenv("TASK_MAX_ATTEMPTS", "5")), ge=1)
    retry_backoff_ms: int = Field(default=int(os.getenv("TASK_RETRY_BACKOFF_MS", "500")), ge=0)
    retry_backoff_multiplier: float = Field(
        default=float(os.getenv("TASK_RETRY_BACKOFF_MULTIPLIER", "2.0")), ge=1.0
    )

    # * Misc
    log_level: str = Field(default=os.getenv("LOG_LEVEL", "INFO"))

    @property
    def sqlalchemy_dsn(self) -> str:
        return f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}@{self.mysql_host}:{self.mysql_port}/{self.mysql_db}?charset=utf8mb4"


@lru_cache
def get_settings() -> Settings:
    return Settings()
