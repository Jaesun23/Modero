# 09L-09_task_009_checklist

> **Task ID**: T009
> **Task 명**: WebSocket 클라이언트 모듈 구현
> **관련 문서**: 07B-02 (Sec 4.1), T007 완료
> **예상 소요**: 3 hours

## Step 1: 목표 이해 ✅

### 1.1 목표
- 백엔드(`ws://localhost:8000`)와 안정적인 연결을 유지한다.
- 오디오 바이너리 데이터를 전송하고, STT/AI JSON 응답을 수신한다.
- 연결 끊김 시 자동 재연결(Retry) 로직을 수행한다.

## Step 2: SocketClient 클래스 구현 🔨

**파일**: `src/lib/websocket/SocketClient.ts`

### 2.1 기본 구조
- `connect(url: string, token: string)`: 소켓 생성 및 이벤트 리스너 등록
- `disconnect()`: 소켓 종료 및 리소스 정리
- `send(data: ArrayBuffer | string)`: 데이터 전송 (연결 상태 체크 포함)

### 2.2 이벤트 핸들링
- **`onopen`**: `useMeetingStore`의 상태를 `connected`로 변경
- **`onclose` / `onerror`**: 상태를 `disconnected` 또는 `error`로 변경 후 재연결 시도
- **`onmessage`**:
  - 수신 데이터 `JSON.parse`
  - 메시지 `type` (`stt_result` | `ai_response`) 분기
  - Store Action (`addTranscript`, `addInsight`) 호출

### 2.3 재연결 전략 (Backoff)
- `setTimeout`을 사용하여 1s, 2s, 4s... 간격으로 `connect()` 재시도
- 최대 재연결 횟수(예: 5회) 제한

## Step 3: Store 연동 🔨

**파일**: `src/hooks/useSocket.ts` (선택적)
- 컴포넌트에서 쉽게 사용할 수 있도록 `SocketClient`를 감싸는 Hook 작성
- 마운트 시 연결, 언마운트 시 해제 로직 관리

## Step 4: 검증 (Verification) ✅

- [ ] 로컬 백엔드 서버(`uvicorn`) 실행
- [ ] 프론트엔드에서 연결 시도 -> 백엔드 로그에 "Connected" 확인
- [ ] 오디오 데이터 전송 시 백엔드에서 수신 확인
- [ ] 백엔드 강제 종료 시 프론트엔드에서 재연결 시도 로그 확인

------

