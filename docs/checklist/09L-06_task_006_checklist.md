# 09L-06_task_006_checklist

> Task ID: T006
>
> Task 명: WebSocket 통합 및 E2E 테스트
>
> 예상 소요: 3 hours
>
> 관련 문서: 07B-01 (Section 2.2)

------

## Step 1: 목표 이해 (Goal Understanding) ✅

### 1.1 Task 목표

- `AudioQueue`(T003) -> `STT`(T004) -> `Gemini`(T005) -> `WebSocket Send`(T002)를 연결하는 메인 파이프라인(`MeetingOrchestrator`)을 완성한다.
- WebSocket 엔드포인트에서 이 파이프라인을 백그라운드 태스크로 실행한다.

### 1.2 입력 (Inputs)

- **Services**: `AudioService`, `GoogleSTTClient`, `GeminiClient`
- **Infrastructure**: `ConnectionManager`

### 1.3 성공 기준 (Acceptance Criteria)

- [ ] 오디오 입력 시 STT 결과가 WebSocket으로 전송되어야 함.
- [ ] STT `is_final=True` 시 Gemini가 호출되고 결과가 전송되어야 함.
- [ ] 연결 종료 시 파이프라인 태스크가 정상적으로 캔슬(Cancel)되어야 함.

------

## Step 2: 테스트 작성 (Test First) 🧪

### 2.1 테스트 시나리오

1. **파이프라인 실행**: `Orchestrator` 실행 시 STT 스트림을 소비하고 결과를 브로드캐스트 하는지 확인(Mock 활용).
2. **연쇄 호출**: STT 결과가 Final일 때만 Gemini Client가 호출되는지 검증.
3. **Graceful Shutdown**: `stop_processing` 호출 시 루프가 종료되는지 확인.

### 2.2 테스트 파일 생성

- 파일: `tests/domain/test_orchestrator.py`
- 코드 스켈레톤:

```python
import pytest
from unittest.mock import AsyncMock
from src.domain.services.meeting_orchestrator import MeetingOrchestrator

@pytest.mark.asyncio
async def test_orchestrator_flow():
    # Mocks
    audio_service = AsyncMock()
    stt_client = AsyncMock()
    gemini_client = AsyncMock()
    manager = AsyncMock()
    
    # STT가 1개의 결과를 주는 상황 모킹
    async def stt_gen(stream):
        yield {"text": "hello", "is_final": True}
    stt_client.transcribe.side_effect = stt_gen
    
    orch = MeetingOrchestrator(audio_service, stt_client, gemini_client, manager)
    await orch.start_processing("user1", "room1")
    
    # Assertions
    gemini_client.generate_insight.assert_called_once() # Final이라 호출되어야 함
    assert manager.broadcast.call_count >= 1
```

------

## Step 3: 구현 (Implementation) 🔨

### 3.1 구현 위치

- `src/domain/services/meeting_orchestrator.py`
- `src/api/endpoints/websocket.py` (최종 수정)

### 3.2 구현 힌트 (Orchestrator)

```python
import asyncio
from src.core.websocket.schemas import WebSocketMessage

class MeetingOrchestrator:
    def __init__(self, audio_service, stt_client, gemini_client, manager):
        self.audio = audio_service
        self.stt = stt_client
        self.gemini = gemini_client
        self.manager = manager

    async def start_processing(self, user_id: str, room_id: str):
        stream = self.audio.get_audio_stream(user_id)
        
        try:
            async for result in self.stt.transcribe(stream):
                # 1. STT 결과 전송
                msg = WebSocketMessage(type="stt_result", payload=result)
                await self.manager.broadcast(msg, room_id)
                
                # 2. Final인 경우 Gemini 호출
                if result.get("is_final"):
                    insight = await self.gemini.generate_insight(result["text"])
                    ai_msg = WebSocketMessage(type="ai_response", payload=insight)
                    await self.manager.broadcast(ai_msg, room_id)
                    
        except asyncio.CancelledError:
            pass # 정상 종료
        except Exception as e:
            # 로깅 후 종료 (연결 하나 에러가 서버 전체를 죽이지 않도록)
            pass
```

### 3.3 Endpoint 연결

```python
# src/api/endpoints/websocket.py
@router.websocket("/ws/{room_id}")
async def websocket_endpoint(...):
    # ... 연결 수락 ...
    orchestrator = MeetingOrchestrator(...)
    
    # 파이프라인을 별도 태스크로 실행
    process_task = asyncio.create_task(orchestrator.start_processing(user.sub, room_id))
    
    try:
        while True:
            data = await websocket.receive_bytes()
            await audio_service.push_audio(user.sub, data)
    except WebSocketDisconnect:
        # ... 정리 ...
        process_task.cancel() # 태스크 종료
        await process_task
```

------

## Step 4: 정적 검증 (Static Analysis) 🔍

### 4.1 Linting

```bash
ruff check src/domain/services/meeting_orchestrator.py src/api/endpoints/websocket.py --fix
```

### 4.2 Type Checking

```bash
mypy src/domain/services/meeting_orchestrator.py
```

------

## Step 5: 단위 테스트 실행 (Run Tests) ✅

### 5.1 테스트 실행

```bash
pytest tests/domain/test_orchestrator.py -v
```

### 5.2 커버리지 확인

```bash
pytest --cov=src/domain/services/meeting_orchestrator.py tests/domain/test_orchestrator.py
```

------

## Step 6: 리팩토링 (Refactor) 🔄

- [ ] Orchestrator 클래스를 DI(Dependency Injection) 받도록 `src/api/dependencies.py`에 팩토리 함수 추가 고려.
- [ ] 에러 발생 시 클라이언트에게 에러 메시지를 전송하는 로직(`manager.send_personal_message`) 추가.

------

## Step 7: 통합 테스트 (Integration Test) 🔗

- [ ] `tests/e2e/test_meeting_flow.py` (T006용) 작성 및 실행.
- [ ] Mock 객체들을 사용하여 Audio Input -> STT Output -> AI Output이 순차적으로 발생하는지 전체 흐름 검증.

------

## Step 8: 문서화 (Documentation) 📝

- [ ] Orchestrator의 역할과 데이터 흐름을 설명하는 Docstring 작성.
- [ ] `WebSocketMessage` 스키마(JSON 구조)를 API 문서(Swagger/README)에 명시.

------

## Step 9: 커밋 (Commit) ✅

### 9.1 Pre-commit 확인

- [ ] 전체 테스트 슈트 실행 (`pytest`) -> All Pass 확인.

### 9.2 Git Commit

```bash
git add src/domain/services/meeting_orchestrator.py src/api/endpoints/websocket.py tests/
git commit -m "feat(core): Complete real-time pipeline orchestration"
```

------

