# src/core/logging/config.py
import logging
import sys
from typing import Any, Dict

import structlog
from core.config import get_settings
from .context import get_context


def add_context(
    logger: Any, method_name: str, event_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """컨텍스트(trace_id 등)를 로그에 병합합니다."""
    context = get_context()
    if context:
        event_dict.update(context)
    return event_dict


def configure_logging() -> None:
    settings = get_settings()

    # 공통 프로세서
    processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        add_context,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # 환경별 렌더러 선택
    if settings.env == "prod":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    structlog.configure(
        processors=processors,
        logger_factory=structlog.PrintLoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level)
        ),
        cache_logger_on_first_use=True,
    )
