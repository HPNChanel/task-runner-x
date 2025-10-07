from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import get_settings

settings = get_settings()
engine: Engine = create_engine(
    settings.sqlalchemy_dsn,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
    future=True,
)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base class."""


SessionLocal: sessionmaker[Session] = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True,
    class_=Session,
)
