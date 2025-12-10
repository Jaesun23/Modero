# DNA Blueprint: Configuration System

## 1. 개요 및 목적 (Purpose & Scope)
- **목적**: 실행 환경(Development/Production)에 따라 애플리케이션 설정을 분리하고, 필수 환경변수(API Key 등)의 존재 여부와 타입을 앱 시작 시점에 검증함.
- **핵심 가치**: "설정 오류로 인한 런타임 에러 방지" 및 "비밀 정보(Secret)의 안전한 관리".
- **범위**:
  - `.env` 파일 로딩 및 환경변수 오버라이딩
  - `pydantic` 기반의 엄격한 타입 검사 (Type-safe Settings)
  - 싱글톤 패턴을 통한 설정 접근 일원화

## 2. 디렉토리 구조 (Directory Structure)

```
src/
 └── core/
 └── config/
       ├── init.py       # 공개 API (get_settings, Settings 등) 노출
       └── settings.py       # Pydantic 모델 정의 및 로딩 로직
```

## 3. 핵심 설계 결정 (Key Design Decisions)

### 3.1 Pydantic Settings 활용
- **결정**: `BaseSettings`를 상속받아 설정 클래스를 정의함.
- **이유**: 환경변수 읽기, 타입 변환(str -> int/bool), 유효성 검사(필수값 체크)를 단 한 줄의 코드로 처리 가능.

### 3.2 계층적 설정 관리
- **구조**:
  - `BaseConfig`: 공통 설정 (앱 이름, 버전 등)
  - `ServerConfig`: 서버 실행 관련 (Host, Port)
  - `ModelConfig`: AI 모델 관련 (Gemini API Key, Model Name)
  - `STTConfig`: STT 관련 (Google Credential)
  - `Settings`: 위 설정들을 통합하는 최상위 클래스
- **이유**: 설정이 많아질 경우를 대비해 도메인별로 그룹화하여 가독성 확보.

### 3.3 환경별 `.env` 파일 지원
- **전략**: 기본적으로 `.env` 파일을 읽되, 시스템 환경변수가 있으면 우선순위를 가짐 (Docker/Cloud 배포 친화적).

## 4. 공개 API (Public API)

### `Settings` 클래스
- **역할**: 모든 설정 값의 집합체.
- **주요 필드**:
  - `env`: `Literal["dev", "prod"]`
  - `gemini_api_key`: `SecretStr` (로그 출력 시 마스킹 처리됨)
  - `google_application_credentials`: `FilePath` (파일 존재 여부 자동 검증)

### `get_settings() -> Settings`
- **역할**: `lru_cache`를 적용하여 설정 객체를 캐싱하고 싱글톤처럼 반환.
- **사용법**:
  ```python
  from core.config import get_settings
  
  settings = get_settings()
  print(settings.gemini_api_key.get_secret_value())

## 5. 의존성 (Dependencies)

- **외부 라이브러리**:
  - `pydantic-settings`
  - `pydantic[email]` (이메일 등 추가 검증 필요 시)

## 6. 테스트 전략 (Testing Strategy)

- **단위 테스트 (`tests/core/config/`)**:
  - 필수 환경변수(`GEMINI_API_KEY`) 누락 시 `ValidationError` 발생 여부 검증.
  - 잘못된 타입(예: Port에 문자열 입력) 시 에러 발생 검증.
  - `.env` 파일 오버라이딩 동작 확인.
- **목표 커버리지**: 100%

## 7. 구현 우선순위

1. `settings.py`: 기본 구조 및 Gemini/Google 설정 정의
2. `__init__.py`: API 노출 및 캐싱 적용