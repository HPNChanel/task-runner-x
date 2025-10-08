"""Safety checks for Alembic migrations."""

from __future__ import annotations

from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config

PROJECT_ROOT = Path(__file__).resolve().parent
ALEMBIC_CONFIG = PROJECT_ROOT / "alembic.ini"


def _alembic_config(database_url: str) -> Config:
    cfg = Config(str(ALEMBIC_CONFIG))
    cfg.set_main_option("script_location", "alembic")
    cfg.set_main_option("sqlalchemy.url", database_url)
    return cfg


def _get_engine(url: str) -> sa.Engine:
    return sa.create_engine(url, future=True)


@pytest.fixture()
def temp_db(tmp_path: Path) -> str:
    db_file = tmp_path / "taskrunnerx.sqlite"
    return f"sqlite:///{db_file}"


def _legacy_schema_metadata() -> sa.MetaData:
    metadata = sa.MetaData()
    sa.Table(
        "tasks",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True, nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="queued"),
        sa.Column("payload", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    return metadata


def _get_columns(engine: sa.Engine, table: str) -> set[str]:
    inspector = sa.inspect(engine)
    return {column["name"] for column in inspector.get_columns(table)}


def _get_indexes(engine: sa.Engine, table: str) -> set[str]:
    inspector = sa.inspect(engine)
    return {index["name"] for index in inspector.get_indexes(table)}


def test_upgrade_and_downgrade_clean_database(temp_db: str) -> None:
    cfg = _alembic_config(temp_db)
    command.upgrade(cfg, "head")

    engine = _get_engine(temp_db)
    inspector = sa.inspect(engine)
    tables = set(inspector.get_table_names())
    assert "tasks" in tables
    assert {"task_outbox", "task_inbox", "task_dead_letter"} <= tables
    columns = _get_columns(engine, "tasks")
    expected_columns = {
        "id",
        "name",
        "status",
        "payload",
        "attempts",
        "last_error",
        "created_at",
        "updated_at",
        "started_at",
        "finished_at",
        "payload_hash",
        "scheduled_at",
        "scheduled_window_start",
        "execution_key",
    }
    assert expected_columns <= columns
    indexes = _get_indexes(engine, "tasks")
    assert {"ix_tasks_name", "ix_tasks_status"} <= indexes

    command.downgrade(cfg, "base")
    inspector = sa.inspect(_get_engine(temp_db))
    assert "tasks" not in inspector.get_table_names()


def test_upgrade_and_downgrade_legacy_snapshot(temp_db: str) -> None:
    engine = _get_engine(temp_db)
    metadata = _legacy_schema_metadata()
    metadata.create_all(engine)
    tasks = metadata.tables["tasks"]
    with engine.begin() as conn:
        conn.execute(
            tasks.insert(),
            [
                {
                    "name": "echo",
                    "status": "queued",
                    "payload": {"message": "hello"},
                }
            ],
        )

    engine.dispose()

    cfg = _alembic_config(temp_db)
    command.upgrade(cfg, "head")

    engine = _get_engine(temp_db)
    columns = _get_columns(engine, "tasks")
    assert {"attempts", "last_error", "payload_hash", "execution_key"} <= columns
    with engine.begin() as conn:
        result = conn.execute(
            sa.text(
                "SELECT attempts, last_error, payload_hash, execution_key FROM tasks"
            )
        )
        attempts, last_error, payload_hash, execution_key = result.first()
    assert attempts == 0
    assert last_error is None
    assert payload_hash
    assert execution_key.startswith("legacy:")
    indexes = _get_indexes(engine, "tasks")
    assert {"ix_tasks_name", "ix_tasks_status"} <= indexes

    command.downgrade(cfg, "base")

    engine = _get_engine(temp_db)
    inspector = sa.inspect(engine)
    tables = set(inspector.get_table_names())
    assert "tasks" in tables
    assert "task_outbox" not in tables
    columns = _get_columns(engine, "tasks")
    assert "attempts" not in columns
    assert "last_error" not in columns
    assert "execution_key" not in columns
    with engine.begin() as conn:
        result = conn.execute(sa.text("SELECT name, status FROM tasks"))
        row = result.first()
    assert row == ("echo", "queued")
