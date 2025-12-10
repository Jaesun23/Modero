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
            # 기존 큐가 있다면 정리하고 새로 시작 (또는 정책에 따라 유지)
            await self.stop_stream(user_id)

        self._queues[user_id] = asyncio.Queue()
        logger.info("audio_stream_started", user_id=user_id)

    async def push_audio(self, user_id: str, data: bytes):
        """수신된 오디오 데이터를 큐에 넣습니다."""
        if user_id in self._queues:
            await self._queues[user_id].put(data)
        else:
            # 스트림이 시작되지 않은 상태에서 데이터가 오면 로그를 남기고 무시
            logger.warning("audio_stream_not_found_for_push", user_id=user_id)

    async def get_audio_stream(self, user_id: str) -> AsyncGenerator[bytes, None]:
        """
        큐에서 데이터를 순차적으로 꺼내주는 비동기 제너레이터입니다.
        
        Yields:
            bytes: 오디오 바이너리 청크
            
        종료 조건:
            큐에서 None(Sentinel)을 꺼내면 루프를 종료합니다.
        """
        queue = self._queues.get(user_id)
        if not queue:
            logger.warning("audio_stream_not_found_for_consumption", user_id=user_id)
            return

        try:
            while True:
                # 큐에서 데이터 대기
                chunk = await queue.get()

                # 종료 시그널(None)을 받으면 루프 종료
                if chunk is None:
                    break

                yield chunk
        finally:
            # 스트리밍이 끝나면(정상 종료 혹은 에러) 자원 정리 확인
            # stop_stream에서 이미 del을 수행하지만, 안전을 위해 확인
            pass

    async def stop_stream(self, user_id: str):
        """스트림을 종료하고 자원을 정리합니다."""
        if user_id in self._queues:
            # 소비자가 루프를 탈출할 수 있도록 None(Sentinel) 전달
            await self._queues[user_id].put(None)

            # 큐 자체를 맵에서 제거하여 메모리 누수 방지 (Step 6 리팩토링 항목 선반영)
            del self._queues[user_id]
            logger.info("audio_stream_stopped", user_id=user_id)


# 싱글톤 인스턴스 (필요시 의존성 주입으로 변경 가능)
audio_service = AudioService()
