import asyncio
from typing import Any

from core.logging import get_logger
from core.websocket.manager import ConnectionManager
from core.websocket.schemas import WebSocketMessage
from domain.services.audio_service import AudioService
from infrastructure.external.gemini_client import GeminiClient
from infrastructure.external.google_stt import GoogleSTTClient

logger = get_logger(__name__)


class MeetingOrchestrator:
    """
    오디오 스트림 수집 -> STT 변환 -> AI 분석 -> WebSocket 전송을
    담당하는 파이프라인 조정자 클래스입니다.
    """

    def __init__(
        self,
        audio_service: AudioService,
        stt_client: GoogleSTTClient,
        gemini_client: GeminiClient,
        manager: ConnectionManager,
    ):
        self.audio = audio_service
        self.stt = stt_client
        self.gemini = gemini_client
        self.manager = manager

    async def start_processing(self, user_id: str, room_id: str) -> None:
        """
        사용자의 오디오 스트림을 소비하여 STT 및 AI 파이프라인을 실행합니다.
        이 메서드는 별도의 asyncio Task로 실행되어야 합니다.
        """
        logger.info("orchestrator_started", user_id=user_id, room_id=room_id)

        # AudioService에서 오디오 스트림 생성기 획득
        audio_stream = self.audio.get_audio_stream(user_id)

        try:
            # STT 클라이언트에게 오디오 스트림 전달 및 결과 구독
            async for stt_result in self.stt.transcribe(audio_stream):

                # 1. STT 결과를 즉시 WebSocket으로 전송 (낙관적 UI)
                await self._broadcast_message(
                    room_id=room_id, msg_type="stt_result", payload=stt_result
                )

                # 2. 문장이 완성된 경우(Final), Gemini에게 분석 요청
                if stt_result.get("is_final"):
                    transcript_text = stt_result.get("text", "")
                    await self._process_ai_insight(room_id, transcript_text)

        except asyncio.CancelledError:
            logger.info("orchestrator_cancelled", user_id=user_id)
            # 태스크 취소 시 정상 종료 처리
            raise
        except Exception as e:
            logger.error("orchestrator_error", error=str(e), user_id=user_id)
            # 에러 발생 시 클라이언트에게 알림 (선택적)
            await self._broadcast_message(
                room_id=room_id,
                msg_type="system",
                payload={"error": "Processing failed", "details": str(e)},
            )
        finally:
            logger.info("orchestrator_stopped", user_id=user_id)

    async def _process_ai_insight(self, room_id: str, text: str) -> None:
        """Gemini를 호출하고 결과를 브로드캐스트합니다."""
        if not text.strip():
            return

        try:
            # Gemini 호출 (비동기)
            insight = await self.gemini.generate_insight(text)

            # 결과 전송
            await self._broadcast_message(
                room_id=room_id, msg_type="ai_response", payload=insight
            )
        except Exception as e:
            # AI 분석 실패가 전체 파이프라인을 멈추게 하면 안 됨
            logger.warning("ai_processing_failed", error=str(e))

    async def _broadcast_message(
        self, room_id: str, msg_type: str, payload: Any
    ) -> None:
        """WebSocketMessage 스키마에 맞춰 메시지를 전송합니다."""
        message = WebSocketMessage(
            type=msg_type,  # type: ignore[arg-type]
            payload=payload,
        )
        # Pydantic v2: mode='json' converts datetime to string
        await self.manager.broadcast(message.model_dump(mode="json"), room_id)