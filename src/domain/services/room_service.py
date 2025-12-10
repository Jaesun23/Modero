import uuid
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from domain.models import MeetingRoom, Transcript, AiInsight
from core.logging import get_logger

logger = get_logger(__name__)


class RoomService:
    """회의실 관련 비즈니스 로직을 처리하는 도메인 서비스"""

    async def create_room(
        self, db: AsyncSession, title: str, host_id: uuid.UUID
    ) -> MeetingRoom:
        """회의실을 생성합니다."""
        new_room = MeetingRoom(
            title=title,
            host_id=host_id,
            is_active=True,
            # started_at은 첫 사용자가 입장하거나 명시적 시작 시 업데이트 가능
            # 여기서는 생성 시점엔 None으로 둠
        )
        db.add(new_room)
        await db.commit()
        await db.refresh(new_room)

        logger.info("room_created", room_id=new_room.id, host_id=host_id)
        return new_room

    async def get_room(
        self, db: AsyncSession, room_id: uuid.UUID
    ) -> Optional[MeetingRoom]:
        """회의실 정보를 조회합니다."""
        stmt = select(MeetingRoom).where(MeetingRoom.id == room_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def close_room(
        self, db: AsyncSession, room_id: uuid.UUID, user_id: str
    ) -> MeetingRoom:
        """
        회의를 종료합니다. (방장 권한 체크 포함)
        """
        room = await self.get_room(db, room_id)
        if not room:
            raise ValueError("Room not found")

        if str(room.host_id) != user_id:
            raise PermissionError("Only host can close the meeting")

        if room.is_active:
            room.is_active = False
            await db.commit()
            await db.refresh(room)
            logger.info("room_closed", room_id=room_id, user_id=user_id)

        return room

    async def get_transcripts_history(
        self,
        db: AsyncSession,
        room_id: uuid.UUID,
        cursor: Optional[int] = None,
        limit: int = 50,
    ) -> List[Transcript]:
        """대화록 이력을 페이징 조회합니다 (Cursor-based)."""
        stmt = select(Transcript).where(Transcript.room_id == room_id)

        if cursor:
            stmt = stmt.where(Transcript.id < cursor)

        stmt = stmt.order_by(desc(Transcript.id)).limit(limit)

        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_insights_history(
        self,
        db: AsyncSession,
        room_id: uuid.UUID,
        cursor: Optional[int] = None,
        limit: int = 20,
    ) -> List[AiInsight]:
        """AI 인사이트 이력을 페이징 조회합니다."""
        stmt = select(AiInsight).where(AiInsight.room_id == room_id)

        if cursor:
            stmt = stmt.where(AiInsight.id < cursor)

        stmt = stmt.order_by(desc(AiInsight.id)).limit(limit)

        result = await db.execute(stmt)
        return list(result.scalars().all())


# 싱글톤 인스턴스
room_service = RoomService()
