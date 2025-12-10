# DNA Blueprint: Security System (Auth)

## 1. 개요 및 목적 (Purpose & Scope)
- **목적**: WebSocket 연결 요청 시 유효한 사용자인지 검증하고, 각 연결에 고유한 사용자 정보(`user_id`, `room_id`)를 식별하여 바인딩함.
- **핵심 가치**: "인증되지 않은 WebSocket 접근 차단" 및 "Stateless 인증 처리를 통한 인프라 의존성 제거".
- **범위**:
  - JWT(JSON Web Token) 기반의 액세스 토큰 생성 및 검증
  - WebSocket 핸드셰이크 시점의 인증 미들웨어(Dependency)
  - 비밀 키(Secret Key) 관리

## 2. 디렉토리 구조 (Directory Structure)

```
src/
 └── core/
 └── security/
       ├── init.py       # 공개 API (create_access_token, get_current_user 등)
       ├── jwt.py            # JWT 인코딩/디코딩 로직
       └── pwd.py            # (선택) 비밀번호 해싱 유틸리티 (Passlib)
```

## 3. 핵심 설계 결정 (Key Design Decisions)

### 3.1 JWT (Stateless Authentication)
- **결정**: 세션 저장소(Redis/DB) 없이 검증 가능한 **JWT(HS256)**를 사용함.
- **이유**: `ADR-202`(No-Redis) 제약에 따라, 서버 메모리에 세션을 저장하는 대신 토큰 자체에 정보를 담아 서버 재시작 시에도 인증 유효성을 유지(Stateless)하려 함.

### 3.2 WebSocket 인증 방식: Query Parameter
- **결정**: WebSocket 연결 URL에 `ws://...?token=xyz` 형태로 토큰을 전달함.
- **이유**: 표준 브라우저 WebSocket API는 커스텀 헤더(Authorization) 설정을 지원하지 않는 경우가 많아, 호환성을 위해 쿼리 파라미터 방식을 채택.

### 3.3 임시 익명 사용자 지원
- **전략**: 복잡한 가입 절차 없이, '닉네임'만 입력하면 즉시 임시 `user_id`와 JWT를 발급하는 "Guest Login" 기능을 구현하여 대회 시연 시 접근성을 높임.

## 4. 공개 API (Public API)

### `create_access_token(data: dict) -> str`
- **역할**: 사용자 정보(`sub`, `room_id`)와 만료 시간(`exp`)을 담은 JWT 문자열 생성.
- **사용법**: 로그인 API에서 호출하여 클라이언트에게 반환.

### `get_current_user_ws(token: str) -> UserPayload`
- **역할**: WebSocket 연결 시 토큰을 검증하고 사용자 정보를 반환. 유효하지 않으면 `WebSocketDisconnect` 예외 발생.
- **사용법**:
  ```python
  @app.websocket("/ws")
  async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
      user = verify_token_ws(token)
      # 연결 수락

## 5. 의존성 (Dependencies)

- **외부 라이브러리**:
  - `pyjwt` (JWT 처리)
  - `passlib[bcrypt]` (비밀번호 해싱 - 필요시)
- **내부 의존성**:
  - `core.config`: JWT Secret Key 및 알고리즘 설정 로드

## 6. 테스트 전략 (Testing Strategy)

- **단위 테스트 (`tests/core/security/`)**:
  - 유효한 토큰 생성 및 디코딩 성공 여부 검증.
  - 만료된 토큰이나 조작된 토큰 입력 시 `InvalidTokenError` 발생 검증.
  - Secret Key 변경 시 기존 토큰 무효화 확인.
- **목표 커버리지**: 100%

## 7. 구현 우선순위

1. `jwt.py`: 토큰 생성/검증 핵심 로직
2. `__init__.py`: FastAPI Dependency (`Depends`) 래퍼 구현