import pytest
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from core.database import Base, get_session
from api.routes.rooms import router as rooms_router
from api.routes.websocket import router as websocket_router

@pytest.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    # In-memory SQLite for testing
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Session factory
    SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionLocal() as session:
        yield session
        await session.rollback()

@pytest.fixture
async def db_session(session):
    return session

@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()
    app.include_router(rooms_router, prefix="/api/v1")
    app.include_router(websocket_router)
    return app

@pytest.fixture
async def client(app: FastAPI, session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    # Dependency override
    async def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
