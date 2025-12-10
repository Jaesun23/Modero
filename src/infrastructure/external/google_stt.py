import asyncio
from typing import AsyncGenerator, Dict, Any, Optional
from google.cloud import speech
from google.api_core import exceptions as google_exceptions # Google API 관련 예외
import grpc.aio # grpc.aio.AioRpcError를 사용하기 위함 (TransportError 대체)

from core.config import get_settings
from core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class GoogleSTTClient:
    """
    Google Cloud Speech-to-Text 비동기 스트리밍 클라이언트
    """

    def __init__(self, client: Optional[speech.SpeechAsyncClient] = None):
        self.client = client or speech.SpeechAsyncClient()
        self._language_code = "ko-KR"
        self._sample_rate = 16000

    def _create_streaming_config(self) -> speech.StreamingRecognitionConfig:
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=self._sample_rate,
            language_code=self._language_code,
        )
        return speech.StreamingRecognitionConfig(
            config=config,
            interim_results=True,
        )

    async def _request_generator(
        self,
        streaming_config: speech.StreamingRecognitionConfig,
        audio_stream: AsyncGenerator[bytes, None],
    ) -> AsyncGenerator[speech.StreamingRecognizeRequest, None]:
        yield speech.StreamingRecognizeRequest(streaming_config=streaming_config)
        async for chunk in audio_stream:
            yield speech.StreamingRecognizeRequest(audio_content=chunk)

    async def transcribe(
        self, audio_stream: AsyncGenerator[bytes, None]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        오디오 스트림을 입력받아 실시간으로 텍스트 인식 결과를 반환합니다.
        [DNA Fix] T004: 네트워크 오류 시 자동 재연결(Retry) 로직 포함.
        """
        retry_count = 0
        max_retries = 3

        # 스트림 재연결 루프
        while True:
            streaming_config = self._create_streaming_config()
            # 주의: audio_stream 제너레이터는 한 번 소비되면 재사용이 불가능하므로,
            # 실제 프로덕션에서는 버퍼링된 스트림을 사용하거나
            # 큐에서 다시 가져오는 구조가 필요할 수 있음.
            # 여기서는 연결 끊김 시점 이후의 데이터부터 다시 보낸다고 가정(AudioService Queue 지속)
            requests = self._request_generator(streaming_config, audio_stream)

            try:
                responses = await self.client.streaming_recognize(requests=requests)

                async for response in responses:
                    # 정상 응답 수신 시 재시도 카운트 초기화
                    retry_count = 0

                    if not response.results:
                        continue

                    result = response.results[0]
                    if not result.alternatives:
                        continue

                    transcript = result.alternatives[0].transcript
                    is_final = result.is_final

                    if is_final:
                        logger.info(
                            "stt_transcript_final",
                            transcript=transcript,
                            confidence=result.alternatives[0].confidence,
                        )

                    yield {
                        "text": transcript,
                        "is_final": is_final,
                        "type": "final" if is_final else "interim",
                    }

                # 정상적인 스트림 종료 (Loop break)
                break

            except (
                google_exceptions.ServiceUnavailable,
                # TransportError 대신 gRPC의 AioRpcError를 사용하여 포괄적인 네트워크 오류 처리
                grpc.aio.AioRpcError,
            ) as e:
                # [DNA Fix] 일시적인 네트워크/서버 오류 시 재연결 시도
                retry_count += 1
                if retry_count > max_retries:
                    logger.error("stt_max_retries_exceeded", error=str(e))
                    raise e

                logger.warning(
                    "stt_connection_lost_retrying", retry=retry_count, error=str(e)
                )
                await asyncio.sleep(0.5 * retry_count)  # Backoff
                continue

            except Exception as e:
                # 복구 불가능한 에러
                logger.error("stt_fatal_error", error=str(e))
                raise e