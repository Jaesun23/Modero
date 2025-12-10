# src/core/logging/context.py
import uuid
from contextvars import ContextVar
from typing import Any, Dict

# 요청별 컨텍스트 저장소 (비동기 안전)
_context_storage: ContextVar[Dict[str, Any]] = ContextVar("log_context", default={})


def bind_context(**kwargs: Any) -> None:
    """현재 요청 컨텍스트에 키-값을 추가합니다."""
    ctx = _context_storage.get().copy()
    ctx.update(kwargs)
    _context_storage.set(ctx)


def get_context() -> Dict[str, Any]:
    """현재 컨텍스트를 반환합니다."""
    return _context_storage.get()


def clear_context() -> None:
    """컨텍스트를 초기화합니다."""
    _context_storage.set({})


def generate_trace_id() -> str:
    """새로운 Trace ID를 생성합니다."""
    return str(uuid.uuid4())[:8]
