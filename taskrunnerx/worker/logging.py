import logging
from logging import Logger
import sys
from typing import Any

from contextvars import ContextVar


TRACE_ID: ContextVar[str] = ContextVar("trace_id", default="-")
SPAN_ID: ContextVar[str] = ContextVar("span_id", default="-")


class ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:  # noqa: D401 - logging hook
        record.trace_id = TRACE_ID.get("-")
        record.span_id = SPAN_ID.get("-")
        return True


def setup_logging(level: str = "INFO") -> Logger:
    logger = logging.getLogger("worker")
    logger.setLevel(level)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s trace=%(trace_id)s span=%(span_id)s %(message)s"
        )
        handler.setFormatter(formatter)
        handler.addFilter(ContextFilter())
        logger.addHandler(handler)
        logger.propagate = False
    return logger


def set_trace_context(trace_id: str, span_id: str) -> tuple[Any, Any]:
    trace_token = TRACE_ID.set(trace_id)
    span_token = SPAN_ID.set(span_id)
    return trace_token, span_token


def reset_trace_context(tokens: tuple[Any, Any]) -> None:
    trace_token, span_token = tokens
    TRACE_ID.reset(trace_token)
    SPAN_ID.reset(span_token)
