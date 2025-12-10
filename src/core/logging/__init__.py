# src/core/logging/__init__.py
import structlog
from .config import configure_logging
from .context import bind_context, clear_context, generate_trace_id


def get_logger(name: str | None = None) -> structlog.BoundLogger:
    return structlog.get_logger(name)


__all__ = [
    "get_logger",
    "configure_logging",
    "bind_context",
    "clear_context",
    "generate_trace_id",
]
