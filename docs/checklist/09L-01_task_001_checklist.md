# 09L-01_task_001_checklist

> Task ID: T001
>
> Task 명: 도메인 엔티티 구현 및 마이그레이션
>
> 예상 소요: 3 hours
>
> 관련 문서: 07B-01 (Section 3), 06D-01 (DB 표준)

------

## Step 1: 목표 이해 (Goal Understanding) ✅

### 1.1 Task 목표

- `User`, `MeetingRoom`, `Transcript`, `AiInsight` 4개 핵심 엔티티를 `SQLAlchemy` 비동기 모델로 구현.
- `Alembic`을 설정하고 첫 번째 마이그레이션 파일 생성.

### 1.2 입력 (Inputs)

- **Blueprint Section 3.1 (엔티티 명세)**: `docs/blueprint/07B-01_project_blueprint.md`
  - **User**: `id(UUIDv7)`, `email`, `nickname`, `password_hash`
  - **MeetingRoom**: `id(UUIDv7)`, `title`, `host_id`, `is_active`
  - **Transcript**: `id(BigInt)`, `room_id`, `user_id`, `content`, `timestamp`
  - **AiInsight**: `id(BigInt)`, `room_id`, `type`, `content`
- **Core Modules**: `src/core/database/base.py`, `src/core/database/mixins.py`

### 1.3 성공 기준 (Acceptance Criteria)

- [ ] `src/domain/models.py`에 4개 클래스 구현 완료.
- [ ] `alembic revision --autogenerate` 성공 및 마이그레이션 파일 생성.
- [ ] `pytest` 실행 시 SQLite 메모리 DB에서 테이블 생성 및 CRUD 성공.

------

## Step 2: 테스트 작성 (Test First) 🧪

### 2.1 테스트 시나리오

1. **User 생성**: `User` 모델 인스턴스화 및 DB 저장, `id` 자동 생성 확인.
2. **Room 생성**: `MeetingRoom` 생성 및 `host_id` 관계 매핑 확인.
3. **Transcript 저장**: 대화록 저장 시 `created_at` 자동 생성 확인.
4. **관계 무결성**: 존재하지 않는 `user_id`로 Room 생성 시 에러 발생 확인.

### 2.2 테스트 파일 생성

- 파일: `tests/domain/test_models.py`
- 코드 스켈레톤:

```python
import pytest
from sqlalchemy import select
from src.domain.models import User, MeetingRoom

@pytest.mark.asyncio
async def test_create_user(db_session):
    user = User(email="test@example.com", nickname="tester", password_hash="hash")
    db_session.add(user)
    await db_session.commit()
    
    result = await db_session.execute(select(User).where(User.email == "test@example.com"))
    saved_user = result.scalar_one()
    assert saved_user.id is not None
    assert saved_user.nickname == "tester"
```

------

## Step 3: 구현 (Implementation) 🔨

### 3.1 구현 위치

- `src/domain/models.py`

### 3.2 구현 힌트

```Python
import uuid
from sqlalchemy import Column, String, Boolean, ForeignKey, Text, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from src.core.database import Base, TimestampMixin

class User(Base, TimestampMixin):
    # __tablename__은 Base에서 자동 생성 (user)
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    nickname: Mapped[str] = mapped_column(String)
    password_hash: Mapped[str] = mapped_column(String)

class MeetingRoom(Base, TimestampMixin):
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String)
    host_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
```

------

## Step 4: 정적 검증 (Static Analysis) 🔍

### 4.1 Linting & Formatting

```bash
ruff check src/domain/models.py tests/domain/test_models.py --fix
ruff format src/domain/models.py tests/domain/test_models.py
```

- **기준**: `0 violations`.

### 4.2 Type Checking

```bash
mypy src/domain/models.py
```

- **기준**: `0 errors`. SQLAlchemy 타입 힌트 오류가 없어야 함.

------

## Step 5: 단위 테스트 실행 (Run Tests) ✅

### 5.1 테스트 실행

```bash
pytest tests/domain/test_models.py -v
```

### 5.2 커버리지 확인

```bash
pytest --cov=src/domain/models tests/domain/test_models.py
```

- **기준**: Coverage 95% 이상.

------

## Step 6: 마이그레이션 (Migration) 🐘

### 6.1 Alembic 초기화 (최초 1회)

```bash
alembic init alembic
```

### 6.2 Env 설정 (`alembic/env.py`)

- `src/core/database/base.py`의 `Base`를 import.
- `target_metadata = Base.metadata` 설정.
- `src/core/config.py`의 `settings.database_url`을 사용하여 `sqlalchemy.url` 설정.
- **주의**: `async_engine`을 사용하는 `run_migrations_online` 함수 확인.

### 6.3 리비전 생성

```bash
alembic revision --autogenerate -m "Initial tables"
```

- 생성된 `versions/xxxx_initial_tables.py` 확인 (4개 테이블 생성 코드 확인).

------

## Step 7: 리팩토링 (Refactor) 🔄

- [ ] 중복되는 컬럼 정의가 있다면 Mixin으로 분리 고려.
- [ ] 관계(Relationship) 정의가 필요한 경우 (`back_populates`) 추가.
- [ ] 모델 클래스 Docstring 작성 (`Example` 포함).

------

## Step 8: 문서화 (Documentation) 📝

- [ ] `src/domain/models.py` 상단에 모듈 설명 작성.
- [ ] 각 필드에 대한 주석(Comment) 작성 (특히 FK 관계).

------

## Step 9: 커밋 (Commit) ✅

### 9.1 Pre-commit 재확인

- [ ] Ruff, Mypy, Pytest 통과 확인.

### 9.2 Git Commit

```bash
git add src/domain/models.py tests/domain/test_models.py alembic/
git commit -m "feat(domain): Implement User, Room, Transcript, Insight entities"
```

------

