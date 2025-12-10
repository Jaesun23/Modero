# ADR-202: 인프라 최소화 (No-Redis) 전략

**상태**: 승인됨 (Accepted)
**일자**: 2025-12-10
**카테고리**: 기술 스택
**관련 문서**: 02C-01_external_constraints.md (인프라 제약)

## 1. 맥락 (Context)
실시간 채팅/알림을 위해선 일반적으로 Redis Pub/Sub나 Kafka가 필요합니다.
하지만 대회 환경 특성상 **배포 복잡도를 낮추고 운영 비용을 '0'으로 수렴**시켜야 합니다.

## 2. 결정 (Decision)
별도의 메시지 브로커(Redis/Kafka) 없이, **Python 내장 `asyncio.Queue`와 `Memory Object`**를 사용하여 단일 서버 내에서 Pub/Sub를 구현합니다.

## 3. 결과 (Consequences)
* ✅ **긍정적**: `docker-compose` 없이 Python 코드만 실행하면 서버 가동. 배포/디버깅 속도 매우 빠름.
* ❌ **부정적**: 서버 재시작 시 대기 중인 메시지 소실. 스케일 아웃(서버 2대 이상) 불가능.
* **대응**: 대회 데모용이므로 단일 서버로 충분하며, 데이터 영속성이 필요한 내용은 즉시 DB(PostgreSQL/SQLite)에 기록함.