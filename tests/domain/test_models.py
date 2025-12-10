import pytest
import uuid
from sqlalchemy import select
from src.domain.models import User, MeetingRoom, Transcript, AiInsight


@pytest.mark.asyncio
async def test_create_user(session):
    """User 엔티티 생성 및 저장 테스트"""
    # Given
    email = "test@example.com"
    nickname = "tester"
    password_hash = "hashed_secret"

    user = User(email=email, nickname=nickname, password_hash=password_hash)

    # When
    session.add(user)
    await session.commit()

    # Then
    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)
    saved_user = result.scalar_one()

    assert saved_user.id is not None
    assert isinstance(saved_user.id, uuid.UUID)
    assert saved_user.nickname == nickname
    assert saved_user.created_at is not None


@pytest.mark.asyncio
async def test_create_meeting_room_with_host(session):
    """MeetingRoom 생성 및 Host 관계 매핑 테스트"""
    # Given
    user = User(email="host@example.com", nickname="host", password_hash="pw")
    session.add(user)
    await session.commit()

    room = MeetingRoom(title="Weekly Sync", host_id=user.id)

    # When
    session.add(room)
    await session.commit()

    # Then
    stmt = select(MeetingRoom).where(MeetingRoom.id == room.id)
    result = await session.execute(stmt)
    saved_room = result.scalar_one()

    assert saved_room.title == "Weekly Sync"
    assert saved_room.host_id == user.id
    assert saved_room.is_active is True  # Default value check


@pytest.mark.asyncio
async def test_transcript_creation(session):
    """Transcript 생성 테스트 (BigInt ID 확인)"""
    # Given
    user = User(email="speaker@example.com", nickname="speaker", password_hash="pw")
    session.add(user)
    await session.commit()

    room = MeetingRoom(title="Transcript Room", host_id=user.id)
    session.add(room)
    await session.commit()

    transcript = Transcript(
        room_id=room.id,
        user_id=user.id,
        content="Hello, World!",
        timestamp=1678886400,  # Unix timestamp example
    )

    # When
    session.add(transcript)
    await session.commit()

    # Then
    assert transcript.id is not None
    assert transcript.content == "Hello, World!"
    assert transcript.created_at is not None  # Mixin check


@pytest.mark.asyncio
async def test_ai_insight_creation(session):
    """AiInsight 생성 테스트"""
    # Given
    user = User(email="insight@example.com", nickname="owner", password_hash="pw")
    session.add(user)
    await session.commit()

    room = MeetingRoom(title="Insight Room", host_id=user.id)
    session.add(room)
    await session.commit()

    insight = AiInsight(
        room_id=room.id,
        type="summary",
        content="This meeting was about DNA methodology.",
    )

    # When
    session.add(insight)
    await session.commit()

    # Then
    assert insight.id is not None
    assert insight.type == "summary"
