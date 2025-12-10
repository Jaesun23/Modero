import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_session
from domain.models import MeetingRoom
from api.schemas.rooms import CreateRoomRequest, RoomResponse
from core.security import get_current_user, TokenPayload

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.post("", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room(
    request: CreateRoomRequest,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """새로운 회의실을 생성합니다."""
    try:
        # 토큰의 sub(Subject)를 UUID로 변환하여 Host ID로 사용
        host_id = uuid.UUID(current_user.sub)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Invalid user ID format in token"
        )

    new_room = MeetingRoom(
        title=request.title,
        host_id=host_id,
        is_active=True,
    )

    db.add(new_room)
    await db.commit()
    await db.refresh(new_room)

    return new_room


@router.get("/{room_id}", response_model=RoomResponse)
async def get_room(room_id: uuid.UUID, db: AsyncSession = Depends(get_session)):
    """회의실 정보를 조회합니다."""
    stmt = select(MeetingRoom).where(MeetingRoom.id == room_id)
    result = await db.execute(stmt)
    room = result.scalar_one_or_none()

    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Room not found"
        )

    return room
