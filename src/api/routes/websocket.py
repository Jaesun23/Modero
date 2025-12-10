import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from core.logging import get_logger
from core.security import get_current_user_ws, TokenPayload
from api.dependencies import (
    AudioServiceDep,
    MeetingOrchestratorDep,
    ConnectionManagerDep,
)

router = APIRouter()
logger = get_logger(__name__)


@router.websocket("/ws/audio/{room_id}")
async def audio_websocket_endpoint(
    websocket: WebSocket,
    room_id: str,
    # Parameters without default values first
    audio_service: AudioServiceDep,
    manager: ConnectionManagerDep,
    orchestrator: MeetingOrchestratorDep,
    # Parameters with default values last
    token_payload: TokenPayload = Depends(get_current_user_ws),
):
    user_id = token_payload.sub

    # 1. 연결 수락 및 관리자에 등록
    await manager.connect(websocket, room_id, user_id)

    # 2. 오디오 스트림 큐 초기화
    await audio_service.start_stream(user_id)

    # 3. 파이프라인을 백그라운드 태스크로 실행
    # 클라이언트가 오디오를 보내는 루프(Main Loop)와
    # 오디오를 처리해서 응답을 보내는 루프(Orchestrator Task)를 분리 (Dual-Task Pattern)
    process_task = asyncio.create_task(orchestrator.start_processing(user_id, room_id))

    try:
        while True:
            # 4. 바이너리 데이터(오디오) 수신
            data = await websocket.receive_bytes()

            # 5. 오디오 서비스 큐에 푸시 -> Orchestrator가 소비함
            await audio_service.push_audio(user_id, data)

    except WebSocketDisconnect:
        logger.info("websocket_disconnected", user_id=user_id, room_id=room_id)
    except Exception as e:
        logger.error("websocket_error", error=str(e), user_id=user_id)
    finally:
        # 6. 자원 정리 및 태스크 종료
        manager.disconnect(room_id, user_id)

        # 오디오 스트림 종료 신호 (Orchestrator 루프 탈출 유도)
        await audio_service.stop_stream(user_id)

        # 태스크 강제 취소 (혹시 루프가 안 끝났을 경우 대비)
        if not process_task.done():
            process_task.cancel()
            try:
                await process_task
            except asyncio.CancelledError:
                pass