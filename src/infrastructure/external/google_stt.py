from typing import AsyncGenerator, Dict, Any, Optional
from google.cloud import speech
from google.api_core import exceptions as google_exceptions

from core.config import get_settings
from core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class GoogleSTTClient:
    """
    Google Cloud Speech-to-Text 비동기 스트리밍 클라이언트
    """

    def __init__(self, client: Optional[speech.SpeechAsyncClient] = None):
        # 의존성 주입 또는 기본 클라이언트 생성 (테스트 용이성 확보)
        self.client = client or speech.SpeechAsyncClient()
        self._language_code = "ko-KR"
        self._sample_rate = 16000

    def _create_streaming_config(self) -> speech.StreamingRecognitionConfig:
        """STT 스트리밍 설정을 생성합니다."""
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=self._sample_rate,
            language_code=self._language_code,
        )
        return speech.StreamingRecognitionConfig(
            config=config,
            interim_results=True,  # 중간 결과 포함 (실시간 피드백용)
        )

    async def _request_generator(
        self,
        streaming_config: speech.StreamingRecognitionConfig,
        audio_stream: AsyncGenerator[bytes, None],
    ) -> AsyncGenerator[speech.StreamingRecognizeRequest, None]:
        """
        gRPC 스트리밍 요청을 생성합니다.
        첫 번째 요청은 설정(Config)을 포함하고, 이후 요청은 오디오 청크를 포함합니다.
        """
        # 첫 번째 요청: Config 전송
        yield speech.StreamingRecognizeRequest(streaming_config=streaming_config)

        # 이후 요청: 오디오 데이터 스트리밍
        async for chunk in audio_stream:
            yield speech.StreamingRecognizeRequest(audio_content=chunk)

    async def transcribe(
        self, audio_stream: AsyncGenerator[bytes, None]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        오디오 스트림을 입력받아 실시간으로 텍스트 인식 결과를 반환합니다.

        Yields:
            Dict: {
                "text": str,       # 인식된 텍스트
                "is_final": bool,  # 최종 결과 여부
                "type": str        # "final" | "interim"
            }
        """
        streaming_config = self._create_streaming_config()
        requests = self._request_generator(streaming_config, audio_stream)

        try:
            # Google STT API 호출 (비동기 스트리밍)
            responses = await self.client.streaming_recognize(requests=requests)

            async for response in responses:
                if not response.results:
                    continue

                # 가장 신뢰도 높은 결과 하나만 처리
                result = response.results[0]
                if not result.alternatives:
                    continue

                transcript = result.alternatives[0].transcript
                is_final = result.is_final

                # 로그는 구조화된 형태로 남김 (표준 준수)
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

        except google_exceptions.GoogleAPICallError as e:
            # 외부 API 에러 처리
            logger.error("stt_api_error", error=str(e))
            raise e
        except Exception as e:
            # 기타 예외 처리
            logger.error("stt_unknown_error", error=str(e))
            raise e