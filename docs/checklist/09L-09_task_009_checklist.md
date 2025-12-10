# 09L-09_task_009_checklist

> **Task ID**: T009
> **Task 명**: WebSocket 통신 및 상태 동기화
> **관련 문서**: 07B-02 (Sec 4.1), T007 완료
> **예상 소요**: 3 hours

---

## Step 1: 목표 이해 ✅

### 1.1 Task 목표

- `SocketClient` 클래스 구현 (연결, 송신, 수신).
- 서버 메시지(`stt_result`, `ai_response`) 파싱 후 Store 업데이트.
- 연결 끊김 시 자동 재연결(Exponential Backoff).

### 1.2 성공 기준

- [ ] 로컬 서버(`ws://localhost:8000/ws`) 연결 성공.
- [ ] 메시지 수신 시 `useMeetingStore`의 상태가 변경됨.
- [ ] `sendAudio()` 메서드로 바이너리 데이터 전송 가능.

---

## Step 2: 테스트 작성 (TDD) 🧪

```typescript
// src/lib/websocket/__tests__/SocketClient.test.ts
import { describe, it, expect, vi } from 'vitest';
import { SocketClient } from '../SocketClient';

describe('SocketClient', () => {
  it('should connect to url', () => {
    const client = new SocketClient('ws://test');
    // Mock WebSocket & Test connect logic
  });
});
```

## Step 3: 구현 (Implementation) 🔨

### 3.1 인터페이스 정의 (Inline Spec)

*`src/lib/websocket/SocketClient.ts`*

```TypeScript
type MessageHandler = (data: any) => void;

export class SocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  
  constructor(url: string, private onMessage: MessageHandler, private onStatusChange: (status: string) => void) {
    this.url = url;
  }

  connect() {
    // 1. new WebSocket(this.url)
    // 2. Setup onopen, onclose, onerror, onmessage
    // 3. onmessage: parse JSON -> call this.onMessage
    // 4. onclose: handle reconnect (exponential backoff)
  }

  sendAudio(chunk: Blob | ArrayBuffer) {
    // if open, this.ws.send(chunk)
  }

  disconnect() {
    // close socket, clear reconnect timers
  }
}
```

### 3.2 훅 구현 (Store 연결)

*`src/hooks/useSocket.ts`*

```TypeScript
export const useSocket = () => {
  const actions = useMeetingActions();
  const socketRef = useRef<SocketClient | null>(null);

  useEffect(() => {
    socketRef.current = new SocketClient(
      '/ws', // Vite Proxy 사용
      (data) => {
        // Handle Messages
        if (data.type === 'stt_result') actions.addTranscript(data.payload);
        if (data.type === 'ai_response') actions.addInsight(data.payload);
      },
      (status) => actions.setStatus(status)
    );
    
    return () => socketRef.current?.disconnect();
  }, []);

  return socketRef.current;
};
```

------

## Step 4: 정적 검증 🔍

- [ ] `npx tsc` (엄격한 타입 체크)

------

## Step 5: 단위 테스트 실행 ✅

- [ ] `npm run test`

------

## Step 6: 리팩토링 ✨

- [ ] 재연결 로직에서 최대 재연결 횟수 제한(Max retries) 추가.

------

## Step 7: 통합 확인 (Manual) 🔗

- 백엔드 서버를 켜고 `connect()` 시도 시 Store의 `connectionStatus`가 `connected`로 변하는지 확인.

------

## Step 8: 문서화 📝

- SocketClient 재연결 전략 주석 작성.

------

## Step 9: 커밋 ✅

```bash
git add .
git commit -m "feat(socket): Implement SocketClient with auto-reconnect and store integration"
```

