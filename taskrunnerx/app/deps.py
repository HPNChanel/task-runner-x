from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy.orm import Session

from .db import SessionLocal


@contextmanager
def db_session() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
