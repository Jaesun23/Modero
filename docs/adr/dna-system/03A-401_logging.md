# ADR-401: 비동기 로깅(Logging) 표준

**상태**: 승인됨 (Accepted)
**일자**: 2025-12-10
**카테고리**: DNA 시스템 (Observability)

## 1. 맥락 (Context)
WebSocket 연결과 비동기 태스크가 수십 개 동시에 돌아가는 환경에서 `print()`문은 출력이 뒤섞여 디버깅이 불가능합니다.
또한, 동기식 로깅은 I/O를 차단(Block)하여 실시간성을 해칠 수 있습니다.

## 2. 결정 (Decision)
* 라이브러리: **`structlog`** 사용 (JSON 구조화 로깅).
* 포맷: 개발 환경은 컬러 콘솔, 운영 환경은 JSON.
* 필수 컨텍스트: 모든 로그에 `trace_id`(요청/연결 ID)를 자동 주입하여 흐름을 추적 가능하게 함.

## 3. 준수 (Compliance)
* `print()` 사용 시 CI/CD 파이프라인(Ruff Linter `T201`)에서 빌드 실패 처리.