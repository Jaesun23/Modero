# 09L-02_task_002_checklist

> Task ID: T002
>
> Task 명: 회의실 API & 연결 관리자(ConnectionManager) 고도화
>
> 예상 소요: 3 hours
>
> 관련 문서: 07B-01 (Section 4), 04B-02 (DNA: WebSocket)

------

## Step 1: 목표 이해 (Goal Understanding) ✅

### 1.1 Task 목표

- 회의실 생성(`POST /rooms`) 및 조회(`GET /rooms/{id}`) API 구현.
- `ConnectionManager`를 고도화하여 **방(Room)** 단위로 WebSocket 연결을 관리하고 브로드캐스트 구현.

### 1.2 입력 (Inputs)

- **Core**: `src/core/websocket/manager.py`
- **Domain**: `src/domain/models.py` (MeetingRoom 엔티티)

### 1.3 성공 기준 (Acceptance Criteria)

- [ ] API를 통해 회의실을 생성하면 DB에 저장되고 `room_id`가 반환됨.
- [ ] WebSocket 연결 시 `manager.active_connections[room_id]`에 정상 등록됨.
- [ ] `manager.broadcast(room_id, msg)` 호출 시 해당 방 인원에게만 메시지 전송됨.

------

## Step 2: 테스트 작성 (Test First) 🧪

### 2.1 테스트 시나리오

1. **방 생성 API**: 유효한 토큰으로 요청 시 201 Created 및 UUID 반환.
2. **WebSocket 방 격리**:
   - User A (Room 1), User B (Room 1), User C (Room 2) 연결.
   - Room 1에 메시지 전송 -> A, B만 수신 확인. C는 수신 X.
3. **방 종료**: 방 종료 API 호출 -> Room 1의 모든 소켓 연결 끊김 확인.

### 2.2 테스트 파일 경로

- `tests/api/test_rooms.py`
- `tests/core/websocket/test_manager_room.py`

------

## Step 3: 구현 (Implementation) 🔨

### 3.1 구현 위치

- `src/api/routes/rooms.py`
- `src/api/schemas/rooms.py` (Pydantic DTO)
- `src/core/websocket/manager.py` (수정)

### 3.2 구현 힌트 (ConnectionManager)

```python
# src/core/websocket/manager.py
from collections import defaultdict

class ConnectionManager:
    def __init__(self):
        # {room_id: {user_id: websocket}}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = defaultdict(dict)

    async def connect(self, websocket: WebSocket, room_id: str, user_id: str):
        await websocket.accept()
        self.active_connections[room_id][user_id] = websocket

    async def broadcast(self, message: dict, room_id: str):
        if room_id in self.active_connections:
            # 방 안의 모든 연결에 대해 비동기 전송 (gather 권장 아님 - 에러 격리 위해 루프 사용)
            for ws in self.active_connections[room_id].values():
                await ws.send_json(message)
```

------

## Step 4: 정적 검증 (Static Analysis) 🔍

### 4.1 Linting & Formatting

```bash
ruff check src/api src/core/websocket --fix
ruff format src/api src/core/websocket
```

### 4.2 Type Checking

```bash
mypy src/api src/core/websocket
```

------

## Step 5: 단위 테스트 실행 (Run Tests) ✅

### 5.1 테스트 실행

```bash
pytest tests/api/test_rooms.py tests/core/websocket/test_manager_room.py -v
```

### 5.2 커버리지 확인

```bash
pytest --cov=src/api/routes --cov=src/core/websocket tests/api/test_rooms.py tests/core/websocket/test_manager_room.py
```

------

## Step 6: 리팩토링 (Refactor) 🔄

- [ ] `broadcast` 메서드에서 예외 발생 시(연결 끊김 등) 해당 소켓을 `disconnect` 처리하는 로직 추가.
- [ ] API 라우터 함수명을 RESTful하게 정리 (`create_room`, `get_room`).

------

## Step 7: 통합 테스트 (Integration Test) 🔗

- [ ] `TestClient`를 사용하여 API로 방 생성 -> 생성된 ID로 WebSocket 연결 시도 -> 성공 확인.

------

## Step 8: 문서화 (Documentation) 📝

- [ ] `src/api/routes/rooms.py`의 각 엔드포인트에 `summary`, `response_model` 명시 (Swagger UI용).

------

## Step 9: 커밋 (Commit) ✅

```bash
git add src/api/ src/core/websocket/ tests/
git commit -m "feat(api): Room CRUD and WebSocket room management"
```

------

