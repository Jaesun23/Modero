import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Boolean, ForeignKey, Text, BigInteger, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from core.database import Base, TimestampMixin


class User(Base, TimestampMixin):
    """사용자 엔티티"""

    __tablename__ = "user"
    # CRITICAL: 테스트 환경에서 conftest.py와 test_models.py가 동일 모델을 import할 때
    # Base.metadata에 중복 등록 시도가 발생. extend_existing으로 허용하되,
    # UNIQUE constraint만 사용 (index=True 제거하여 중복 index 생성 방지)
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    nickname: Mapped[str] = mapped_column(String(100), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Relationships
    rooms: Mapped[list["MeetingRoom"]] = relationship(
        "MeetingRoom", back_populates="host"
    )


class MeetingRoom(Base, TimestampMixin):
    """회의실 엔티티"""

    __tablename__ = "meeting_room"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    host_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # [DNA Fix] Blueprint 3.1: 시작 시간 필드 추가
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

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
    __table_args__ = {"extend_existing": True}

    # BigInt ID 사용 (AutoInc)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("meeting_room.id"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # 발화 시점 (Unix Timestamp, ms 단위 권장)
    # [DNA Note] Blueprint에는 DateTime이었으나 성능상 BigInt(Unix Time) 유지
    timestamp: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Relationships
    room: Mapped["MeetingRoom"] = relationship(
        "MeetingRoom", back_populates="transcripts"
    )
    user: Mapped["User"] = relationship("User")


class AiInsight(Base, TimestampMixin):
    """AI 분석 결과 엔티티"""

    __tablename__ = "ai_insight"
    __table_args__ = {"extend_existing": True}

    # BigInt ID 사용
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("meeting_room.id"), nullable=False, index=True
    )

    # 분석 유형 (예: summary, action_item, sentiment)
    type: Mapped[str] = mapped_column(String(50), nullable=False)

    # 분석 내용
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # [DNA Fix] Blueprint 3.1: 특정 발언 참조 필드 추가
    ref_transcript_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("transcript.id"), nullable=True
    )

    # Relationships
    room: Mapped["MeetingRoom"] = relationship("MeetingRoom", back_populates="insights")
