"""Logging configuration."""

import logging
from logging import Logger
import sys
from typing import Any

from contextvars import ContextVar

from .app.config import get_settings

TRACE_ID: ContextVar[str] = ContextVar("trace_id", default="-")
SPAN_ID: ContextVar[str] = ContextVar("span_id", default="-")


class ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:  # noqa: D401 - logging hook
        record.trace_id = TRACE_ID.get("-")
        record.span_id = SPAN_ID.get("-")
        return True


def setup_logging() -> None:
    """Setup application logging."""

    settings = get_settings()
    if logging.getLogger().handlers:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - trace=%(trace_id)s span=%(span_id)s %(message)s"
        )
    )
    handler.addFilter(ContextFilter())
    root = logging.getLogger()
    root.setLevel(getattr(logging, settings.log_level.upper()))
    root.addHandler(handler)


def get_logger(name: str) -> Logger:
    """Get logger instance."""
    return logging.getLogger(name)


def set_trace_context(trace_id: str, span_id: str) -> tuple[Any, Any]:
    trace_token = TRACE_ID.set(trace_id)
    span_token = SPAN_ID.set(span_id)
    return trace_token, span_token


def reset_trace_context(tokens: tuple[Any, Any]) -> None:
    trace_token, span_token = tokens
    TRACE_ID.reset(trace_token)
    SPAN_ID.reset(span_token)
