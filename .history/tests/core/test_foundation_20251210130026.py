import os
import pytest
from core.config import get_settings
from core.logging import bind_context, get_context


def test_settings_load():
    """환경변수가 올바르게 로드되는지 테스트"""
    os.environ["GEMINI_API_KEY"] = "test_key"
    os.environ["JWT_SECRET_KEY"] = "test_secret"

    settings = get_settings()
    assert settings.gemini_api_key.get_secret_value() == "test_key"

    # 필수값 누락 시 에러 발생 확인
    del os.environ["GEMINI_API_KEY"]
    get_settings.cache_clear()  # 캐시 초기화

    with pytest.raises(Exception):  # ValidationError
        get_settings()


@pytest.mark.asyncio
async def test_logging_context_isolation():
    """비동기 작업 간 컨텍스트가 격리되는지 테스트"""
    import asyncio

    async def task_a():
        bind_context(trace_id="task-a")
        await asyncio.sleep(0.1)
        return get_context()["trace_id"]

    async def task_b():
        bind_context(trace_id="task-b")
        await asyncio.sleep(0.1)
        return get_context()["trace_id"]

    # 두 태스크를 동시에 실행
    res_a, res_b = await asyncio.gather(task_a(), task_b())

    # 서로의 trace_id가 섞이지 않아야 함
    assert res_a == "task-a"
    assert res_b == "task-b"
