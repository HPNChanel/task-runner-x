"""Add idempotent execution metadata and supporting tables."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

from alembic import op
import sqlalchemy as sa

revision = "20241108_01"
down_revision = "20241102_01_add_task_attempts_last_error"
branch_labels = None
depends_on = None


def _hash_payload(payload: dict[str, object] | None) -> str:
    normalized = json.dumps(payload or {}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _window_start(ts: datetime, window_ms: int = 60000) -> datetime:
    epoch_ms = int(ts.timestamp() * 1000)
    bucket = epoch_ms // window_ms
    aligned = bucket * window_ms
    return datetime.fromtimestamp(aligned / 1000, tz=UTC)


def upgrade() -> None:
    op.add_column("tasks", sa.Column("payload_hash", sa.String(length=128), nullable=True))
    op.add_column("tasks", sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "tasks",
        sa.Column("scheduled_window_start", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "tasks",
        sa.Column("execution_key", sa.String(length=256), nullable=True),
    )

    connection = op.get_bind()
    tasks = sa.table(
        "tasks",
        sa.column("id", sa.Integer),
        sa.column("name", sa.String(128)),
        sa.column("payload", sa.JSON),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("payload_hash", sa.String(128)),
        sa.column("scheduled_at", sa.DateTime(timezone=True)),
        sa.column("scheduled_window_start", sa.DateTime(timezone=True)),
        sa.column("execution_key", sa.String(256)),
    )

    rows = list(connection.execute(sa.select(tasks.c.id, tasks.c.name, tasks.c.payload, tasks.c.created_at)))
    now = datetime.now(tz=UTC)
    for row in rows:
        scheduled_at = row.created_at or now
        payload_hash = _hash_payload(row.payload)
        window_start = _window_start(scheduled_at)
        execution_key = f"legacy:{row.id}"
        connection.execute(
            tasks.update()
            .where(tasks.c.id == row.id)
            .values(
                payload_hash=payload_hash,
                scheduled_at=scheduled_at,
                scheduled_window_start=window_start,
                execution_key=execution_key,
            )
        )

    op.alter_column("tasks", "payload_hash", existing_type=sa.String(length=128), nullable=False)
    op.alter_column("tasks", "scheduled_at", existing_type=sa.DateTime(timezone=True), nullable=False)
    op.alter_column(
        "tasks",
        "scheduled_window_start",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )
    op.alter_column("tasks", "execution_key", existing_type=sa.String(length=256), nullable=False)
    op.create_unique_constraint("uq_tasks_execution_key", "tasks", ["execution_key"])

    op.create_table(
        "task_outbox",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("task_id", sa.Integer, sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("stream", sa.String(length=128), nullable=False),
        sa.Column("execution_key", sa.String(length=256), nullable=False),
        sa.Column("payload", sa.JSON, nullable=False, server_default=sa.text("'{}'")),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("stream_id", sa.String(length=128), nullable=True),
        sa.Column("delivery_attempts", sa.Integer, nullable=False, server_default="0"),
    )

    op.create_table(
        "task_inbox",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("task_id", sa.Integer, sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("execution_key", sa.String(length=256), nullable=False, unique=True),
        sa.Column("attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "task_dead_letter",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("task_id", sa.Integer, sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("execution_key", sa.String(length=256), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("payload", sa.JSON, nullable=False, server_default=sa.text("'{}'")),
        sa.Column("error", sa.Text, nullable=False),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("task_id", "execution_key", name="uq_dead_letter_task"),
    )


def downgrade() -> None:
    op.drop_table("task_dead_letter")
    op.drop_table("task_inbox")
    op.drop_table("task_outbox")
    op.drop_constraint("uq_tasks_execution_key", "tasks", type_="unique")
    op.drop_column("tasks", "execution_key")
    op.drop_column("tasks", "scheduled_window_start")
    op.drop_column("tasks", "scheduled_at")
    op.drop_column("tasks", "payload_hash")
