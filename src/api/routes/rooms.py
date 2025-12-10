import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_session
from domain.services.room_service import room_service
from api.schemas.rooms import CreateRoomRequest, RoomResponse
from core.security import get_current_user, TokenPayload
from core.websocket.manager import manager

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.post("", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room(
    request: CreateRoomRequest,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """새로운 회의실을 생성합니다."""
    try:
        host_id = uuid.UUID(current_user.sub)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")

    room = await room_service.create_room(db, request.title, host_id)
    return room


@router.get("/{room_id}", response_model=RoomResponse)
async def get_room(room_id: uuid.UUID, db: AsyncSession = Depends(get_session)):
    """회의실 정보를 조회합니다."""
    room = await room_service.get_room(db, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room


@router.patch("/{room_id}/close", status_code=status.HTTP_200_OK)
async def close_room(
    room_id: uuid.UUID,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    [DNA Fix] CRITICAL-001: 회의 종료 및 웹소켓 연결 해제
    """
    try:
        # DB 상태 업데이트 (Service 위임)
        await room_service.close_room(db, room_id, current_user.sub)

        # WebSocket 강제 종료 (Manager 위임)
        await manager.disconnect_room(str(room_id))

        return {"message": "Meeting closed successfully"}

    except ValueError:
        raise HTTPException(status_code=404, detail="Room not found")
    except PermissionError:
        raise HTTPException(status_code=403, detail="Only host can close the meeting")


@router.get("/{room_id}/history/transcripts")
async def get_transcripts_history(
    room_id: uuid.UUID,
    cursor: Optional[int] = Query(None, description="Last seen ID for pagination"),
    limit: int = Query(50, le=100),
    db: AsyncSession = Depends(get_session),
):
    """[DNA Fix] HIGH-001: 대화록 페이징 조회"""
    return await room_service.get_transcripts_history(db, room_id, cursor, limit)


@router.get("/{room_id}/history/insights")
async def get_insights_history(
    room_id: uuid.UUID,
    cursor: Optional[int] = Query(None, description="Last seen ID for pagination"),
    limit: int = Query(20, le=50),
    db: AsyncSession = Depends(get_session),
):
    """[DNA Fix] HIGH-001: AI 인사이트 페이징 조회"""
    return await room_service.get_insights_history(db, room_id, cursor, limit)
