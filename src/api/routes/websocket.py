from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from core.logging import get_logger
from core.websocket.manager import manager
from domain.services.audio_service import audio_service
from core.security import get_current_user_ws, TokenPayload

router = APIRouter()
logger = get_logger(__name__)


@router.websocket("/ws/audio/{room_id}")
async def audio_websocket_endpoint(
    websocket: WebSocket,
    room_id: str,
    # WebSocket 연결 시 토큰 검증 (Query Param)
    token_payload: TokenPayload = Depends(get_current_user_ws),
):
    user_id = token_payload.sub

    # 1. 연결 수락 및 관리자에 등록
    await manager.connect(websocket, room_id, user_id)

    # 2. 오디오 스트림 큐 초기화
    await audio_service.start_stream(user_id)

    try:
        while True:
            # 3. 바이너리 데이터(오디오) 수신
            data = await websocket.receive_bytes()

            # 4. 오디오 서비스 큐에 푸시
            await audio_service.push_audio(user_id, data)

    except WebSocketDisconnect:
        logger.info("websocket_disconnected", user_id=user_id, room_id=room_id)
        # 연결 종료 시 처리
        manager.disconnect(room_id, user_id)
        await audio_service.stop_stream(user_id)

    except Exception as e:
        logger.error("websocket_error", error=str(e), user_id=user_id)
        # 에러 발생 시에도 안전하게 종료 처리
        manager.disconnect(room_id, user_id)
        await audio_service.stop_stream(user_id)