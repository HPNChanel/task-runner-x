"""Database initialization script."""

from ..app.db import engine, Base
from ..app.models import Job, Schedule, Execution
from ..logging import setup_logging, get_logger

logger = get_logger(__name__)


def init_db():
    """Initialize database tables."""
    setup_logging()
    logger.info("Creating database tables...")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    logger.info("Database tables created successfully")


if __name__ == "__main__":
    init_db()
