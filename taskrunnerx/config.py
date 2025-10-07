from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # * MySQL Config
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "hpnchanel"
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_DB: str = "taskrunnerx"
    MYSQL_DSN: str | None = None

    # * Redis Config
    REDIS_URL: str = "redis://localhost:6379/0"
    QUEUE_STREAM: str = "trx:tasks"
    CONSUMER_GROUP: str = "trx:workers"
    CONSUMER_NAME: str = "worker-1"

    # * Scheduler
    SCHEDULER_TZ: str = "Asia/Ho_Chi_Minh"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def dsn(self) -> str:
        if self.MYSQL_DSN:
            return self.MYSQL_DSN
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}?charset=utf8mb4"
        )


settings = Settings()
