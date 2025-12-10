import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from core.logging import get_logger
from core.logging.context import bind_context, generate_trace_id, clear_context
from core.websocket.manager import manager
from domain.services.audio_service import audio_service
from core.security import get_current_user_ws, TokenPayload

# 클래스 자체를 임포트 (테스트에서 monkeypatch로 교체하기 위함)
from infrastructure.external.google_stt import GoogleSTTClient
from infrastructure.external.gemini_client import GeminiClient
from domain.services.meeting_orchestrator import MeetingOrchestrator

router = APIRouter()
logger = get_logger(__name__)


@router.websocket("/ws/audio/{room_id}")
async def audio_websocket_endpoint(
    websocket: WebSocket,
    room_id: str,
    token_payload: TokenPayload = Depends(get_current_user_ws),
):
    user_id = token_payload.sub

    # [DNA Fix] Trace ID 생성 및 컨텍스트 바인딩
    trace_id = generate_trace_id()
    bind_context(trace_id=trace_id, user_id=user_id, room_id=room_id)

    logger.info("websocket_connection_init", trace_id=trace_id)

    # 1. 연결 수락
    await manager.connect(websocket, room_id, user_id)

    # 2. 오디오 스트림 시작
    await audio_service.start_stream(user_id)

    # 3. Orchestrator 초기화
    stt_client = GoogleSTTClient()
    gemini_client = GeminiClient()

    orchestrator = MeetingOrchestrator(
        audio_service=audio_service,
        stt_client=stt_client,
        gemini_client=gemini_client,
        manager=manager,
    )

    # 4. 백그라운드 태스크 실행 (Process Task)
    # Trace ID 컨텍스트가 이 Task 내부로 전파되도록 함 (Python 3.7+ asyncio 기본 동작)
    process_task = asyncio.create_task(orchestrator.start_processing(user_id, room_id))

    try:
        while True:
            # 클라이언트로부터 오디오 데이터 수신
            data = await websocket.receive_bytes()
            # 오디오 서비스 큐에 넣기
            await audio_service.push_audio(user_id, data)

    except WebSocketDisconnect:
        logger.info("websocket_disconnected", user_id=user_id, room_id=room_id)
    except Exception as e:
        logger.error("websocket_error", error=str(e), user_id=user_id)
    finally:
        # 정리 작업
        manager.disconnect(room_id, user_id)
        await audio_service.stop_stream(user_id)

        # 태스크 취소 및 대기
        if not process_task.done():
            process_task.cancel()
            try:
                await process_task
            except asyncio.CancelledError:
                pass
            except Exception as task_e:
                logger.error("orchestrator_task_error", error=str(task_e))

        # 컨텍스트 정리
        clear_context()
