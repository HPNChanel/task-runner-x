"""Logging configuration."""

import logging
import sys
from typing import Any, Dict

from .app.config import get_settings as settings


def setup_logging() -> None:
    """Setup application logging."""
    
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def get_logger(name: str) -> logging.Logger:
    """Get logger instance."""
    return logging.getLogger(name)
