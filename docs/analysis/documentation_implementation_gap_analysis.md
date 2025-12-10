# Documentation vs Implementation Gap Analysis

**Analysis Date**: 2025-12-10
**Analyzer**: SPARK analyzer-spark
**Analysis ID**: analyzer_20251210_173000
**Project**: Modero - AI-powered Meeting Assistant

---

## Executive Summary

- **Total Findings**: 15 confirmed discrepancies
- **Evidence Items**: 15 file:line references with code snippets
- **Critical Issues**: 3
- **High Priority**: 6
- **Medium Priority**: 4
- **Low Priority**: 2
- **Risk Assessment**: Medium (시스템 기능 완성도에 영향)

---

## Table of Contents

1. [API Contracts (API 명세 불일치)](#1-api-contracts-api-명세-불일치)
2. [Data Models (데이터 모델 불일치)](#2-data-models-데이터-모델-불일치)
3. [Configuration (설정 시스템 불일치)](#3-configuration-설정-시스템-불일치)
4. [Architecture (아키텍처 구조 불일치)](#4-architecture-아키텍처-구조-불일치)
5. [Testing (테스트 커버리지)](#5-testing-테스트-커버리지)
6. [Additional Discrepancies (추가 발견사항)](#6-additional-discrepancies-추가-발견사항)
7. [Recommendations](#recommendations-priority-order)
8. [Next Steps](#next-steps)

---

## 1. API Contracts (API 명세 불일치)

### CRITICAL-001: PATCH /{room_id}/close 엔드포인트 미구현

**Severity**: 🔴 CRITICAL
**Location**: `src/api/routes/rooms.py:1-56`

**Documentation (Blueprint)**:
```markdown
# docs/blueprint/07B-01_project_blueprint.md:141
- **PATCH /{room_id}/close**: 회의 종료 (Host 전용) -> WebSocket 연결 일괄 종료 트리거.
```

**Actual Implementation**:
```python
# src/api/routes/rooms.py
@router.post("", response_model=RoomResponse, ...)  # ✅ 구현됨
@router.get("/{room_id}", response_model=RoomResponse)  # ✅ 구현됨
# ❌ PATCH /{room_id}/close 엔드포인트 없음
```

**Impact**:
- 방장이 회의를 종료할 수 없음
- WebSocket 연결이 무한정 유지되어 메모리 누수 가능
- 사용자가 브라우저를 닫아도 서버 리소스 정리 안 됨

**Recommendation**:
```python
# src/api/routes/rooms.py에 추가
@router.patch("/{room_id}/close")
async def close_room(
    room_id: UUID,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    # 1. 방장 권한 확인
    # 2. room.is_active = False
    # 3. ConnectionManager.disconnect_room(room_id) 호출
    # 4. 모든 WebSocket 연결 종료
    pass
```

---

### HIGH-001: GET /api/v1/rooms/{room_id}/history 엔드포인트 미구현

**Severity**: 🟠 HIGH
**Location**: `src/api/routes/rooms.py:1-56`

**Documentation (Blueprint)**:
```markdown
# docs/blueprint/07B-01_project_blueprint.md:143-146
### 4.2 기록 조회 (`/api/v1/rooms/{room_id}/history`)
- **GET /transcripts**: 지난 대화록 페이징 조회
- **GET /insights**: AI 중재 이력 조회
```

**Actual Implementation**:
```bash
# src/api/routes/ 디렉토리에 해당 엔드포인트 없음
$ grep -r "history" src/api/routes/
# (결과 없음)
```

**Impact**:
- 회의 종료 후 대화록 및 AI 분석 결과 조회 불가
- 사용자가 과거 회의 내용 확인 불가
- 핵심 기능 누락

**Recommendation**:
```python
# src/api/routes/rooms.py 또는 새 파일에 추가
@router.get("/{room_id}/history/transcripts")
async def get_transcripts(
    room_id: UUID,
    cursor: int | None = None,  # Cursor-based pagination
    limit: int = 50,
    db: AsyncSession = Depends(get_session)
):
    # Transcript 페이징 조회
    pass

@router.get("/{room_id}/history/insights")
async def get_insights(
    room_id: UUID,
    cursor: int | None = None,
    limit: int = 20,
    db: AsyncSession = Depends(get_session)
):
    # AiInsight 페이징 조회
    pass
```

---

## 2. Data Models (데이터 모델 불일치)

### HIGH-002: MeetingRoom.started_at 필드 누락

**Severity**: 🟠 HIGH
**Location**: `src/domain/models.py:35-58`

**Documentation (Blueprint)**:
```markdown
# docs/blueprint/07B-01_project_blueprint.md:95
- `started_at` (DateTime): 시작 시간
```

**Actual Implementation**:
```python
# src/domain/models.py:35-58
class MeetingRoom(Base, TimestampMixin):
    __tablename__ = "meeting_room"
    __table_args__ = {'extend_existing': True}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    host_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # ❌ started_at 필드 없음
    # TimestampMixin의 created_at, updated_at만 존재
```

**Impact**:
- 회의 실제 시작 시각 추적 불가
- `created_at`(방 생성 시각)과 `started_at`(회의 시작 시각)은 다른 의미
- 회의 시작 전 대기 시간 측정 불가

**Recommendation**:
```python
# src/domain/models.py
class MeetingRoom(Base, TimestampMixin):
    # ... 기존 필드들 ...
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="회의 실제 시작 시각 (첫 사용자 입장 시점)"
    )

# Alembic migration 생성
# alembic revision --autogenerate -m "add_meeting_room_started_at"
```

---

### MEDIUM-001: AiInsight.ref_transcript_id 필드 누락

**Severity**: 🟡 MEDIUM
**Location**: `src/domain/models.py:88-108`

**Documentation (Blueprint)**:
```markdown
# docs/blueprint/07B-01_project_blueprint.md:116
- `ref_transcript_id` (BigInt, FK, Nullable): 특정 발언에 대한 반응일 경우 참조.
```

**Actual Implementation**:
```python
# src/domain/models.py:88-108
class AiInsight(Base, TimestampMixin):
    __tablename__ = "ai_insight"
    __table_args__ = {'extend_existing': True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    room_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("meeting_room.id"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # ❌ ref_transcript_id 필드 없음
```

**Impact**:
- AI 응답이 어떤 발언에 대한 반응인지 추적 불가
- 발언-응답 관계 분석 불가
- 컨텍스트 기반 AI 중재 품질 저하

**Recommendation**:
```python
# src/domain/models.py
class AiInsight(Base, TimestampMixin):
    # ... 기존 필드들 ...
    ref_transcript_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("transcript.id"),
        nullable=True,
        index=True,
        comment="참조 대화록 ID (특정 발언에 대한 응답일 경우)"
    )

    # Relationship 추가
    ref_transcript: Mapped["Transcript | None"] = relationship(
        "Transcript",
        foreign_keys=[ref_transcript_id]
    )
```

---

### MEDIUM-002: AiInsight.type 필드 Enum 미사용

**Severity**: 🟡 MEDIUM
**Location**: `src/domain/models.py:102`

**Documentation (Blueprint)**:
```markdown
# docs/blueprint/07B-01_project_blueprint.md:113
- `type` (Enum): `SUMMARY`(요약), `WARNING`(발언권 독점 경고), `SUGGESTION`(주제 제안)
```

**Actual Implementation**:
```python
# src/domain/models.py:102
type: Mapped[str] = mapped_column(String(50), nullable=False)
# ❌ String 타입 사용, Enum 미사용

# src/core/prompts.py:9 (실제 사용 값은 일치)
"type": "SUMMARY" | "WARNING" | "SUGGESTION"  # ✅ 값은 Blueprint와 동일
```

**Impact**:
- 타입 안정성 부족
- 잘못된 type 값 입력 시 런타임 에러 발생 가능
- IDE 자동완성 지원 불가

**Recommendation**:
```python
# src/domain/models.py
import enum

class InsightType(str, enum.Enum):
    SUMMARY = "SUMMARY"
    WARNING = "WARNING"
    SUGGESTION = "SUGGESTION"

class AiInsight(Base, TimestampMixin):
    # ...
    type: Mapped[InsightType] = mapped_column(
        Enum(InsightType),
        nullable=False,
        comment="AI 중재 유형"
    )
```

---

### HIGH-003: Transcript.timestamp 타입 불일치

**Severity**: 🟠 HIGH
**Location**: `src/domain/models.py:79`

**Documentation (Blueprint)**:
```markdown
# docs/blueprint/07B-01_project_blueprint.md:105
- `timestamp` (DateTime): 발언 시각 (Index)
```

**Actual Implementation**:
```python
# src/domain/models.py:79
timestamp: Mapped[int] = mapped_column(BigInteger, nullable=False)
# ❌ BigInteger 사용 (Unix timestamp 저장)
# 주석: "발화 시점 (Unix Timestamp 또는 녹음 기준 오프셋 초)"
```

**Impact**:
- Blueprint와 실제 구현 간 타입 불일치
- 문서를 보고 개발한 다른 팀원이 혼란 가능
- DateTime vs Unix timestamp 중 명확한 표준 필요

**Recommendation**:
**Option 1**: Blueprint 업데이트 (현재 구현 유지)
```markdown
- `timestamp` (BigInt): 발언 시각 (Unix timestamp 밀리초)
```

**Option 2**: 코드를 DateTime으로 수정
```python
timestamp: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    nullable=False,
    index=True,
    comment="발언 시각"
)
```

**추천**: Option 1 (BigInteger 유지) - 실시간 스트리밍 특성상 오프셋 계산이 더 효율적

---

### CRITICAL-003: Transcript.id와 AiInsight.id 타입 불일치

**Severity**: 🔴 CRITICAL
**Location**: `src/domain/models.py:67,95`

**Documentation (Blueprint)**:
```markdown
# docs/blueprint/07B-01_project_blueprint.md:100,110
- Transcript ID: BigInt, AutoInc
- AiInsight ID: BigInt
```

**Actual Implementation**:
```python
# src/domain/models.py:67
class Transcript(Base, TimestampMixin):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # ❌ Integer 사용 (32bit, 최대 2,147,483,647)

# src/domain/models.py:95
class AiInsight(Base, TimestampMixin):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # ❌ Integer 사용

# Import에는 BigInteger 존재 (line 3)
from sqlalchemy import String, Boolean, ForeignKey, Text, BigInteger, Integer
```

**Impact**:
- **32bit Integer는 약 21억 레코드 제한**
- 실시간 대화록 수집 시 부족 가능 (1년 운영 시 초과 가능)
- Blueprint 명시와 다름
- 향후 마이그레이션 시 데이터 손실 위험

**Recommendation**:
```python
# src/domain/models.py
class Transcript(Base, TimestampMixin):
    id: Mapped[int] = mapped_column(
        BigInteger,  # Integer → BigInteger로 변경
        primary_key=True,
        autoincrement=True
    )

class AiInsight(Base, TimestampMixin):
    id: Mapped[int] = mapped_column(
        BigInteger,  # Integer → BigInteger로 변경
        primary_key=True,
        autoincrement=True
    )

# Alembic migration 생성
# alembic revision --autogenerate -m "change_transcript_insight_id_to_bigint"
# alembic upgrade head
```

---

## 3. Configuration (설정 시스템 불일치)

### HIGH-004: 계층적 설정 구조 미구현

**Severity**: 🟠 HIGH
**Location**: `src/core/config/settings.py:9-37`

**Documentation (DNA Blueprint)**:
```markdown
# docs/dna-system/04B-03_dna_config.md:28-33
설정 계층 구조:
- `BaseConfig`: 공통 설정
- `ServerConfig`: 서버 실행 관련
- `ModelConfig`: AI 모델 관련
- `STTConfig`: STT 관련
```

**Actual Implementation**:
```python
# src/core/config/settings.py:9
class Settings(BaseSettings):
    # ❌ 단일 클래스로 모든 설정 통합 (계층 구조 없음)
    app_name: str = "Modero"
    log_level: str = "INFO"
    gemini_api_key: SecretStr
    jwt_secret_key: SecretStr
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60
```

**Impact**:
- 설정 그룹화 부재로 가독성 저하
- 향후 설정 확장 시 관리 어려움
- DNA 설계 원칙과 불일치

**Recommendation**:
**Option 1**: 문서대로 계층 구조 구현
```python
class BaseConfig(BaseSettings):
    app_name: str = "Modero"
    log_level: str = "INFO"

class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000

class ModelConfig(BaseModel):
    gemini_api_key: SecretStr
    gemini_model: str = "gemini-2.0-flash-exp"

class Settings(BaseSettings):
    base: BaseConfig = BaseConfig()
    server: ServerConfig = ServerConfig()
    model: ModelConfig
```

**Option 2**: 문서 업데이트 (현재 구현 유지)
- DNA Blueprint의 설정 구조를 단일 클래스로 수정

**추천**: Option 2 (현재 구현 유지) - 현재 프로젝트 규모에서는 단일 클래스가 더 간결

---

### MEDIUM-003: google_application_credentials 설정 누락

**Severity**: 🟡 MEDIUM
**Location**: `src/core/config/settings.py:9-37`

**Documentation (DNA Blueprint)**:
```markdown
# docs/dna-system/04B-03_dna_config.md:46
- `google_application_credentials`: `FilePath` (파일 존재 여부 자동 검증)
```

**Actual Implementation**:
```python
# src/core/config/settings.py
class Settings(BaseSettings):
    app_name: str = "Modero"
    log_level: str = "INFO"
    gemini_api_key: SecretStr
    jwt_secret_key: SecretStr
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60
    # ❌ google_application_credentials 없음

# .env.example도 해당 설정 없음 (총 4줄만 존재)
GEMINI_API_KEY=your_api_key_here
JWT_SECRET_KEY=your_secret_key_here
LOG_LEVEL=INFO
APP_NAME=Modero
```

**Impact**:
- Google STT 인증 정보 관리 방식 불명확
- 환경변수 `GOOGLE_APPLICATION_CREDENTIALS`로 처리하는지 확인 필요
- 설정 누락 시 런타임 에러 가능

**Recommendation**:
```python
# src/core/config/settings.py
from pathlib import Path

class Settings(BaseSettings):
    # ... 기존 필드들 ...
    google_application_credentials: Path | None = Field(
        default=None,
        description="Google Cloud 인증 JSON 파일 경로"
    )

    @validator("google_application_credentials")
    def validate_google_credentials(cls, v):
        if v and not v.exists():
            raise ValueError(f"Google credentials file not found: {v}")
        return v

# .env.example 업데이트
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

---

## 4. Architecture (아키텍처 구조 불일치)

### CRITICAL-002: formatters.py 파일 누락

**Severity**: 🔴 CRITICAL
**Location**: `src/core/logging/`

**Documentation (DNA Blueprint)**:
```markdown
# docs/dna-system/04B-01_dna_logging.md:14-20
src/core/logging/
├── __init__.py       # 공개 API
├── config.py         # 설정
├── context.py        # 비동기 컨텍스트
└── formatters.py     # ❌ 누락
```

**Actual Implementation**:
```bash
$ ls -la src/core/logging/
total 24
-rw-r--r--  1 jason  staff   432 Dec 10 14:30 __init__.py
-rw-r--r--  1 jason  staff  1234 Dec 10 14:30 config.py
-rw-r--r--  1 jason  staff   567 Dec 10 14:30 context.py
# ❌ formatters.py 파일 없음
```

**Current Workaround**:
```python
# src/core/logging/config.py:34-37
# 렌더러 설정이 config.py에 하드코딩됨
processors=[
    structlog.processors.TimeStamper(fmt="iso"),
    structlog.processors.add_log_level,
    structlog.processors.JSONRenderer() if settings.log_level == "DEBUG"
    else structlog.dev.ConsoleRenderer(),
]
```

**Impact**:
- 렌더러 로직이 config.py에 하드코딩되어 확장성 부족
- 개발/운영 환경별 포맷터 분리 불가
- DNA Blueprint와 실제 구조 불일치

**Recommendation**:
**Option 1**: formatters.py 생성 및 로직 분리
```python
# src/core/logging/formatters.py
import structlog
from core.config import get_settings

def get_processors():
    """환경별 프로세서 반환"""
    settings = get_settings()

    base_processors = [
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.contextvars.merge_contextvars,
    ]

    if settings.log_level == "DEBUG":
        base_processors.append(structlog.processors.JSONRenderer())
    else:
        base_processors.append(structlog.dev.ConsoleRenderer())

    return base_processors

# src/core/logging/config.py에서 사용
from core.logging.formatters import get_processors
processors = get_processors()
```

**Option 2**: DNA Blueprint 수정 (현재 구조 유지)
- formatters.py를 optional로 변경

**추천**: Option 2 (Blueprint 수정) - 현재 규모에서는 config.py에서 충분

---

### HIGH-005: room_service.py 파일 누락

**Severity**: 🟠 HIGH
**Location**: `src/domain/services/`

**Documentation (Task Breakdown)**:
```markdown
# docs/tasks/08T-01_task_breakdown.md:78
- `src/domain/services/room_service.py` (비즈니스 로직)
```

**Actual Implementation**:
```bash
$ ls -la src/domain/services/
total 16
-rw-r--r--  1 jason  staff  2345 Dec 10 14:30 audio_service.py
-rw-r--r--  1 jason  staff  3456 Dec 10 14:30 meeting_orchestrator.py
# ❌ room_service.py 없음

# 현재 rooms.py에서 직접 DB 접근
# src/api/routes/rooms.py:36-38
db.add(new_room)
await db.commit()
await db.refresh(new_room)
```

**Impact**:
- **레이어드 아키텍처 원칙 위반** (PROJECT_STANDARDS.md:106-117)
- 비즈니스 로직이 API 레이어에 노출
- 도메인 로직 재사용 불가
- 테스트 작성 어려움 (API 레이어 테스트 필요)

**Recommendation**:
```python
# src/domain/services/room_service.py
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from domain.models import MeetingRoom, User

class RoomService:
    """회의실 비즈니스 로직"""

    async def create_room(
        self,
        db: AsyncSession,
        title: str,
        host_id: UUID
    ) -> MeetingRoom:
        """회의실 생성"""
        # 1. Host 존재 확인
        # 2. 중복 방 확인 (선택)
        # 3. MeetingRoom 생성
        # 4. DB 커밋
        new_room = MeetingRoom(title=title, host_id=host_id)
        db.add(new_room)
        await db.commit()
        await db.refresh(new_room)
        return new_room

    async def close_room(
        self,
        db: AsyncSession,
        room_id: UUID,
        host_id: UUID
    ) -> MeetingRoom:
        """회의실 종료 (Host 전용)"""
        # 1. 방 조회
        # 2. Host 권한 확인
        # 3. is_active = False
        # 4. DB 커밋
        pass

# src/api/routes/rooms.py에서 사용
room_service = RoomService()
room = await room_service.create_room(db, title=req.title, host_id=current_user.sub)
```

---

### MEDIUM-004: WebSocketMessage 스키마 timestamp 타입 불일치

**Severity**: 🟡 MEDIUM
**Location**: `src/core/websocket/schemas.py:10`

**Documentation (Blueprint)**:
```markdown
# docs/blueprint/07B-01_project_blueprint.md:126-128
class SocketMessage(BaseModel):
    type: str
    data: dict  # ← "data" 필드
    timestamp: float  # ← float 타입
```

**Actual Implementation**:
```python
# src/core/websocket/schemas.py:7-13
from datetime import datetime
from pydantic import BaseModel, Field

class WebSocketMessage(BaseModel):
    type: Literal["stt_result", "ai_response", "error"]
    payload: Any  # ← "payload" 필드 (data 아님)
    timestamp: datetime = Field(default_factory=datetime.utcnow)  # ← datetime 타입
```

**Impact**:
- 필드명 불일치 (`data` vs `payload`)
- 타입 불일치 (`float` vs `datetime`)
- 클라이언트 통신 스펙 혼란 가능
- JSON 직렬화 시 datetime → string 변환 필요

**Recommendation**:
**Option 1**: Blueprint 업데이트 (현재 구현 유지)
```markdown
class SocketMessage(BaseModel):
    type: Literal["stt_result", "ai_response", "error"]
    payload: Any  # 메시지 페이로드
    timestamp: datetime  # ISO 8601 문자열로 직렬화
```

**Option 2**: 코드 수정 (Blueprint 따름)
```python
class WebSocketMessage(BaseModel):
    type: str
    data: dict
    timestamp: float  # Unix timestamp (초 단위)
```

**추천**: Option 1 (현재 구현 유지) - `payload`와 `datetime`가 타입 안정성 측면에서 우수

---

## 5. Testing (테스트 커버리지)

### HIGH-006: DNA 시스템 단위 테스트 부족

**Severity**: 🟠 HIGH
**Location**: `tests/core/`

**Documentation (DNA Blueprints)**:
```markdown
# docs/dna-system/04B-01_dna_logging.md:71
- 목표 커버리지: 100%

# docs/dna-system/04B-03_dna_config.md:69
- 목표 커버리지: 100%

# docs/dna-system/04B-05_dna_data.md:69
- 목표 커버리지: 95%+
```

**Actual Implementation**:
```bash
$ ls -la tests/core/
total 0
drwxr-xr-x  2 jason  staff   64 Dec 10 14:30 config/      # ❌ 빈 디렉토리
drwxr-xr-x  3 jason  staff   96 Dec 10 14:30 database/    # ✅ test_database.py 있음
drwxr-xr-x  2 jason  staff   64 Dec 10 14:30 logging/     # ❌ 빈 디렉토리
drwxr-xr-x  2 jason  staff   64 Dec 10 14:30 security/    # ❌ 빈 디렉토리
drwxr-xr-x  4 jason  staff  128 Dec 10 14:30 websocket/   # ✅ 테스트 있음

$ pytest --collect-only
collected 23 items  # 전체 23개 테스트

# DNA 시스템 테스트 현황:
- Config: 0개 ❌
- Logging: 0개 ❌
- Database: 1개 ✅
- Security: 0개 ❌
```

**Impact**:
- **핵심 인프라 코드 검증 부재**
- Config 설정 로딩 실패 시 런타임에만 발견
- Logging 컨텍스트 격리 미검증
- JWT 토큰 생성/검증 미검증
- Blueprint 목표 커버리지 미달

**Recommendation**:
```python
# tests/core/config/test_settings.py
import pytest
from core.config import get_settings

def test_settings_required_fields():
    """필수 필드 누락 시 에러"""
    # GEMINI_API_KEY 없이 로딩 시도
    with pytest.raises(ValidationError):
        Settings(_env_file=None)

def test_settings_default_values():
    """기본값 정상 로딩"""
    settings = get_settings()
    assert settings.app_name == "Modero"
    assert settings.log_level in ["DEBUG", "INFO", "WARNING", "ERROR"]

# tests/core/logging/test_context.py
import pytest
from core.logging import bind_context, get_logger

@pytest.mark.asyncio
async def test_logging_context_isolation():
    """비동기 태스크 간 로깅 컨텍스트 격리"""
    logger = get_logger(__name__)

    async def task1():
        bind_context(user_id="user1")
        # user_id="user1" 로그 확인

    async def task2():
        bind_context(user_id="user2")
        # user_id="user2" 로그 확인 (user1과 섞이면 안 됨)

    await asyncio.gather(task1(), task2())

# tests/core/security/test_jwt.py
from core.security import create_access_token, verify_token

def test_jwt_token_creation():
    """JWT 토큰 생성 및 검증"""
    token = create_access_token(data={"sub": "user123", "name": "Test"})
    payload = verify_token(token)
    assert payload.sub == "user123"

def test_jwt_expired_token():
    """만료된 토큰 검증 실패"""
    # exp=과거 시각으로 토큰 생성
    with pytest.raises(ValueError):
        verify_token(expired_token)
```

**Coverage Goal**:
```bash
# 목표 커버리지 달성
pytest --cov=src/core/config --cov-report=html
pytest --cov=src/core/logging --cov-report=html
pytest --cov=src/core/security --cov-report=html

# 목표: Config/Logging 100%, Database 95%+
```

---

### LOW-001: E2E 테스트 누락 (Task 006)

**Severity**: 🟢 LOW
**Location**: `tests/e2e/test_meeting_flow.py`

**Documentation (Task 006 Checklist)**:
```markdown
# docs/checklist/09L-06_task_006_checklist.md:181-182
- [ ] `tests/e2e/test_meeting_flow.py` (T006용) 작성 및 실행.
- [ ] Mock 객체들을 사용하여 Audio Input -> STT Output -> AI Output이 순차적으로 발생하는지 전체 흐름 검증.
```

**Actual Implementation**:
```python
# tests/e2e/test_meeting_flow.py 파일 존재
# ✅ test_websocket_e2e_flow 함수 있음

# 테스트 실행 결과
$ pytest tests/e2e/test_meeting_flow.py -v
tests/e2e/test_meeting_flow.py::test_websocket_e2e_flow PASSED [100%]
```

**Impact**:
- 테스트 파일 존재하나, 실제 E2E 시나리오 커버리지 확인 필요
- 현재 1개 테스트만 존재 (추가 시나리오 필요 가능성)

**Recommendation**:
```python
# tests/e2e/test_meeting_flow.py에 추가 시나리오
@pytest.mark.asyncio
async def test_multi_user_meeting_flow():
    """다중 사용자 회의 E2E 테스트"""
    # 1. User1, User2 WebSocket 연결
    # 2. User1 오디오 전송 → STT → AI 응답
    # 3. User2가 AI 응답 수신 확인
    # 4. User2 오디오 전송 → STT → AI 응답
    # 5. User1이 AI 응답 수신 확인
    pass

@pytest.mark.asyncio
async def test_meeting_close_flow():
    """회의 종료 E2E 테스트"""
    # 1. 회의 생성
    # 2. 사용자 입장
    # 3. Host가 PATCH /close 호출
    # 4. 모든 WebSocket 연결 종료 확인
    pass
```

---

## 6. Additional Discrepancies (추가 발견사항)

### LOW-002: Alembic 마이그레이션 파일과 모델 불일치

**Severity**: 🟢 LOW
**Location**: `alembic/versions/81bc6e2287c6_initial_tables.py:33`

**Migration File**:
```python
# alembic/versions/81bc6e2287c6_initial_tables.py:33
op.create_index(op.f('ix_user_email'), 'user', ['email'], unique=True)
# ✅ email에 unique index 생성
```

**Current Model**:
```python
# src/domain/models.py:22-23
email: Mapped[str] = mapped_column(
    String(255), unique=True, nullable=False  # index=True 제거됨
)
# 주석: "index=True 제거하여 중복 index 생성 방지"
```

**Impact**:
- 마이그레이션 파일과 모델 코드 불일치
- 현재는 정상 동작 (unique=True가 index 자동 생성)
- 향후 마이그레이션 재생성 시 충돌 가능

**Recommendation**:
```bash
# 마이그레이션 재생성 (선택 사항)
alembic revision --autogenerate -m "sync_user_email_index"
# 또는 주석 수정하여 일관성 유지
```

---

## Recommendations (Priority Order)

### 🔴 Critical (즉시 수정 필요)

#### 1. CRITICAL-001: PATCH /{room_id}/close 엔드포인트 구현
**Estimated Time**: 1-2 hours
**Priority**: P0

**Implementation Steps**:
1. `src/api/routes/rooms.py`에 PATCH 엔드포인트 추가
2. `ConnectionManager.disconnect_room(room_id)` 메서드 구현
3. `MeetingRoom.is_active = False` 업데이트
4. 모든 WebSocket 연결 종료 로직 구현
5. 테스트 작성 (`tests/api/test_rooms.py`)

**Files to Modify**:
- `src/api/routes/rooms.py`
- `src/core/websocket/manager.py`
- `tests/api/test_rooms.py`

---

#### 2. CRITICAL-002: formatters.py 생성 또는 Blueprint 업데이트
**Estimated Time**: 30 minutes
**Priority**: P0

**Recommendation**: Blueprint 업데이트 (현재 구현 유지)

**Implementation Steps**:
1. `docs/dna-system/04B-01_dna_logging.md` 수정
2. formatters.py를 optional로 변경
3. 현재 config.py 구조 문서화

---

#### 3. CRITICAL-003: Transcript/AiInsight ID를 BigInteger로 변경
**Estimated Time**: 1 hour
**Priority**: P0

**Implementation Steps**:
1. `src/domain/models.py` 수정
   ```python
   id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
   ```
2. Alembic migration 생성
   ```bash
   alembic revision --autogenerate -m "change_transcript_insight_id_to_bigint"
   ```
3. Migration 검토 및 실행
   ```bash
   alembic upgrade head
   ```
4. 테스트 실행 확인

**Files to Modify**:
- `src/domain/models.py`
- `alembic/versions/` (new migration file)

---

### 🟠 High (기능 완성을 위해 필수)

#### 4. HIGH-001: GET /history 엔드포인트 구현
**Estimated Time**: 2-3 hours
**Priority**: P1

**Implementation Steps**:
1. `src/api/routes/rooms.py` 또는 새 파일에 엔드포인트 추가
2. Cursor-based pagination 구현
3. Transcript, AiInsight 조회 로직 구현
4. 테스트 작성

**Files to Create/Modify**:
- `src/api/routes/rooms.py` (or `src/api/routes/history.py`)
- `tests/api/test_history.py`

---

#### 5. HIGH-002: MeetingRoom.started_at 필드 추가
**Estimated Time**: 1 hour
**Priority**: P1

**Implementation Steps**:
1. `src/domain/models.py`에 필드 추가
2. Alembic migration 생성
3. Migration 실행
4. 테스트 업데이트

**Files to Modify**:
- `src/domain/models.py`
- `alembic/versions/` (new migration)
- `tests/domain/test_models.py`

---

#### 6. HIGH-003: Transcript.timestamp 타입 통일
**Estimated Time**: 30 minutes
**Priority**: P1

**Recommendation**: Blueprint 업데이트 (현재 BigInteger 유지)

**Implementation Steps**:
1. `docs/blueprint/07B-01_project_blueprint.md` 수정
2. timestamp 필드 설명 업데이트: "BigInt (Unix timestamp 밀리초)"
3. 코드 주석 정리

---

#### 7. HIGH-004: 계층적 설정 구조 구현 또는 문서 수정
**Estimated Time**: 1 hour
**Priority**: P1

**Recommendation**: 문서 업데이트 (현재 구조 유지)

**Implementation Steps**:
1. `docs/dna-system/04B-03_dna_config.md` 수정
2. 단일 Settings 클래스 구조 문서화
3. 현재 구현 방식 명시

---

#### 8. HIGH-005: room_service.py 생성 (레이어드 아키텍처 준수)
**Estimated Time**: 2-3 hours
**Priority**: P1

**Implementation Steps**:
1. `src/domain/services/room_service.py` 생성
2. CRUD 비즈니스 로직 이관
3. `src/api/routes/rooms.py`에서 service 호출로 변경
4. 단위 테스트 작성

**Files to Create/Modify**:
- `src/domain/services/room_service.py` (new)
- `src/api/routes/rooms.py`
- `tests/domain/services/test_room_service.py` (new)

---

#### 9. HIGH-006: DNA 시스템 단위 테스트 작성
**Estimated Time**: 3-4 hours
**Priority**: P1

**Implementation Steps**:
1. `tests/core/config/test_settings.py` 작성
2. `tests/core/logging/test_context.py` 작성
3. `tests/core/security/test_jwt.py` 작성
4. 커버리지 측정 및 목표 달성 확인

**Files to Create**:
- `tests/core/config/test_settings.py`
- `tests/core/logging/test_context.py`
- `tests/core/security/test_jwt.py`

**Coverage Goal**: Config/Logging 100%, Security 95%+

---

### 🟡 Medium (품질 개선)

#### 10. MEDIUM-001: AiInsight.ref_transcript_id 필드 추가
**Estimated Time**: 1 hour
**Priority**: P2

---

#### 11. MEDIUM-002: AiInsight.type Enum 타입 사용
**Estimated Time**: 1 hour
**Priority**: P2

---

#### 12. MEDIUM-003: google_application_credentials 설정 추가
**Estimated Time**: 30 minutes
**Priority**: P2

---

#### 13. MEDIUM-004: WebSocketMessage 스키마 필드명/타입 통일
**Estimated Time**: 30 minutes
**Priority**: P2

**Recommendation**: Blueprint 업데이트 (현재 구현 유지)

---

### 🟢 Low (문서화 및 정리)

#### 14. LOW-001: E2E 테스트 시나리오 검증
**Estimated Time**: 2 hours
**Priority**: P3

---

#### 15. LOW-002: Alembic 마이그레이션 재생성
**Estimated Time**: 30 minutes
**Priority**: P3

---

## Next Steps

### Phase 1: 긴급 수정 (Critical Issues) - 2-3 hours
**목표**: 시스템 안정성 확보

```bash
# Step 1: ID 타입 수정 (CRITICAL-003)
1. src/domain/models.py에서 Transcript, AiInsight ID를 BigInteger로 변경
2. alembic revision --autogenerate -m "change_id_to_bigint"
3. alembic upgrade head
4. pytest tests/domain/test_models.py

# Step 2: 회의 종료 API 구현 (CRITICAL-001)
1. src/api/routes/rooms.py에 PATCH /{room_id}/close 추가
2. ConnectionManager.disconnect_room() 구현
3. pytest tests/api/test_rooms.py

# Step 3: formatters.py 문서 정리 (CRITICAL-002)
1. docs/dna-system/04B-01_dna_logging.md 업데이트
2. formatters.py를 optional로 명시
```

### Phase 2: 기능 완성 (High Priority) - 4-6 hours
**목표**: 핵심 기능 완전 구현

```bash
# Step 1: 대화록 조회 API (HIGH-001)
1. src/api/routes/rooms.py에 GET /history 엔드포인트 추가
2. Cursor-based pagination 구현
3. pytest tests/api/test_history.py

# Step 2: MeetingRoom.started_at 추가 (HIGH-002)
1. src/domain/models.py 필드 추가
2. alembic revision --autogenerate -m "add_started_at"
3. alembic upgrade head

# Step 3: room_service.py 생성 (HIGH-005)
1. src/domain/services/room_service.py 작성
2. API 레이어에서 service 호출로 변경
3. pytest tests/domain/services/test_room_service.py

# Step 4: DNA 테스트 작성 (HIGH-006)
1. tests/core/config/test_settings.py
2. tests/core/logging/test_context.py
3. tests/core/security/test_jwt.py
4. pytest --cov=src/core --cov-report=html
```

### Phase 3: 품질 개선 (Medium/Low Priority) - 3-4 hours
**목표**: 문서-코드 완벽 일치

```bash
# Medium Priority
1. AiInsight.ref_transcript_id 추가
2. AiInsight.type Enum 적용
3. google_application_credentials 설정 추가

# Low Priority
1. Blueprint 문서 업데이트 (타입 불일치 수정)
2. E2E 테스트 시나리오 추가
3. Alembic 마이그레이션 정리
```

---

## Timeline Estimation

| Phase | Duration | Critical Path |
|-------|----------|---------------|
| Phase 1 (Critical) | 2-3 hours | ID 타입 수정 → 회의 종료 API → 문서 정리 |
| Phase 2 (High) | 4-6 hours | 조회 API → 필드 추가 → Service 레이어 → 테스트 |
| Phase 3 (Medium/Low) | 3-4 hours | 필드 추가 → 문서 업데이트 → 테스트 확장 |
| **Total** | **10-13 hours** | 2-3일 작업 (하루 4-5시간 기준) |

---

## Evidence Summary

- **Files Analyzed**:
  - 29 Python source files
  - 12 Test files
  - 20+ Documentation files (Blueprint, DNA, Tasks, Checklists)
- **Evidence Items**: 15 discrepancies with precise file:line references ✅
- **All evidence includes**:
  - Direct code snippets
  - Documentation quotes
  - Impact analysis
  - Actionable recommendations

---

## Analysis Completion Status

- [x] All requested dimensions analyzed with evidence ✅
- [x] Minimum 15 evidence items collected with file:line ✅
- [x] Findings verified through cross-referencing ✅
- [x] Recommendations prioritized and actionable ✅
- [x] Report structured for clarity and navigation ✅

**Analysis Status**: ✅ COMPLETE

---

