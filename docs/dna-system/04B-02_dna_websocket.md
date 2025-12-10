# DNA Blueprint: API System (WebSocket  Infrastructure)

## 1. 개요 및 목적 (Purpose & Scope)
- **목적**: 클라이언트와 서버 간의 **저지연(Low-latency) 양방향 통신** 채널을 안정적으로 관리함.
- **핵심 가치**: "끊김 없는 음성 데이터 수신"과 "AI 응답의 즉각적인 스트리밍 전송"을 보장.
- **범위**:
  - WebSocket 연결 수명 주기 관리 (Connect -> Receive/Send -> Disconnect)
  - 단일 서버 내 메모리 기반 연결 관리 (Connection Manager)
  - 표준화된 메시지 프로토콜(JSON) 정의 및 유효성 검증

## 2. 디렉토리 구조 (Directory Structure)

```
src/
 └── core/
 └── websocket/
       ├── init.py       # 공개 API (ConnectionManager 등) 노출
       ├── manager.py        # 연결 객체 관리 (In-memory Store)
       ├── schemas.py        # 송수신 메시지 타입 정의 (Pydantic)
       └── exceptions.py     # WebSocket 전용 예외 (연결 끊김 등)
```

## 3. 핵심 설계 결정 (Key Design Decisions)

### 3.1 In-Memory Connection Manager (No-Redis) 
- **설계**: `Dict[str, WebSocket]` 형태의 전역 싱글톤 객체를 사용하여 활성 연결을 관리함.
- **이유**: `ADR-202`에 따라 Redis를 사용하지 않으므로, 서버 프로세스 메모리 내에서 특정 사용자(`user_id`)나 회의실(`room_id`)을 찾아 메시지를 라우팅해야 함.

### 3.2 비동기 태스크 분리 (Dual-Task Pattern) [cite: 1253]
- **설계**: 하나의 연결에 대해 **수신 루프(Receive Loop)**와 **송신 루프(Send Loop)**를 `asyncio.create_task`로 분리할 수 있는 구조 제공.
- **이유**: `ADR-002`에 따라, STT로 음성을 보내는 동안(Upstream)에도 Gemini의 응답(Downstream)이 멈추지 않고 클라이언트로 내려가야 함. (Full-Duplex)

### 3.3 메시지 프로토콜 표준화
- **설계**: 모든 메시지는 `{ "type": str, "payload": dict, "timestamp": str }` 형식을 강제함.
- **도구**: `Pydantic` 모델을 사용하여 런타임에 메시지 구조를 엄격히 검증.

## 4. 공개 API (Public API)

### `ConnectionManager` 클래스
- **역할**: WebSocket 객체의 저장소이자 방송(Broadcast) 담당.
- **주요 메서드**:
  - `connect(ws: WebSocket, user_id: str) -> None`: 연결 수락 및 메모리 등록.
  - `disconnect(user_id: str) -> None`: 연결 종료 및 메모리 해제.
  - `send_personal_message(message: dict, user_id: str) -> None`: 특정인에게 전송.
  - `broadcast(message: dict, room_id: str) -> None`: 같은 방의 모든 인원에게 전송 (Loop 활용).

### `WebSocketSchema` (Pydantic Model)
- **역할**: 메시지 타입 정의 및 검증.
- **사용법**:
  ```python
  from core.websocket import WebSocketSchema
  # 수신 데이터 검증
  data = WebSocketSchema.model_validate_json(raw_text)

## 5. 의존성 (Dependencies)

- **외부 라이브러리**:
  - `fastapi` (WebSocket 지원)
  - `pydantic` (데이터 검증)
- **내부 의존성**:
  - `core.logging`3: 연결/해제 및 에러 발생 시 `trace_id`와 함께 로깅.
  - `core.types`: `UserId`, `RoomId` 등 공통 타입 사용.

## 6. 테스트 전략 (Testing Strategy)

- **단위 테스트 (`tests/core/websocket/`)**:
  - `TestClient`의 WebSocketContext를 사용하여 연결/해제 시 Manager의 내부 Dict 상태가 올바르게 변하는지 검증.
  - 잘못된 JSON 형식을 보냈을 때 `ValidationError`가 적절히 발생하고 연결이 유지(또는 종료)되는지 확인.
- **목표 커버리지**: 95%+

## 7. 구현 우선순위

1. `schemas.py`: 메시지 프로토콜 정의 (가장 기본)
2. `manager.py`: 연결 관리 로직 (핵심)
3. `__init__.py`: 패키징