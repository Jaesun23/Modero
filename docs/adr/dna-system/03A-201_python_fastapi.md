# ADR-201: Python & FastAPI 선정

**상태**: 승인됨 (Accepted)
**일자**: 2025-12-10
**카테고리**: 기술 스택
**관련 문서**: 02D-01_tech_stack.md

## 1. 맥락 (Context)
본 프로젝트는 **'바이브코딩 대회'** 출품작으로, 제한된 시간 내에 AI 기능을 통합한 실시간 웹앱을 완성해야 합니다.
STT/LLM 처리를 위한 라이브러리 지원과 WebSocket을 통한 비동기 처리가 동시에 요구됩니다.

## 2. 검토한 대안
* **Node.js**: 실시간(WebSocket) 처리에 강하나, AI/데이터 처리 라이브러리 생태계가 Python에 비해 부족함.
* **Go**: 성능은 최고이나, 대회 기간 내에 생산성을 극대화하기엔 팀의 러닝 커브가 존재함.
* **Python (FastAPI)**: Gemini SDK 등 AI 라이브러리가 가장 풍부하며, `asyncio`를 통한 비동기 성능도 충분함.

## 3. 결정 (Decision)
**Python 3.12+**와 **FastAPI**를 사용합니다.
단, 성능 확보를 위해 **모든 I/O 바운드 작업(DB, API 호출)은 비동기(`async/await`)로 구현**하는 것을 강제합니다.

## 4. 결과 (Consequences)
* ✅ **긍정적**: Gemini, Google STT 등 핵심 라이브러리를 네이티브로 사용 가능. 개발 속도 극대화.
* ⚠️ **부정적**: 동기 함수(`time.sleep`, `requests` 등) 실수 사용 시 전체 서버가 멈출 위험 있음.
* **대응**: `PROJECT_STANDARDS`에서 동기 함수 사용을 엄격히 금지(Linting)함.