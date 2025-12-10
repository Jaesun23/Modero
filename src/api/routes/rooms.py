import uuid
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_session
from domain.models import MeetingRoom
from api.schemas.rooms import CreateRoomRequest, RoomResponse
from core.security import get_current_user, TokenPayload
from core.websocket.manager import manager  # [DNA Fix] 소켓 매니저 임포트

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
            detail="Invalid user ID format in token",
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


@router.patch("/{room_id}/close", status_code=status.HTTP_200_OK)
async def close_room(
    room_id: uuid.UUID,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    [DNA Fix] 회의를 종료하고 모든 참여자의 WebSocket 연결을 끊습니다.
    오직 방장(Host)만 실행할 수 있습니다.
    """
    # 1. 회의실 조회
    stmt = select(MeetingRoom).where(MeetingRoom.id == room_id)
    result = await db.execute(stmt)
    room = result.scalar_one_or_none()

    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    # 2. 권한 체크 (방장 여부)
    if str(room.host_id) != current_user.sub:
        raise HTTPException(status_code=403, detail="Only host can close the meeting")

    # 3. DB 상태 업데이트
    if room.is_active:
        room.is_active = False
        await db.commit()

    # 4. WebSocket 강제 종료 브로드캐스트
    room_id_str = str(room_id)
    close_message = {
        "type": "system",
        "payload": {
            "event": "meeting_closed",
            "message": "The host has closed the meeting.",
        },
    }

    # 먼저 종료 메시지 전송
    await manager.broadcast(close_message, room_id_str)

    # 해당 방의 모든 연결 강제 해제 (서버 측 close)
    # 딕셔너리 변경 방지를 위해 리스트로 복사
    active_users = list(manager.active_connections[room_id_str].items())
    for user_id, ws in active_users:
        try:
            await ws.close(code=status.WS_1000_NORMAL_CLOSURE)
        except Exception:
            pass  # 이미 닫힌 경우 무시
        finally:
            manager.disconnect(room_id_str, user_id)

    return {"message": "Meeting closed successfully"}
