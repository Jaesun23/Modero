# 프로젝트: AI Moderator - Blueprint

> 프로젝트: AI Moderator (실시간 회의 중재 시스템)
>
> 단계: Stage 7 - Project Blueprint
>
> 패밀리: B-A-A (협업/동기화)
>
> 핵심 제약: Single Server (No Redis), Async Essential

------

## 1. 시스템 개요

### 1.1 목적

사용자의 발언을 실시간으로 분석하여 1초 이내에 시각적 피드백(중재, 요약, 경고)을 제공하고, 대화 내용을 기록하는 회의 보조 웹 애플리케이션.

### 1.2 핵심 아키텍처 원칙 (DNA 반영)

- **Single Server Concurrency**: `asyncio`를 활용하여 단일 프로세스 내에서 WebSocket 연결, STT 스트리밍, LLM 추론을 비동기로 처리.
- **In-Memory State**: Redis 부재로 인한 상태 관리(방, 연결)를 Python 메모리(`dict`, `set`)와 `asyncio.Queue`로 해결.

------

## 2. 아키텍처 구조 및 데이터 흐름 (Pipeline)

이 프로젝트의 가장 중요한 부분인 **실시간 파이프라인** 설계입니다.

### 2.1 오디오-AI 파이프라인 데이터 흐름도

코드 스니펫

```graph
graph TD
    User[Client (Browser)] -- "WebSocket (Audio Blob)" --> WSE[WebSocket Endpoint]
    
    subgraph "Backend (FastAPI Single Server)"
        WSE -- "Put into Queue" --> AudioQueue[Asyncio Queue]
        
        subgraph "Consumer Worker"
            AudioQueue -- "Pop" --> STT[Google Cloud STT Stream]
            STT -- "Intermediate/Final Text" --> TranscriptSvc[Transcript Service]
            
            TranscriptSvc -- "Save (Final Only)" --> DB[(SQLite/PG)]
            TranscriptSvc -- "Prompt Context" --> LLM[Gemini 1.5 Flash]
            
            LLM -- "Insight/Moderation" --> InsightSvc[Insight Service]
        end
        
        InsightSvc -- "Broadcast JSON" --> ConnMgr[Connection Manager]
    end
    
    ConnMgr -- "WebSocket (Text/Alert)" --> RoomUsers[All Users in Room]
```

### 2.2 상세 파이프라인 단계

1. **Ingestion (수집)**
   - 클라이언트는 마이크 입력을 100ms~250ms 단위의 Blob(WebM/PCM)으로 청크하여 WebSocket으로 전송.
   - 서버는 `ConnectionManager`를 통해 해당 유저의 스트림 큐에 오디오 데이터를 삽입.
2. **Processing (변환 및 추론)**
   - **STT**: Google STT의 Streaming API를 사용하여 실시간으로 텍스트 변환.
     - *최적화*: `is_final=False`인 중간 결과는 UI 표시용으로 즉시 브로드캐스팅, `is_final=True`인 결과만 DB 저장 및 LLM 입력으로 사용.
   - **LLM (Gemini)**:
     - Trace ID를 유지하며 STT 결과를 프롬프트 템플릿에 주입.
     - Gemini Streaming API를 호출하여 토큰 단위가 아닌 '문장/의미' 단위로 버퍼링 후 전송 (JSON 포맷 강제).
3. **Broadcasting (전파)**
   - 생성된 `Transcript`와 `AiInsight`를 `ConnectionManager.broadcast(room_id, message)`를 통해 방에 있는 모든 클라이언트에게 전송.

------

## 3. 도메인 모델 (Domain Model)

### 3.1 엔티티 (Entities)

모든 모델은 `src/core/database.py`의 `Base`를 상속받으며 `Async SQLAlchemy`를 사용합니다.

#### **User (사용자)**

- **식별자**: `id` (UUIDv7)
- **필드**:
  - `email` (String, Unique): 로그인 ID
  - `nickname` (String): 회의실 표시 이름
  - `password_hash` (String): 보안 처리된 비밀번호
- **관계**: `MeetingRoom` (N:M, 참여 중인 방)

#### **MeetingRoom (회의실)**

- **식별자**: `id` (UUIDv7)
- **필드**:
  - `title` (String): 회의 제목
  - `host_id` (UUID, FK): 방장 ID
  - `is_active` (Boolean): 회의 진행 여부 (종료 시 False)
  - `started_at` (DateTime): 시작 시간
- **In-Memory 매핑**: DB 외에 `ConnectionManager` 메모리에 `room_id: Set[WebSocket]` 형태로 활성 연결 관리.

#### **Transcript (대화록)**

- **식별자**: `id` (BigInt, AutoInc) - *삽입 성능 최적화*
- **필드**:
  - `room_id` (UUID, FK, Index): 소속 회의실
  - `user_id` (UUID, FK): 화자
  - `content` (Text): 발언 내용
  - `timestamp` (DateTime): 발언 시각 (Index)
- **특이사항**: 실시간성을 위해 `is_final=True` 시점에 비동기(`await session.commit()`)로 저장.

#### **AiInsight (AI 중재 및 요약)**

- **식별자**: `id` (BigInt)
- **필드**:
  - `room_id` (UUID, FK)
  - `type` (Enum): `SUMMARY`(요약), `WARNING`(발언권 독점 경고), `SUGGESTION`(주제 제안)
  - `content` (Text): AI 메시지 본문
  - `created_at` (DateTime)
  - `ref_transcript_id` (BigInt, FK, Nullable): 특정 발언에 대한 반응일 경우 참조.

### 3.2 값 객체 (Value Objects) & DTO

- **SocketMessage**: WebSocket 통신을 위한 표준 JSON 포맷

  Python

  ```
  class SocketMessage(BaseModel):
      type: str  # "transcript", "insight", "system"
      data: dict # Payload
      timestamp: float
  ```

------

## 4. API 설계 (REST Interface)

WebSocket 연결 전/후의 상태 관리를 위한 REST API입니다.

### 4.1 회의실 관리 (`/api/v1/rooms`)

- **POST /**: 회의실 생성 (JWT 필수)
- **GET /{room_id}**: 회의실 정보 및 입장 가능 여부 확인
- **PATCH /{room_id}/close**: 회의 종료 (Host 전용) -> WebSocket 연결 일괄 종료 트리거.

### 4.2 기록 조회 (`/api/v1/rooms/{room_id}/history`)

- **GET /transcripts**: 지난 대화록 페이징 조회 (Cursor-based Pagination 권장).
- **GET /insights**: AI 중재 이력 조회.

------

## 5. 구현 제약 사항 (Constraints from ADR & Stage 6)

1. **비동기 필수 (Async Essential)**:
   - 모든 DB 접근은 `await session.execute()` 패턴 사용.
   - 외부 API 호출(Google, Gemini)은 반드시 비동기 클라이언트 사용 (Blocking I/O 금지).
2. **도메인 분리**:
   - `src/domain/speech` (STT 처리)
   - `src/domain/insight` (Gemini 처리)
   - `src/domain/room` (회의실 관리)
   - 도메인 간 의존성은 `Service` 레이어에서 주입받아 처리.
3. **Traceability**:
   - WebSocket 연결 시 생성된 `trace_id`를 STT 요청 및 LLM 요청 헤더/메타데이터까지 전파하여 로그 추적성 확보.

------

