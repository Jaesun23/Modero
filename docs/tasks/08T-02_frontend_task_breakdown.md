# Frontend Task Breakdown

> 프로젝트: Modero (Frontend)
>
> 버전: v1.0
>
> 작성일: 2025-12-10
>
> Blueprint 참조: 07B-02_frontend_blueprint.md

------

## 1. 개요

| **항목**         | **값**                    |
| ---------------- | ------------------------- |
| **총 Task 수**   | 5개                       |
| **예상 총 시간** | 12시간                    |
| **예상 세션 수** | 5세션 (Task당 1세션 권장) |
| **핵심 경로**    | T007 → T009 → T010        |

------

## 2. Phase 1: Foundation (기반 구축 - Easy)

> **목표**: 프로젝트 환경을 설정하고, 공통 레이아웃과 타입 시스템을 정의합니다.

| **ID**   | **Task 명**                     | **난이도** | **예상** | **의존성** | **Blueprint 참조** |
| -------- | ------------------------------- | ---------- | -------- | ---------- | ------------------ |
| **T007** | 프론트엔드 스캐폴딩 및 레이아웃 | Easy       | 2h       | -          | Sec 2, Sec 3.1     |

------

## 3. Phase 2: Core Logic (핵심 모듈 - Intermediate)

> **목표**: UI 없는 상태에서 핵심 비즈니스 로직(오디오, 통신, 상태)을 구현합니다.

| **ID**   | **Task 명**                        | **난이도**   | **예상** | **의존성** | **Blueprint 참조** |
| -------- | ---------------------------------- | ------------ | -------- | ---------- | ------------------ |
| **T008** | 오디오 처리 모듈 (AudioRecorder)   | Intermediate | 2h       | T007       | Sec 4.2            |
| **T009** | 통신 및 상태 관리 (Socket & Store) | Intermediate | 3h       | T007       | Sec 3.2, Sec 4.1   |

------

## 4. Phase 3: Integration (통합 - Final)

> **목표**: 로직과 UI를 결합하고, 실제 서버와 연동하여 기능을 완성합니다.

| **ID**   | **Task 명**              | **난이도** | **예상** | **의존성** | **Blueprint 참조** |
| -------- | ------------------------ | ---------- | -------- | ---------- | ------------------ |
| **T010** | UI 컴포넌트 구현 및 조립 | Final      | 3h       | T008, T009 | Sec 3.1, Sec 6     |
| **T011** | E2E 통합 및 최적화       | Final      | 2h       | T010       | Sec 8              |

------

## 5. 의존성 다이어그램

코드 스니펫

```
graph TD
    T007[T007: Scaffolding] --> T008[T008: Audio Logic]
    T007 --> T009[T009: Socket & Store]
    
    T008 --> T010[T010: UI Integration]
    T009 --> T010
    
    T010 --> T011[T011: E2E & Optimize]
```

------

## 6. Task 상세 정의

### Task 007: 프론트엔드 스캐폴딩 및 레이아웃

#### 메타 정보

- **ID**: T007
- **난이도**: Easy
- **예상 시간**: 2시간
- **의존성**: 없음

#### 목표

Vite 프로젝트를 초기화하고, Tailwind CSS 기반의 기본 레이아웃(Header, Main, Footer)과 공통 타입을 정의한다.

#### 입력

- Blueprint **Section 2.1** (기술 스택)
- Blueprint **Section 2.2** (디렉토리 구조)
- Blueprint **Section 3.1** (계층 구조)

#### 출력

- 프로젝트 구조 (`src/api`, `src/components`, `src/lib` 등)
- `src/types/websocket.ts` (타입 정의)
- `src/layouts/MainLayout.tsx` (기본 레이아웃)
- `npm run dev` 실행 가능한 상태

#### 제약

- **MUST**: TypeScript Strict 모드 활성화
- **MUST**: Path Alias (`@/`) 설정
- **MUST**: Tailwind CSS 초기 설정 완료

#### 완료 조건

- [ ] Vite + React + TS 프로젝트 생성 완료
- [ ] Tailwind CSS 적용 확인 (배경색 변경 등 테스트)
- [ ] 기본 레이아웃 컴포넌트 렌더링 확인

------

### Task 008: 오디오 처리 모듈 (AudioRecorder)

#### 메타 정보

- **ID**: T008
- **난이도**: Intermediate
- **예상 시간**: 2시간
- **의존성**: T007

#### 목표

브라우저 마이크 권한을 획득하고, 오디오 스트림을 바이너리 청크로 변환하는 `AudioRecorder` 클래스를 구현한다.

#### 입력

- Blueprint **Section 4.2** (오디오 인터페이스)
- Blueprint **Section 2.3** (데이터 흐름)

#### 출력

- `src/lib/audio/AudioRecorder.ts`
- `src/hooks/useAudio.ts` (선택적)

#### 제약

- **MUST**: `MediaRecorder` API 사용
- **MUST**: 250ms 간격(`timeslice`)으로 데이터 청크 생성
- **MUST**: 오디오 볼륨 레벨 계산 로직 포함 (시각화용)

#### 완료 조건

- [ ] 마이크 권한 요청 및 획득 성공
- [ ] 콘솔에 `ArrayBuffer` 데이터가 주기적으로 출력됨 확인
- [ ] 볼륨 레벨(0~100) 값이 실시간으로 변화함 확인

------

### Task 009: 통신 및 상태 관리 (Socket & Store)

#### 메타 정보

- **ID**: T009
- **난이도**: Intermediate
- **예상 시간**: 3시간
- **의존성**: T007

#### 목표

WebSocket 클라이언트를 구현하여 서버와 통신하고, 수신된 데이터를 Zustand Store에 실시간으로 반영한다.

#### 입력

- Blueprint **Section 4.1** (WebSocket 프로토콜)
- Blueprint **Section 3.2** (핵심 상태)
- Blueprint **Section 7** (보안/토큰)

#### 출력

- `src/lib/websocket/SocketClient.ts`
- `src/store/useMeetingStore.ts`
- `src/hooks/useSocket.ts`

#### 제약

- **MUST**: `stt_result`와 `ai_response` 메시지 타입 분기 처리
- **MUST**: 연결 끊김 시 자동 재연결(Exponential Backoff) 구현
- **MUST**: Zustand Store 구조 (`transcripts`, `insights`) 준수

#### 완료 조건

- [ ] 로컬 백엔드(`ws://localhost:8000`)와 연결 성공
- [ ] 가짜 메시지 수신 시 Store 상태 업데이트 확인 (Redux DevTools 등 활용)
- [ ] 재연결 로직 동작 확인 (서버 재시작 시)

------

### Task 010: UI 컴포넌트 구현 및 조립

#### 메타 정보

- **ID**: T010
- **난이도**: Final
- **예상 시간**: 3시간
- **의존성**: T008, T009

#### 목표

개별 구현된 오디오/소켓 모듈을 UI 컴포넌트(`TranscriptViewer`, `InsightPanel`, `Controls`)와 연결하고 화면을 완성한다.

#### 입력

- Blueprint **Section 3.1** (컴포넌트 모델)
- Blueprint **Section 6** (에러 처리 UI)

#### 출력

- `src/components/feature/TranscriptViewer.tsx`
- `src/components/feature/InsightPanel.tsx`
- `src/components/feature/MeetingController.tsx`
- `src/App.tsx` (최종 조립)

#### 제약

- **MUST**: `is_final` 상태에 따라 자막 스타일 구분 (회색/검은색)
- **MUST**: 새 메시지 도착 시 자동 스크롤
- **MUST**: 마이크 버튼 상태 동기화 (Store <-> AudioRecorder)

#### 완료 조건

- [ ] 말하면 화면에 실시간으로 자막이 표시됨
- [ ] AI 응답 시 인사이트 카드가 우측에 생성됨
- [ ] 마이크 끄기/켜기 버튼이 정상 동작함

------

### Task 011: E2E 통합 및 최적화

#### 메타 정보

- **ID**: T011
- **난이도**: Final
- **예상 시간**: 2시간
- **의존성**: T010

#### 목표

실제 시나리오 기반으로 전체 기능을 테스트하고, 프로덕션 빌드를 위한 최적화를 수행한다.

#### 입력

- Blueprint **Section 8** (다음 단계)

#### 출력

- 최종 빌드 파일 (`dist/`)
- 버그 수정 커밋

#### 제약

- **MUST**: 콘솔 에러/경고 제거
- **MUST**: 프로덕션 빌드(`npm run build`) 성공

#### 완료 조건

- [ ] "회의 시작 -> 발언 -> AI 피드백 -> 회의 종료" 시나리오 성공
- [ ] 브라우저 리사이즈 등 반응형 동작 확인
- [ ] 배포 가능한 정적 파일 생성 확인

------

