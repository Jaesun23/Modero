import pytest
from sqlalchemy import select, MetaData
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs

from core.database import TimestampMixin


# 테스트 전용 Base (독립적인 metadata 사용)
# 이름을 _로 시작해서 pytest가 test class로 인식하지 않도록 함
class _TestBase(AsyncAttrs, DeclarativeBase):
    """테스트 전용 Base - 다른 테이블과 격리"""
    pass


# 테스트용 임시 모델 정의
class ModelForTest(_TestBase, TimestampMixin):
    __tablename__ = "test_model"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]


@pytest.mark.asyncio
async def test_database_session_and_model():
    """DB 세션 생성 및 모델 CRUD 테스트"""

    # 1. In-Memory DB 엔진 생성 (테스트 전용)
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    # 2. 테이블 생성 (_TestBase의 독립적인 metadata 사용)
    async with test_engine.begin() as conn:
        await conn.run_sync(_TestBase.metadata.create_all)

    # 3. 세션 팩토리
    TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession)

    async with TestSessionLocal() as session:
        # Create
        new_item = ModelForTest(name="test_item")
        session.add(new_item)
        await session.commit()
        await session.refresh(new_item)

        assert new_item.id is not None
        assert new_item.created_at is not None
        assert new_item.updated_at is not None
        assert new_item.name == "test_item"

        # Read
        result = await session.execute(
            select(ModelForTest).where(ModelForTest.name == "test_item")
        )
        item = result.scalar_one()
        assert item.id == new_item.id