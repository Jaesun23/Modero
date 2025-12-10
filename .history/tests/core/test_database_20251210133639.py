import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base, TimestampMixin


# 테스트용 임시 모델 정의
class TestModel(Base, TimestampMixin):
    __tablename__ = "test_model"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]


@pytest.mark.asyncio
async def test_database_session_and_model():
    """DB 세션 생성 및 모델 CRUD 테스트"""

    # 1. In-Memory DB 엔진 생성 (테스트 전용)
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    # 2. 테이블 생성
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 3. 세션 팩토리
    TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession)

    async with TestSessionLocal() as session:
        # Create
        new_item = TestModel(name="test_item")
        session.add(new_item)
        await session.commit()
        await session.refresh(new_item)

        assert new_item.id is not None
        assert new_item.created_at is not None
        assert new_item.updated_at is not None
        assert new_item.name == "test_item"

        # Read
        result = await session.execute(
            select(TestModel).where(TestModel.name == "test_item")
        )
        item = result.scalar_one()
        assert item.id == new_item.id
