import uuid

from sqlalchemy import String, Boolean, ForeignKey, Text, BigInteger, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from core.database import Base, TimestampMixin


class User(Base, TimestampMixin):
    """사용자 엔티티"""

    __tablename__ = "user"
    # CRITICAL: 테스트 환경에서 conftest.py와 test_models.py가 동일 모델을 import할 때
    # Base.metadata에 중복 등록 시도가 발생. extend_existing으로 허용하되,
    # UNIQUE constraint만 사용 (index=True 제거하여 중복 index 생성 방지)
    __table_args__ = {'extend_existing': True}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False  # index=True 제거됨
    )
    nickname: Mapped[str] = mapped_column(String(100), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Relationships
    # user 삭제 시 관련 데이터 처리는 비즈니스 로직 또는 DB Cascade 설정에 따름
    rooms: Mapped[list["MeetingRoom"]] = relationship(
        "MeetingRoom", back_populates="host"
    )


class MeetingRoom(Base, TimestampMixin):
    """회의실 엔티티"""

    __tablename__ = "meeting_room"
    __table_args__ = {'extend_existing': True}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    host_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    host: Mapped["User"] = relationship("User", back_populates="rooms")
    transcripts: Mapped[list["Transcript"]] = relationship(
        "Transcript", back_populates="room"
    )
    insights: Mapped[list["AiInsight"]] = relationship(
        "AiInsight", back_populates="room"
    )


class Transcript(Base, TimestampMixin):
    """대화록 엔티티"""

    __tablename__ = "transcript"
    __table_args__ = {'extend_existing': True}

    # BigInt ID 사용
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("meeting_room.id"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # 발화 시점 (Unix Timestamp 또는 녹음 기준 오프셋 초)
    # Blueprint 명세의 timestamp를 따름. Mixin의 created_at과는 별도.
    timestamp: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Relationships
    room: Mapped["MeetingRoom"] = relationship(
        "MeetingRoom", back_populates="transcripts"
    )
    user: Mapped["User"] = relationship("User")


class AiInsight(Base, TimestampMixin):
    """AI 분석 결과 엔티티"""

    __tablename__ = "ai_insight"
    __table_args__ = {'extend_existing': True}

    # BigInt ID 사용
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("meeting_room.id"), nullable=False, index=True
    )

    # 분석 유형 (예: summary, action_item, sentiment)
    type: Mapped[str] = mapped_column(String(50), nullable=False)

    # 분석 내용
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    room: Mapped["MeetingRoom"] = relationship("MeetingRoom", back_populates="insights")