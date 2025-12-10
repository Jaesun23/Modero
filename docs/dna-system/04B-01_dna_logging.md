# DNA Blueprint: Observability System (Logging)

## 1. 개요 및 목적 (Purpose & Scope)
- **목적**: 수십 개의 WebSocket 연결과 비동기 태스크가 혼재된 환경에서, **요청의 흐름(Trace)**을 추적하고 **지연 시간(Latency)**을 명확히 파악하기 위함.
- **핵심 가치**: "어떤 사용자의 발언이, 어느 시점에, 왜 늦게 처리되었는가?"를 즉시 답변할 수 있어야 함.
- **범위**:
  - `structlog` 기반의 구조화된 로깅
  - `contextvars`를 이용한 비동기 안전(Async-safe) `trace_id` 전파
  - 개발(Console) vs 운영(JSON) 포맷 이원화

## 2. 디렉토리 구조 (Directory Structure)

```
src/
└── core/
└── logging/
      ├── init.py       # 공개 API (get_logger, bind_context 등) 노출
      ├── config.py         # structlog 프로세서 설정 및 초기화
      ├── context.py        # contextvars 기반 컨텍스트 관리 (trace_id)
      └── formatters.py     # 개발용/운영용 렌더러 설정
```

## 3. 핵심 설계 결정 (Key Design Decisions)

### 3.1 Trace ID 전파 (Async Safe)
- **문제**: Python `asyncio` 환경에서는 전역 변수나 ThreadLocal이 각 코루틴 간의 컨텍스트를 유지하지 못함.
- **해결**: `contextvars` 모듈을 사용하여 **Task-local 스토리지**를 구현. 요청이 시작될 때 생성된 `trace_id`가 모든 후속 `await` 호출과 로그에 자동으로 포함되도록 함.

### 3.2 로깅 라이브러리: `structlog`
- **이유**: Python 표준 `logging` 모듈은 JSON 구조화 및 컨텍스트 바인딩이 번거로움. `structlog`는 이 과정을 자동화하며 퍼포먼스 오버헤드가 적음.

### 3.3 포맷 전략
- **Local/Dev**: `ConsoleRenderer` (컬러 출력, 가독성 중심)
- **Prod**: `JSONRenderer` (기계 가독성, 클라우드 로그 수집기 연동 최적화)

## 4. 공개 API (Public API)

### `configure_logging()`
- **역할**: 앱 시작 시(`main.py` lifespan) 호출되어 로깅 설정을 초기화함.
- **설정**: `.env`의 `LOG_LEVEL`, `ENVIRONMENT` 값에 따라 포맷터 결정.

### `get_logger(name: str) -> BoundLogger`
- **역할**: 각 모듈에서 사용할 로거 인스턴스 반환.
- **사용법**:
  ```python
  from core.logging import get_logger
  logger = get_logger(__name__)
  ```

### `bind_context(**kwargs)`

- **역할**: 현재 요청 컨텍스트에 키-값 쌍을 추가. 이후 발생하는 모든 로그에 자동 포함됨.

- **사용법**:

  ```python
  # 미들웨어에서
  bind_context(trace_id="req-123", user_id="user-456")
  ```

## 5. 의존성 (Dependencies)

- **외부 라이브러리**:
  - `structlog>=24.1.0`
  - `colorama` (개발 환경 컬러 출력용)
- **내부 의존성**:
  - `core.config` (설정 값 로드)

## 6. 테스트 전략 (Testing Strategy)

- **단위 테스트 (`tests/core/logging/`)**:
  - `bind_context`가 비동기 태스크 간에 격리되는지 검증 (Task A의 컨텍스트가 Task B에 영향을 주지 않아야 함).
  - JSON 출력이 올바른 키(`trace_id`, `timestamp`, `level`)를 포함하는지 검증.
- **목표 커버리지**: 100% (핵심 인프라 코드이므로 결함 허용 안 됨).

## 7. 구현 우선순위

1. `context.py`: `contextvars` 래퍼 구현 (가장 기본)
2. `config.py`: `structlog` 체인 설정
3. `__init__.py`: 공개 API 노출