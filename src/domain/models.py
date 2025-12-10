import uuid
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    String,
    Boolean,
    ForeignKey,
    Text,
    BigInteger,
    DateTime,
    Enum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from core.database import Base, TimestampMixin


class InsightType(str, enum.Enum):
    """AI 중재 유형"""

    SUMMARY = "SUMMARY"
    WARNING = "WARNING"
    SUGGESTION = "SUGGESTION"


class User(Base, TimestampMixin):
    """사용자 엔티티"""

    __tablename__ = "user"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    nickname: Mapped[str] = mapped_column(String(100), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

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

    # [DNA Fix] 실제 회의 시작 시간 (HIGH-002)
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="회의 실제 시작 시각"
    )

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

    # [DNA Fix] ID를 BigInteger로 변경 (CRITICAL-003)
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("meeting_room.id"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Unix Timestamp (ms)
    timestamp: Mapped[int] = mapped_column(BigInteger, nullable=False)

    room: Mapped["MeetingRoom"] = relationship(
        "MeetingRoom", back_populates="transcripts"
    )
    user: Mapped["User"] = relationship("User")


class AiInsight(Base, TimestampMixin):
    """AI 분석 결과 엔티티"""

    __tablename__ = "ai_insight"
    __table_args__ = {"extend_existing": True}

    # [DNA Fix] ID를 BigInteger로 변경 (CRITICAL-003)
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("meeting_room.id"), nullable=False, index=True
    )

    # [DNA Fix] Enum 타입 적용 (MEDIUM-002)
    type: Mapped[InsightType] = mapped_column(Enum(InsightType), nullable=False)

    content: Mapped[str] = mapped_column(Text, nullable=False)

    # [DNA Fix] 참조 대화록 ID 추가 (MEDIUM-001)
    ref_transcript_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("transcript.id"), nullable=True, index=True
    )

    room: Mapped["MeetingRoom"] = relationship("MeetingRoom", back_populates="insights")
    ref_transcript: Mapped["Transcript"] = relationship("Transcript")
