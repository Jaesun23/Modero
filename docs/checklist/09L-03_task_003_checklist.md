# 09L-03_task_003_checklist

> Task ID: T003
>
> Task 명: 오디오 수집 및 큐잉 (Audio Ingestion)
>
> 예상 소요: 3 hours
>
> 관련 문서: 03A-002 (비동기 파이프라인), 07B-01 (Section 2)

------

## Step 1: 목표 이해 (Goal Understanding) ✅

### 1.1 Task 목표

- WebSocket 엔드포인트를 통해 클라이언트의 오디오 스트림(Binary)을 수신.
- 수신된 오디오를 `asyncio.Queue`에 넣어, 추후 STT 서비스가 비동기로 소비할 수 있도록 버퍼링.

### 1.2 입력 (Inputs)

- **API**: `src/api/routes/websocket.p` (신규 작성)
- **Service**: `src/domain/services/audio_service.py` (신규 작성)

### 1.3 성공 기준 (Acceptance Criteria)

- [ ] `AudioService`가 사용자별(`user_id`)로 독립된 `Queue`를 생성/관리해야 함.
- [ ] WebSocket에서 받은 바이너리 데이터가 큐에 즉시 삽입되어야 함.
- [ ] `get_audio_stream(user_id)` 제너레이터를 통해 큐의 데이터를 순서대로 꺼낼 수 있어야 함.

------

## Step 2: 테스트 작성 (Test First) 🧪

### 2.1 테스트 시나리오

1. **큐잉 테스트**: `push_audio` 3회 호출 -> `Queue` 사이즈 3 확인.
2. **스트리밍 테스트**: `get_audio_stream`을 `async for`로 소비할 때, 넣은 순서대로 데이터가 나오는지 확인.
3. **종료 신호 테스트**: 연결 종료 시 `None` 등의 센티널 값을 넣어 스트림이 정상 종료되는지 확인.

### 2.2 테스트 파일 경로

- `tests/domain/test_audio_service.py`

------

## Step 3: 구현 (Implementation) 🔨

### 3.1 구현 위치

- `src/domain/services/audio_service.py`
- `src/api/routes/websocket.py`

### 3.2 구현 힌트 (AudioService)

```python
import asyncio
from typing import AsyncGenerator, Dict

class AudioService:
    def __init__(self):
        self._queues: Dict[str, asyncio.Queue] = {}

    async def start_stream(self, user_id: str):
        self._queues[user_id] = asyncio.Queue()

    async def push_audio(self, user_id: str, data: bytes):
        if user_id in self._queues:
            await self._queues[user_id].put(data)

    async def get_audio_stream(self, user_id: str) -> AsyncGenerator[bytes, None]:
        queue = self._queues.get(user_id)
        if not queue: return
        
        while True:
            chunk = await queue.get()
            if chunk is None:  # 종료 시그널
                break
            yield chunk
            
    async def stop_stream(self, user_id: str):
        if user_id in self._queues:
            await self._queues[user_id].put(None) # 종료 시그널 전송
```

------

## Step 4: 정적 검증 (Static Analysis) 🔍

### 4.1 Linting & Type Checking

```bash
ruff check src/domain/services/audio_service.py --fix
mypy src/domain/services/audio_service.py
```

------

## Step 5: 단위 테스트 실행 (Run Tests) ✅

```bash
pytest tests/domain/test_audio_service.py -v
```

------

## Step 6: 리팩토링 (Refactor) 🔄

- [ ] `_queues` 딕셔너리의 키 관리(메모리 누수 방지) 확인. 사용자가 연결을 끊으면(`disconnect`) 해당 큐를 `del` 하는 로직 추가.

------

## Step 7: 통합 테스트 (Integration Test) 🔗

- [ ] WebSocket 엔드포인트(`websocket_endpoint`)에서 `audio_service.push_audio`를 호출하는 흐름 검증. (Mock WebSocket 활용)

------

## Step 8: 문서화 (Documentation) 📝

- [ ] `get_audio_stream` 메서드의 반환 타입(`AsyncGenerator`)과 종료 조건에 대해 Docstring 작성.

------

## Step 9: 커밋 (Commit) ✅

```bash
git add src/domain/services/audio_service.py src/api/endpoints/websocket.py tests/
git commit -m "feat(audio): Implement AudioService with asyncio Queue"
```

------

