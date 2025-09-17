
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine
from .config import get_settings


settings = get_settings()
engine = create_engine(
    settings.sqlalchemy_dsn,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

