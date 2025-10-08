"""Add attempts tracking and error storage to tasks."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20241102_01"
down_revision = None
branch_labels = None
depends_on = None

_TASKS_TABLE = "tasks"


def _ensure_tasks_table() -> None:
    """Create the tasks table if it does not yet exist."""

    op.create_table(
        _TASKS_TABLE,
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'queued'")),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("ix_tasks_name", _TASKS_TABLE, ["name"], unique=False)
    op.create_index("ix_tasks_status", _TASKS_TABLE, ["status"], unique=False)


def _ensure_columns(inspector: sa.Inspector) -> None:
    """Ensure newly added columns exist and are populated."""

    existing_columns = {column["name"] for column in inspector.get_columns(_TASKS_TABLE)}
    bind = op.get_bind()

    if "attempts" not in existing_columns:
        op.add_column(
            _TASKS_TABLE,
            sa.Column("attempts", sa.Integer(), nullable=False, server_default=sa.text("0")),
        )
        bind.execute(sa.text("UPDATE tasks SET attempts = 0 WHERE attempts IS NULL"))
    else:
        bind.execute(sa.text("UPDATE tasks SET attempts = 0 WHERE attempts IS NULL"))
        op.alter_column(
            _TASKS_TABLE,
            "attempts",
            existing_type=sa.Integer(),
            nullable=False,
        )

    if "last_error" not in existing_columns:
        op.add_column(_TASKS_TABLE, sa.Column("last_error", sa.Text(), nullable=True))


def _ensure_indexes(inspector: sa.Inspector) -> None:
    """Create required indexes when missing."""

    existing_indexes = {index["name"] for index in inspector.get_indexes(_TASKS_TABLE)}
    if "ix_tasks_name" not in existing_indexes:
        op.create_index("ix_tasks_name", _TASKS_TABLE, ["name"], unique=False)
    if "ix_tasks_status" not in existing_indexes:
        op.create_index("ix_tasks_status", _TASKS_TABLE, ["status"], unique=False)


def upgrade() -> None:
    """Apply the schema changes for task retries and error capture."""

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = inspector.get_table_names()

    if _TASKS_TABLE not in table_names:
        _ensure_tasks_table()
        return

    _ensure_columns(inspector)
    _ensure_indexes(inspector)


def downgrade() -> None:
    """Revert the schema changes introduced in this revision."""

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = inspector.get_table_names()
    if _TASKS_TABLE not in table_names:
        return

    existing_indexes = {index["name"] for index in inspector.get_indexes(_TASKS_TABLE)}
    if "ix_tasks_status" in existing_indexes:
        op.drop_index("ix_tasks_status", table_name=_TASKS_TABLE)
    if "ix_tasks_name" in existing_indexes:
        op.drop_index("ix_tasks_name", table_name=_TASKS_TABLE)

    existing_columns = {column["name"] for column in inspector.get_columns(_TASKS_TABLE)}
    if "last_error" in existing_columns:
        op.drop_column(_TASKS_TABLE, "last_error")
    if "attempts" in existing_columns:
        op.drop_column(_TASKS_TABLE, "attempts")

    row_count = bind.execute(sa.text("SELECT COUNT(*) FROM tasks")).scalar_one()
    if row_count == 0:
        op.drop_table(_TASKS_TABLE)
