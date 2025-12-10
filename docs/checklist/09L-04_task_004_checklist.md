# 09L-04_task_004_checklist

> Task ID: T004
>
> Task 명: Google Cloud STT 스트리밍 연동
>
> 예상 소요: 4 hours
>
> 관련 문서: 03A-002 (ADR: 스트리밍), 07B-01 (Section 2.1)

------

## Step 1: 목표 이해 (Goal Understanding) ✅

### 1.1 Task 목표

- `AudioService` 큐에서 오디오 청크를 소비하여 Google Cloud STT API에 스트리밍으로 전송한다.
- 실시간으로 반환되는 인식 결과(`StreamingRecognizeResponse`)를 처리하여, 중간 결과(Interim)와 최종 결과(Final)를 구분해 반환한다.

### 1.2 입력 (Inputs)

- **Core**: `core.config` (Google Credentials 환경변수)
- **Domain**: `src/domain/services/audio_service.py` (T003 산출물 - 오디오 스트림 소스)
- **Libraries**: `google-cloud-speech` (비동기 클라이언트 사용)

### 1.3 성공 기준 (Acceptance Criteria)

- [ ] `SpeechAsyncClient`를 사용하여 비동기 스트리밍 인식이 동작해야 함.
- [ ] STT 결과가 `Interim`(회색 표시용)과 `Final`(확정용)로 명확히 구분되어야 함.
- [ ] 네트워크 단절 시 재연결(Retry) 로직이 포함되어야 함.

------

## Step 2: 테스트 작성 (Test First) 🧪

### 2.1 테스트 시나리오

1. **설정 검증**: `StreamingRecognitionConfig` 객체가 `ko-KR`, `16000Hz` 등으로 올바르게 생성되는지 확인.
2. **요청 생성기 검증**: 오디오 큐(`AsyncGenerator`)의 데이터가 `StreamingRecognizeRequest` 객체로 올바르게 매핑되는지 확인.
3. **응답 파싱**: Mock STT 클라이언트가 `is_final=True`인 응답을 줄 때, 서비스가 이를 텍스트로 추출하여 반환하는지 테스트.

### 2.2 테스트 파일 생성

- 파일: `tests/infrastructure/test_google_stt.py`
- 코드 스켈레톤:

```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.infrastructure.external.google_stt import GoogleSTTClient

@pytest.mark.asyncio
async def test_stt_streaming_config():
    client = GoogleSTTClient()
    config = client._create_config()
    assert config.config.language_code == "ko-KR"
    assert config.config.encoding == 1 # LINEAR16
    assert config.interim_results is True

@pytest.mark.asyncio
async def test_recognize_stream_processing():
    # Mock STT Client & Response
    mock_speech_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.results = [MagicMock(alternatives=[MagicMock(transcript="테스트")], is_final=True)]
    
    # Async Iterator mocking
    async def response_generator():
        yield mock_response

    mock_speech_client.streaming_recognize.return_value = response_generator()
    
    client = GoogleSTTClient(client=mock_speech_client)
    async for result in client.transcribe(AsyncMock()): # Mock Audio Stream
        assert result.text == "테스트"
        assert result.is_final is True
```

------

## Step 3: 구현 (Implementation) 🔨

### 3.1 구현 위치

- `src/infrastructure/external/google_stt.py`
- `src/domain/services/transcription_service.py`

### 3.2 구현 힌트 (GoogleSTTClient)

```python
from typing import AsyncGenerator
from google.cloud import speech_v1
from core.config import get_settings

class GoogleSTTClient:
    def __init__(self, client: speech_v1.SpeechAsyncClient = None):
        self.client = client or speech_v1.SpeechAsyncClient()
        self.settings = get_settings()

    def _create_config(self) -> speech_v1.StreamingRecognitionConfig:
        return speech_v1.StreamingRecognitionConfig(
            config=speech_v1.RecognitionConfig(
                encoding=speech_v1.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code="ko-KR",
            ),
            interim_results=True,
        )

    async def transcribe(self, audio_stream: AsyncGenerator[bytes, None]):
        """오디오 스트림을 받아 STT 결과를 yield함"""
        config = self._create_config()
        
        # 요청 제너레이터 (첫 요청은 설정, 이후는 오디오)
        async def request_generator():
            yield speech_v1.StreamingRecognizeRequest(streaming_config=config)
            async for chunk in audio_stream:
                yield speech_v1.StreamingRecognizeRequest(audio_content=chunk)

        # 스트리밍 호출
        responses = await self.client.streaming_recognize(requests=request_generator())
        
        async for response in responses:
            if not response.results:
                continue
            result = response.results[0]
            if not result.alternatives:
                continue
                
            yield {
                "text": result.alternatives[0].transcript,
                "is_final": result.is_final
            }
```

### 3.3 프로젝트 표준 준수

- **의존성**: `pyproject.toml`에 `google-cloud-speech` 추가.
- **Async**: 반드시 `SpeechAsyncClient` 사용 (동기 클라이언트 사용 시 전체 서버 블로킹됨).

------

## Step 4: 정적 검증 (Static Analysis) 🔍

### 4.1 Linting

```bash
ruff check src/infrastructure/external/google_stt.py tests/infrastructure/test_google_stt.py --fix
```

### 4.2 Type Checking

```bash
mypy src/infrastructure/external/google_stt.py
```

------

## Step 5: 단위 테스트 실행 (Run Tests) ✅

### 5.1 테스트 실행

```bash
pytest tests/infrastructure/test_google_stt.py -v
```

### 5.2 커버리지 확인

```bash
pytest --cov=src/infrastructure/external --cov-report=term-missing tests/infrastructure/test_google_stt.py
```

- **목표**: Coverage 95% 이상.

------

## Step 6: 리팩토링 (Refactor) 🔄

- [ ] `_create_config` 메서드에서 매직 넘버(16000, "ko-KR")를 상수로 분리.
- [ ] 예외 처리: `GoogleAPICallError` 발생 시 로그를 남기고 스트림을 안전하게 종료하는 로직 추가.

------

## Step 7: 통합 테스트 (Integration Test) 🔗

- [ ] 실제 Google Credentials가 있는 경우, 로컬에서 실제 API를 한 번 호출해보고 응답이 오는지 확인 (선택 사항, 비용 발생 주의).
- [ ] Mock을 사용한 통합 테스트는 Step 2에서 작성한 것으로 대체 가능.

------

## Step 8: 문서화 (Documentation) 📝

- [ ] `transcribe` 메서드의 Docstring 작성 (입력: `AsyncGenerator[bytes]`, 출력: `AsyncGenerator[dict]`).
- [ ] `google-cloud-speech` 라이브러리 버전 명시 (`requirements.txt` 또는 `pyproject.toml`).

------

## Step 9: 커밋 (Commit) ✅

### 9.1 Pre-commit 확인

- [ ] Ruff, Mypy, Pytest 통과 확인.

### 9.2 Git Commit

```bash
git add src/infrastructure/external/google_stt.py tests/infrastructure/test_google_stt.py pyproject.toml
git commit -m "feat(infra): Implement Google STT async streaming client"
```

------

