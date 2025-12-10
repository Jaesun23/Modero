# src/core/database/session.py
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from core.config import get_settings

settings = get_settings()

# 1. 비동기 엔진 생성
# SQLite 사용 시 멀티 스레드 접근을 위한 check_same_thread 옵션 해제 필요
engine = create_async_engine(
    settings.database_url,
    echo=settings.log_level == "DEBUG",
    connect_args=(
        {"check_same_thread": False} if "sqlite" in settings.database_url else {}
    ),
)

# 2. 세션 팩토리 생성
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


# 3. Dependency Injection용 제너레이터
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI Depends용 세션 생성기"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
