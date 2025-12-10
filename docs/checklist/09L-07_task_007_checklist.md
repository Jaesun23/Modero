# 09L-07_task_007_checklist

> **Task ID**: T007
> **Task 명**: 프론트엔드 스캐폴딩 및 타입 시스템 정의
> **관련 문서**: 07B-02 (Sec 2, 4), 03A-F01
> **예상 소요**: 2 hours

---

## Step 1: 목표 이해 ✅

### 1.1 Task 목표

- Vite + React + TS 환경 구축 및 Tailwind CSS 설정.
- 백엔드와 통신할 **WebSocket 메시지 타입 정의**.
- 상태 관리를 위한 **Zustand Store 인터페이스 정의**.

### 1.2 성공 기준

- [ ] `npm run dev` 정상 구동
- [ ] `src/types/websocket.ts` 파일 생성 및 타입 정의 완료
- [ ] `src/store/useMeetingStore.ts` 파일 생성 (기본 구조)
- [ ] **Lint 0, Type Check 0**

---

## Step 2: 테스트 작성 (TDD) 🧪

*기반 구축 단계이므로 Store의 초기 상태를 검증하는 테스트를 먼저 작성합니다.*

```typescript
// src/store/__tests__/useMeetingStore.test.ts
import { describe, it, expect } from 'vitest';
import { useMeetingStore } from '../useMeetingStore';

describe('useMeetingStore', () => {
  it('should have initial state', () => {
    const state = useMeetingStore.getState();
    expect(state.connectionStatus).toBe('idle');
    expect(state.transcripts).toEqual([]);
    expect(state.isMicOn).toBe(false);
  });
});
```

## Step 3: 구현 (Implementation) 🔨

### 3.1 프로젝트 초기화

```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install zustand lucide-react clsx tailwind-merge
npm install -D tailwindcss postcss autoprefixer vitest @testing-library/react jsdom
npx tailwindcss init -p
```

### 3.2 타입 시스템 정의 (Inline Spec)

*아래 코드를 `src/types/websocket.ts`에 그대로 구현하세요.*

```TypeScript
export type ConnectionStatus = 'idle' | 'connecting' | 'connected' | 'error';

export interface SttResultPayload {
  text: string;
  is_final: boolean;
  language_code: string;
}

export interface AiResponsePayload {
  type: 'SUMMARY' | 'WARNING' | 'SUGGESTION';
  content: string;
}

export type WebSocketMessage = 
  | { type: 'stt_result'; payload: SttResultPayload }
  | { type: 'ai_response'; payload: AiResponsePayload };

export interface Transcript {
  id: string;
  text: string;
  isFinal: boolean;
  timestamp: number;
}

export interface Insight {
  id: string;
  type: 'SUMMARY' | 'WARNING' | 'SUGGESTION';
  content: string;
  timestamp: number;
}
```

### 3.3 스토어 스켈레톤 구현

*`src/store/useMeetingStore.ts`*

```TypeScript
import { create } from 'zustand';
import { ConnectionStatus, Transcript, Insight } from '@/types/websocket';

interface MeetingState {
  connectionStatus: ConnectionStatus;
  isMicOn: boolean;
  transcripts: Transcript[];
  insights: Insight[];
  volume: number;
  
  actions: {
    setStatus: (status: ConnectionStatus) => void;
    setMicOn: (isOn: boolean) => void;
    addTranscript: (t: Transcript) => void;
    addInsight: (i: Insight) => void;
    setVolume: (vol: number) => void;
  };
}

export const useMeetingStore = create<MeetingState>((set) => ({
  connectionStatus: 'idle',
  isMicOn: false,
  transcripts: [],
  insights: [],
  volume: 0,
  actions: {
    // Implement actions here
    setStatus: (status) => set({ connectionStatus: status }),
    setMicOn: (isOn) => set({ isMicOn: isOn }),
    addTranscript: (t) => set((state) => ({ transcripts: [...state.transcripts, t] })),
    addInsight: (i) => set((state) => ({ insights: [...state.insights, i] })),
    setVolume: (vol) => set({ volume: vol }),
  },
}));

export const useMeetingActions = () => useMeetingStore((state) => state.actions);
```

------

## Step 4: 정적 검증 🔍

- [ ] `npx tsc --noEmit` (타입 오류 없음)
- [ ] `npm run lint` (ESLint 통과)

------

## Step 5: 단위 테스트 실행 ✅

- [ ] `npm run test` 실행하여 Store 초기 상태 테스트 통과 확인

------

## Step 6: 리팩토링 ✨

- [ ] Path Alias (`@/`)가 `tsconfig.json`과 `vite.config.ts`에 올바르게 설정되었는지 확인.

------

## Step 7: 통합 확인 🔗

- `App.tsx`에서 Store 값을 불러와 콘솔에 찍어보고 에러가 없는지 확인.

------

## Step 8: 문서화 📝

- `README.md`에 실행 방법 및 폴더 구조 기록.

------

## Step 9: 커밋 ✅

```Bash
git add .
git commit -m "feat(base): Setup Vite project with Types and Zustand store"
```

