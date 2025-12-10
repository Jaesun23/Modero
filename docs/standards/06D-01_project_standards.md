# Project Standards

> 프로젝트: AI Moderator
>
> 단계: Stage 6 - Project Standards
>
> 버전: v1.0
>
> 기반: pyproject.toml, src/core/ 구현체

------

## 1. 코드 스타일 및 품질 기준 (Zero Tolerance)

### 1.1 품질 게이트

이 기준을 위반하는 코드는 커밋할 수 없습니다 (CI/CD 빌드 실패).

| **항목**        | **도구**  | **기준**               | **위반 시 조치**   |
| --------------- | --------- | ---------------------- | ------------------ |
| **Lint/Format** | `ruff`    | **0 violations**       | `ruff check --fix` |
| **Type Check**  | `mypy`    | **0 errors** (Strict)  | 타입 힌트 추가     |
| **Test**        | `pytest`  | **100% Pass**          | 테스트 수정        |
| **Async**       | `asyncio` | **Blocking Call 금지** | 비동기 함수로 교체 |

### 1.2 네이밍 컨벤션

- **클래스**: `PascalCase` (예: `MeetingRoom`, `AudioService`)
- **함수/변수**: `snake_case` (예: `create_room`, `user_id`)
- **상수**: `UPPER_SNAKE_CASE` (예: `MAX_CONNECTIONS`)
- **비공개**: `_prefix` (예: `_internal_helper`)

------

## 2. DNA 시스템 사용 규칙 (Mandatory)

도메인 로직 구현 시 반드시 다음 DNA 모듈을 사용해야 합니다.

### 2.1 비동기 I/O 필수 (Async Essential)

**DO ✅**

- 모든 I/O 작업(DB, API, File)에 `await` 키워드 사용.
- `async def`로 함수 선언.

**DON'T ❌**

- `time.sleep()`, `requests.get()`, `open()` 등 동기 함수 사용 절대 금지.
- 동기 함수 사용 시 `Ruff`가 차단함.

### 2.2 로깅 (Logging)

**DO ✅**

Python

```
from core.logging import get_logger
logger = get_logger(__name__)
# ...
await logger.info("room_created", room_id=room.id)
```

- 반드시 `get_logger`를 사용하고, 키워드 인자로 컨텍스트(`room_id` 등)를 전달해야 함.

**DON'T ❌**

- `print()` 사용 금지 (`T201` 에러).
- `logging` 모듈 직접 import 금지.

### 2.3 설정 (Configuration)

**DO ✅**

```python
from core.config import get_settings
settings = get_settings()
api_key = settings.gemini_api_key.get_secret_value()
```

**DON'T ❌**

- `os.environ.get()` 직접 사용 금지.
- 코드 내 하드코딩 금지.

### 2.4 데이터베이스 (Database)

**DO ✅**

```python
from core.database import get_session
# ...
async for session in get_session():
    result = await session.execute(select(User))
```

- `Dependency Injection`을 통해 세션을 주입받아 사용.

**DON'T ❌**

- 전역 세션 객체 직접 생성 금지.
- 동기 `session.query()` 사용 금지.

------

## 3. 아키텍처 규칙 (Layered Architecture)

### 3.1 의존성 방향

```
API -> Domain <- Infrastructure

Domain -> Core
```

- **Domain** 레이어는 외부(API, Infra)에 의존하지 않아야 함.
- **Core**는 프로젝트 전반에서 사용 가능.

### 3.2 디렉토리 구조

```
src/
├── api/            # 엔드포인트 (Router)
├── domain/         # 비즈니스 로직 (Model, Service)
├── infrastructure/ # 외부 연동 (Google STT, Gemini)
└── core/           # DNA 시스템 (Config, Log, DB 등)
```

------

## 4. Git 규칙

### 4.1 커밋 메시지 (Conventional Commits)

- `feat`: 새로운 기능
- `fix`: 버그 수정
- `refactor`: 기능 변경 없는 코드 개선
- `docs`: 문서 수정
- `test`: 테스트 코드 추가/수정

예시: `feat(domain): User 엔티티 추가`