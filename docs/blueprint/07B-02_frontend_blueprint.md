# Frontend Architecture Blueprint

> 프로젝트: Modero (Frontend)
>
> 버전: v1.0
>
> 작성일: 2025-12-10
>
> 패밀리: B-C-A (실시간 스트리밍) - 프론트엔드 관점

------

## 1. 시스템 개요 (System Overview)

### 1.1 목적

사용자의 음성을 실시간으로 캡처하여 서버로 전송하고, 서버로부터 수신된 STT(자막)와 AI 분석 결과(인사이트)를 지연 없이 시각화하여 회의 참여를 돕는 단일 페이지 애플리케이션(SPA)입니다.

### 1.2 범위

- **포함**: 마이크 제어, 실시간 오디오 비주얼라이저, 실시간 자막 스트림, AI 인사이트 카드 뷰, 연결 상태 관리.
- **제외**: 로그인/회원가입 페이지 (이번 MVP에서는 URL 쿼리 파라미터 토큰 방식 사용 또는 하드코딩된 토큰 사용), 지난 회의 이력 조회.

### 1.3 핵심 기능 및 우선순위

| **기능**        | **설명**                                                     | **우선순위** |
| --------------- | ------------------------------------------------------------ | ------------ |
| **실시간 자막** | 서버에서 오는 STT 스트림을 `is_final` 상태에 따라 구분하여 표시 | P0           |
| **오디오 전송** | 브라우저 마이크 입력을 바이너리 청크로 변환하여 WebSocket 전송 | P0           |
| **AI 피드백**   | Gemini가 보낸 JSON 데이터를 파싱하여 적절한 UI 카드(요약/경고)로 렌더링 | P0           |
| **연결 관리**   | WebSocket 연결 끊김 시 자동 재연결 및 UI 피드백              | P1           |

------

## 2. 아키텍처 구조 (Architecture)

### 2.1 기술 스택 (Ref: ADR-F01)

- **Framework**: React 18 + Vite + TypeScript
- **State**: Zustand (전역 상태), React Query (비동기 데이터 - 추후 확장용)
- **Styling**: Tailwind CSS
- **Audio**: Native MediaRecorder API

### 2.2 디렉토리 구조 및 역할

Plaintext

```
src/
├── api/                # HTTP API 클라이언트 (Login 등)
├── assets/             # 정적 리소스
├── components/         # Presentational Components
│   ├── ui/             # 공통 UI (Button, Card, Badge - Atomic)
│   └── feature/        # 도메인 특화 컴포넌트 (TranscriptView, InsightPanel)
├── hooks/              # Custom Hooks (useAudio, useSocket)
├── layouts/            # 페이지 레이아웃 구조
├── lib/                # 핵심 로직 모듈 (Audio, Socket, Utils)
├── store/              # Zustand Global State
├── types/              # TypeScript Type Definitions
└── App.tsx             # 라우팅 및 전역 Provider
```

### 2.3 데이터 흐름 (Unidirectional)

코드 스니펫

```
Mic Input -> [AudioRecorder] -> Blob -> [SocketClient] -> Server
                                              |
Server -> [SocketClient] -> JSON Parsing -> [Zustand Store] -> [React Components] -> UI Update
```

------

## 3. 컴포넌트 모델 (Component Model)

### 3.1 계층 구조

- **MainLayout**: Header(Status), Content Area, Footer(Controls)
- **MeetingRoom (Page)**
  - **LeftPanel**: `TranscriptList`
    - `TranscriptItem` (Props: text, isFinal, user)
  - **RightPanel**: `InsightList`
    - `InsightCard` (Props: type, content, timestamp)
  - **ControlBar**: `MicButton`, `VolumeVisualizer`, `ConnectionBadge`

### 3.2 핵심 상태 (Zustand Store)

Store: useMeetingStore

| State | Type | 설명 |

|-------|------|------|

| connectionStatus | 'idle' | 'connecting' | 'connected' | 'error' | WebSocket 연결 상태 |

| isMicOn | boolean | 마이크 활성화 여부 |

| transcripts | Transcript[] | 대화 기록 배열 |

| insights | Insight[] | AI 분석 결과 배열 |

| volume | number (0-100) | 오디오 시각화용 볼륨 레벨 |

------

## 4. 통신 및 인터페이스 설계 (API Design)

### 4.1 WebSocket 프로토콜

**Ref**: Backend Blueprint Section 3.2 (`WebSocketMessage`)

- **수신 메시지 (`Server -> Client`)**

  TypeScript

  ```
  interface SttResultPayload {
      text: string;
      is_final: boolean;
      language_code: string;
  }
  
  interface AiResponsePayload {
      type: 'SUMMARY' | 'WARNING' | 'SUGGESTION';
      content: string;
  }
  ```

- **송신 메시지 (`Client -> Server`)**

  - **Type**: `Binary` (ArrayBuffer)
  - **Rate**: 250ms 간격 (TimeSlice)

### 4.2 오디오 인터페이스

**Class**: `AudioRecorder`

- `start()`: 스트림 획득 및 녹음 시작
- `stop()`: 녹음 중지 및 스트림 해제
- `getVolume()`: AnalyserNode를 통한 실시간 볼륨 측정

------

## 5. 데이터 저장 및 관리 (Data Strategy)

### 5.1 상태 지속성 (Persistence)

- **전략**: 이번 MVP에서는 브라우저 새로고침 시 대화 내용이 초기화되는 **In-Memory** 방식을 기본으로 함.
- **확장**: 추후 `persist` 미들웨어를 사용하여 `localStorage`에 임시 저장하거나, 백엔드 API (`GET /history`)를 통해 복원.

------

## 6. 에러 처리 (Error Handling)

### 6.1 사용자 피드백 전략

| **상황**             | **처리 방식**                | **UI 피드백**                                           |
| -------------------- | ---------------------------- | ------------------------------------------------------- |
| **마이크 권한 거부** | `AudioPermissionError` throw | 모달: "마이크 사용을 허용해주세요."                     |
| **소켓 연결 실패**   | 자동 재연결(Backoff) 시도    | 상단 배지: "연결 중..." (주황색) -> "오프라인" (빨간색) |
| **서버 에러 메시지** | Toast 알림 표시              | 우측 하단 Toast: "서버 오류: [내용]"                    |

------

## 7. 보안 (Security)

### 7.1 인증 토큰 관리

- **저장**: `sessionStorage` (탭 종료 시 휘발) 또는 메모리 변수.
- **전송**: WebSocket 연결 URL의 Query Parameter (`?token=...`)로 전송.
- **XSS 방지**: React의 기본 이스케이핑 활용, `dangerouslySetInnerHTML` 사용 금지.

------

