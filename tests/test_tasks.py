from __future__ import annotations

from datetime import UTC, datetime, timedelta

from taskrunnerx.app.models import Task
from taskrunnerx.app.schemas import TaskCreate
from taskrunnerx.app.services import tasks as tasks_service


def test_payload_hash_is_order_invariant() -> None:
    payload_a = {"a": 1, "b": 2}
    payload_b = {"b": 2, "a": 1}
    assert tasks_service.compute_payload_hash(payload_a) == tasks_service.compute_payload_hash(
        payload_b
    )


def test_create_task_deduplicates_within_clock_skew(session_factory) -> None:
    scheduled_at = datetime.now(tz=UTC)
    skew = tasks_service.SETTINGS.clock_skew_ms - 10
    request = TaskCreate(name="echo", payload={"msg": "hi"}, scheduled_at=scheduled_at)
    with session_factory() as session:
        task, created = tasks_service.create_task(session, request)
        session.commit()
        first_id = task.id
    assert created

    second_request = TaskCreate(
        name="echo",
        payload={"msg": "hi"},
        scheduled_at=scheduled_at + timedelta(milliseconds=skew),
    )
    with session_factory() as session:
        duplicate, created_second = tasks_service.create_task(session, second_request)
        session.commit()
        duplicate_id = duplicate.id

    assert not created_second
    assert duplicate_id == first_id


def test_create_task_generates_unique_execution_key(session_factory) -> None:
    scheduled_at = datetime.now(tz=UTC)
    first = TaskCreate(name="echo", payload={"seq": 1}, scheduled_at=scheduled_at)
    second = TaskCreate(
        name="echo",
        payload={"seq": 1},
        scheduled_at=scheduled_at + timedelta(milliseconds=tasks_service.SETTINGS.dedupe_window_ms),
    )

    with session_factory() as session:
        task_one, created_one = tasks_service.create_task(session, first)
        session.commit()
        key_one = task_one.execution_key
    with session_factory() as session:
        task_two, created_two = tasks_service.create_task(session, second)
        session.commit()
        key_two = task_two.execution_key

    assert created_one
    assert created_two
    assert key_one != key_two


def test_mark_task_retry_respects_max_attempts(session_factory) -> None:
    scheduled_at = datetime.now(tz=UTC)
    request = TaskCreate(name="echo", payload={"msg": "retry"}, scheduled_at=scheduled_at)
    with session_factory() as session:
        task, _ = tasks_service.create_task(session, request)
        session.commit()
        task_id = task.id
        execution_key = task.execution_key

    with session_factory() as session:
        should_retry, attempts = tasks_service.mark_task_retry(
            session,
            task_id,
            execution_key,
            delay=timedelta(seconds=1),
            error="boom",
            max_attempts=3,
        )
        session.commit()
    assert should_retry
    assert attempts == 0

    with session_factory() as session:
        db_task = session.get(Task, task_id)
        assert db_task is not None
        db_task.attempts = 3
        session.add(db_task)
        session.commit()

    with session_factory() as session:
        should_retry_again, attempts_again = tasks_service.mark_task_retry(
            session,
            task_id,
            execution_key,
            delay=timedelta(seconds=1),
            error="boom",
            max_attempts=3,
        )
        session.commit()
    assert not should_retry_again
    assert attempts_again == 3
