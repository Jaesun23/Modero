# DNA Blueprint: Data System (Database)

## 1. 개요 및 목적 (Purpose & Scope)
- **목적**: 회의실 정보, 사용자 세션, 그리고 가장 중요한 **회의록(Transcript) 및 요약본**을 영구 저장하고 조회함.
- **핵심 가치**: "비동기 I/O를 통한 Non-blocking DB 접근" 및 "개발(SQLite)과 운영(PostgreSQL)의 매끄러운 전환".
- **범위**:
  - `SQLAlchemy 2.0` 기반의 Async ORM 구성
  - `Alembic`을 이용한 스키마 마이그레이션 자동화
  - 공통 모델(Base Mixin) 정의 (생성일, 수정일 등 자동 관리)

## 2. 디렉토리 구조 (Directory Structure)

```
src/
 └── core/
 └── database/
       ├── init.py       # 공개 API (get_session, Base 등) 노출
       ├── session.py        # Async Engine 및 SessionMaker 설정
       ├── base.py           # Declarative Base 모델 정의
       └── mixins.py         # 재사용 가능한 컬럼 (TimestampMixin 등)
```

## 3. 핵심 설계 결정 (Key Design Decisions)

### 3.1 Async SQLAlchemy (비동기 ORM)
- **결정**: 동기식 DB 드라이버 대신 `asyncpg`(PostgreSQL) 또는 `aiosqlite`(SQLite)를 사용하는 비동기 엔진을 구성함.
- **이유**: `ADR-002`의 실시간 스트리밍 파이프라인에서 DB 입출력이 Event Loop를 차단(Block)하면 전체 응답이 끊기기 때문.

### 3.2 Dual-Database Strategy
- **전략**:
  - **Local/Dev**: `sqlite+aiosqlite:///./app.db` (설치 불필요, 파일 기반)
  - **Prod**: `postgresql+asyncpg://...` (고성능, 동시성 제어)
- **구현**: 환경변수(`DATABASE_URL`)만 변경하면 코드 수정 없이 DB가 교체되도록 추상화함.

### 3.3 Code-First Schema Management
- **도구**: **Alembic** 사용.
- **방식**: Python 모델 코드를 작성하면 Alembic이 변경 사항을 감지하여 SQL 마이그레이션 파일(`versions/`)을 자동 생성함. 이를 통해 DB 스키마 변경 이력을 형상 관리함.

## 4. 공개 API (Public API)

### `get_session() -> AsyncGenerator[AsyncSession, None]`
- **역할**: FastAPI의 `Depends`로 주입되어 요청(Request) 단위의 DB 세션을 제공하고, 요청 종료 시 자동으로 닫음.
- **사용법**:
  ```python
  @app.get("/items")
  async def read_items(db: AsyncSession = Depends(get_session)):
      result = await db.execute(select(Item))
      return result.scalars().all()

### `TimestampMixin`

- **역할**: 모든 테이블에 공통적으로 필요한 `created_at`, `updated_at` 컬럼을 자동으로 추가하고 갱신함.

## 5. 의존성 (Dependencies)

- **필수 라이브러리**:
  - `sqlalchemy[asyncio]`
  - `alembic`
  - `aiosqlite` (개발용)
  - `asyncpg` (운영용 - 선택)
- **내부 의존성**:
  - `core.config`: DB URL 설정 로드

## 6. 테스트 전략 (Testing Strategy)

- **단위/통합 테스트 (`tests/core/database/`)**:
  - **In-memory SQLite**: 테스트 실행 시 파일이 아닌 메모리(`sqlite+aiosqlite:///:memory:`)에 DB를 생성하여, 테스트 속도를 극대화하고 데이터 오염을 방지함.
  - 세션의 생성, 커밋, 롤백 동작 검증.
- **목표 커버리지**: 95%+

## 7. 구현 우선순위

1. `session.py`: 엔진 및 세션 팩토리 구성
2. `base.py` & `mixins.py`: 기본 모델 구조 정의
3. `alembic` 초기화 (`alembic init`)