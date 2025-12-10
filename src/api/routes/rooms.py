import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_session
from domain.models import MeetingRoom
from api.schemas.rooms import CreateRoomRequest, RoomResponse

# HTTP용 get_current_user가 있다면 그것을 사용. 여기서는 user_id가 필요함.

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.post("", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room(
    request: CreateRoomRequest,
    # TODO: 실제 인증 의존성 주입 필요. 임시로 user_id를 하드코딩하거나 Mocking 가능한 구조 사용
    # current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """새로운 회의실을 생성합니다."""
    # 임시 호스트 ID (실제로는 current_user.sub 사용)
    # Task 001 테스트에서 생성된 User ID를 사용해야 FK 에러가 안남.
    # 여기서는 데모를 위해 로직만 작성
    dummy_host_id = uuid.uuid4()

    new_room = MeetingRoom(
        title=request.title,
        host_id=dummy_host_id,  # 실제 구현 시 current_user.sub (UUID 변환 필요)
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