# ADR-402: 설정(Configuration) 관리 표준

**상태**: 승인됨 (Accepted)
**일자**: 2025-12-10
**카테고리**: DNA 시스템 (Configuration)

## 1. 맥락 (Context)
Google Cloud Credentials, Gemini API Key 등 민감 정보가 포함되어 있습니다.
하드코딩은 보안 사고로 직결되며, 대회 제출 시 코드가 공개될 수 있어 위험합니다.

## 2. 결정 (Decision)
* 도구: **`pydantic-settings`** 사용.
* 방식: `.env` 파일에서 환경변수를 로드하고, 앱 시작 시 **타입 검사(Validation)**를 수행. 필수 키 누락 시 서버 실행 차단.

## 3. 결과 (Consequences)
* 코드를 GitHub에 공개해도 API Key 유출 위험 없음.
* `config.py`를 통해 Type-safe하게 설정값에 접근 가능 (`settings.gemini_api_key`).