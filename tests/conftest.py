import pytest
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from core.database import Base, get_session
from main import app as main_app  # Application code와 동일한 import 스타일 사용

@pytest.fixture(scope="function")
async def session() -> AsyncGenerator[AsyncSession, None]:
    # In-memory SQLite for testing
    # 각 테스트마다 완전히 독립된 DB 생성
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,  # SQL 로그 비활성화
        poolclass=None,  # Connection pooling 비활성화
    )

    # 테이블 생성
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Session factory
    TestSessionLocal = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with TestSessionLocal() as session:
        yield session
        await session.rollback()

    # Engine 정리 (connection pool 정리)
    await test_engine.dispose()

@pytest.fixture
async def db_session(session):
    return session

@pytest.fixture
def app() -> FastAPI:
    # src/main.py에 정의된 실제 앱 인스턴스를 사용
    return main_app

@pytest.fixture
async def client(app: FastAPI, session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    # Dependency override
    async def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

    # Cleanup: 테스트 간 간섭 방지를 위해 override 제거
    app.dependency_overrides.clear()

