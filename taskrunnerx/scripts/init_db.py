"""Database initialization script."""

from __future__ import annotations

from ..app.db import Base, engine


def init() -> None:
    """Create database schema via SQLAlchemy metadata."""

    Base.metadata.create_all(bind=engine)
    print("Database initialized")


if __name__ == "__main__":
    init()
