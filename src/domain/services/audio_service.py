import asyncio
from typing import AsyncGenerator, Dict
from core.logging import get_logger

logger = get_logger(__name__)


class AudioService:
    def __init__(self):
        # 사용자 ID를 키로, 오디오 데이터 큐를 값으로 저장
        self._queues: Dict[str, asyncio.Queue] = {}

    async def start_stream(self, user_id: str):
        """사용자별 오디오 스트림 큐를 초기화합니다."""
        if user_id in self._queues:
            logger.warning("audio_stream_already_exists", user_id=user_id)
            await self.stop_stream(user_id)

        self._queues[user_id] = asyncio.Queue()
        logger.info("audio_stream_started", user_id=user_id)

    def _is_silence(self, data: bytes, threshold: int = 500) -> bool:
        """
        [DNA Fix] T003: 간단한 VAD(Voice Activity Detection) Placeholder.
        PCM 16bit 데이터의 진폭(Amplitude)을 검사하여 무음 여부를 판단합니다.
        """
        if not data:
            return True

        # 간단한 RMS(Root Mean Square) 계산 대신 최대 진폭으로 약식 검사 (성능 최적화)
        # 실제 프로덕션에서는 webrtcvad 등 전문 라이브러리 사용 권장
        try:
            # 바이트를 int로 변환하여 진폭 검사 (Little Endian, 16bit)
            # 전체를 다 검사하면 느리므로 샘플링 검사
            count = len(data) // 2
            step = max(1, count // 100)  # 100개 샘플만 검사

            for i in range(0, len(data), step * 2):
                if i + 1 >= len(data):
                    break
                sample = int.from_bytes(
                    data[i : i + 2], byteorder="little", signed=True
                )
                if abs(sample) > threshold:
                    return False  # 소리가 감지됨

            return True  # 모든 샘플이 임계값 이하임
        except Exception:
            # 포맷 파싱 에러 시 일단 소리로 간주
            return False

    async def push_audio(self, user_id: str, data: bytes):
        """수신된 오디오 데이터를 큐에 넣습니다."""
        if user_id in self._queues:
            # [DNA Fix] T003: 무음 감지 (VAD) 로직 적용
            if self._is_silence(data):
                # 무음은 큐에 넣지 않거나, 필요 시 특정 마커 처리
                # 여기서는 트래픽 절감을 위해 스킵하되 디버그 로그만 남김
                # logger.debug("silence_detected", user_id=user_id)
                return

            await self._queues[user_id].put(data)
        else:
            logger.warning("audio_stream_not_found_for_push", user_id=user_id)

    async def get_audio_stream(self, user_id: str) -> AsyncGenerator[bytes, None]:
        """
        큐에서 데이터를 순차적으로 꺼내주는 비동기 제너레이터입니다.
        """
        queue = self._queues.get(user_id)
        if not queue:
            logger.warning("audio_stream_not_found_for_consumption", user_id=user_id)
            return

        try:
            while True:
                chunk = await queue.get()
                if chunk is None:
                    break
                yield chunk
        finally:
            pass

    async def stop_stream(self, user_id: str):
        """스트림을 종료하고 자원을 정리합니다."""
        if user_id in self._queues:
            # Sentinel 전달
            await self._queues[user_id].put(None)
            del self._queues[user_id]
            logger.info("audio_stream_stopped", user_id=user_id)


audio_service = AudioService()
