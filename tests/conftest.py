from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from taskrunnerx.app.db import Base
from taskrunnerx.app.services import tasks as tasks_service
from taskrunnerx.app.services.queue import Queue as QueueService
from taskrunnerx.app.services.queue import settings as queue_settings
from taskrunnerx.metrics import metrics
from taskrunnerx.worker import worker as worker_module


@pytest.fixture()
def sqlite_engine(tmp_path: Path) -> Iterator[Session]:
    db_file = tmp_path / "taskrunnerx.sqlite"
    engine = create_engine(f"sqlite:///{db_file}", future=True)
    Base.metadata.create_all(engine)
    try:
        yield engine
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture()
def session_factory(sqlite_engine) -> sessionmaker[Session]:
    return sessionmaker(bind=sqlite_engine, autoflush=False, autocommit=False, future=True)


@pytest.fixture(autouse=True)
def tune_settings() -> Iterator[None]:
    original = {
        "dedupe_window_ms": tasks_service.SETTINGS.dedupe_window_ms,
        "clock_skew_ms": tasks_service.SETTINGS.clock_skew_ms,
        "max_task_attempts": tasks_service.SETTINGS.max_task_attempts,
        "retry_backoff_ms": tasks_service.SETTINGS.retry_backoff_ms,
        "retry_backoff_multiplier": tasks_service.SETTINGS.retry_backoff_multiplier,
    }
    queue_original = {
        "dedupe_window_ms": queue_settings.dedupe_window_ms,
        "clock_skew_ms": queue_settings.clock_skew_ms,
        "max_task_attempts": queue_settings.max_task_attempts,
        "retry_backoff_ms": queue_settings.retry_backoff_ms,
        "retry_backoff_multiplier": queue_settings.retry_backoff_multiplier,
    }
    worker_original = {
        "max_task_attempts": worker_module.SETTINGS.max_task_attempts,
        "retry_backoff_ms": worker_module.SETTINGS.retry_backoff_ms,
        "retry_backoff_multiplier": worker_module.SETTINGS.retry_backoff_multiplier,
    }
    tasks_service.SETTINGS.dedupe_window_ms = 1000
    tasks_service.SETTINGS.clock_skew_ms = 100
    tasks_service.SETTINGS.max_task_attempts = 3
    tasks_service.SETTINGS.retry_backoff_ms = 10
    tasks_service.SETTINGS.retry_backoff_multiplier = 2.0
    queue_settings.dedupe_window_ms = tasks_service.SETTINGS.dedupe_window_ms
    queue_settings.clock_skew_ms = tasks_service.SETTINGS.clock_skew_ms
    queue_settings.max_task_attempts = tasks_service.SETTINGS.max_task_attempts
    queue_settings.retry_backoff_ms = tasks_service.SETTINGS.retry_backoff_ms
    queue_settings.retry_backoff_multiplier = (
        tasks_service.SETTINGS.retry_backoff_multiplier
    )
    worker_module.SETTINGS.max_task_attempts = tasks_service.SETTINGS.max_task_attempts
    worker_module.SETTINGS.retry_backoff_ms = tasks_service.SETTINGS.retry_backoff_ms
    worker_module.SETTINGS.retry_backoff_multiplier = (
        tasks_service.SETTINGS.retry_backoff_multiplier
    )
    try:
        yield
    finally:
        for key, value in original.items():
            setattr(tasks_service.SETTINGS, key, value)
        for key, value in queue_original.items():
            setattr(queue_settings, key, value)
        for key, value in worker_original.items():
            setattr(worker_module.SETTINGS, key, value)


@pytest.fixture(autouse=True)
def reset_metrics() -> Iterator[None]:
    metrics.counters.clear()
    metrics.timers.clear()
    metrics.gauges.clear()
    try:
        yield
    finally:
        metrics.counters.clear()
        metrics.timers.clear()
        metrics.gauges.clear()


@pytest.fixture()
def queue(session_factory: sessionmaker[Session]) -> QueueService:
    return QueueService(session_factory=session_factory)


@pytest.fixture()
def anyio_backend() -> str:
    return "asyncio"
