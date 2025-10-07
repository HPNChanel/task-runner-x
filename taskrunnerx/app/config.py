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

    # * Scheduler
    scheduler_enabled: bool = Field(
        default=os.getenv("SCHEDULER_ENABLED", "true").casefold() == "true"
    )

    # * Misc
    log_level: str = Field(default=os.getenv("LOG_LEVEL", "INFO"))

    @property
    def sqlalchemy_dsn(self) -> str:
        return f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}@{self.mysql_host}:{self.mysql_port}/{self.mysql_db}?charset=utf8mb4"


@lru_cache
def get_settings() -> Settings:
    return Settings()
