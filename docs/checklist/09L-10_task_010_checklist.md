

# 09L-10_task_010_checklist

> **Task ID**: T010
> **Task 명**: UI 컴포넌트 구현 및 통합
> **관련 문서**: 07B-02 (Sec 3.1, Sec 6)
> **예상 소요**: 3 hours

---

## Step 1: 목표 이해 ✅

### 1.1 Task 목표

- `TranscriptViewer`: 실시간 자막 표시, 자동 스크롤.
- `InsightPanel`: AI 피드백 카드 렌더링.
- `MeetingController`: 마이크 제어 및 오디오 연결.

### 1.2 성공 기준

- [ ] 자막이 `is_final` 여부에 따라 회색/검은색으로 구분됨.
- [ ] 새로운 자막 추가 시 뷰어가 자동으로 아래로 스크롤됨.
- [ ] 마이크 버튼 클릭 시 `AudioRecorder`와 `Socket`이 연동되어 작동.

---

## Step 2: 테스트 작성 (TDD) 🧪

*UI 컴포넌트 렌더링 테스트.*

```typescript
// src/components/feature/__tests__/TranscriptViewer.test.tsx
import { render, screen } from '@testing-library/react';
import { TranscriptViewer } from '../TranscriptViewer';

test('renders transcripts', () => {
  const dummyData = [{ id: '1', text: 'Hello', isFinal: true, timestamp: 0 }];
  render(<TranscriptViewer transcripts={dummyData} />);
  expect(screen.getByText('Hello')).toBeInTheDocument();
});
```

## Step 3: 구현 (Implementation) 🔨

### 3.1 TranscriptViewer

*`src/components/feature/TranscriptViewer.tsx`*

- **Props**: `transcripts: Transcript[]`
- **Style**:
  - `isFinal === true`: `text-gray-900`
  - `isFinal === false`: `text-gray-400 italic`
- **Logic**: `useEffect`와 `useRef`를 사용하여 배열 변경 시 `scrollIntoView` 호출.

### 3.2 InsightPanel

*`src/components/feature/InsightPanel.tsx`*

- **Props**: `insights: Insight[]`
- **UI**: 카드 형태 (`border rounded-lg p-4 shadow-sm`).
- **Icons**: Lucide React 아이콘 사용 (`AlertTriangle` for WARNING, `Lightbulb` for SUGGESTION).

### 3.3 MeetingController (Integration)

*`src/components/feature/MeetingController.tsx`*

- **Hooks**: `useAudio`, `useSocket`, `useMeetingStore`

- **Logic**:

  ```TypeScript
  const toggleMic = async () => {
    if (isMicOn) {
      recorder.stop();
      socket.disconnect();
    } else {
      await recorder.start((chunk) => socket.sendAudio(chunk));
      socket.connect();
    }
    // Update Store
  };
  ```

------

## Step 4: 정적 검증 🔍

- [ ] `npm run lint`

------

## Step 5: 단위 테스트 실행 ✅

- [ ] UI 컴포넌트 렌더링 테스트 통과.

------

## Step 6: 리팩토링 ✨

- [ ] 컴포넌트 내부의 복잡한 로직을 Custom Hook으로 분리.

------

## Step 7: 통합 확인 (Manual) 🔗

- `App.tsx`에 위 컴포넌트들을 배치하고 전체 흐름(Start -> Talk -> Display) 확인.

------

## Step 8: 문서화 📝

- 컴포넌트 Props 문서화.

------

## Step 9: 커밋 ✅

```bash
git add .
git commit -m "feat(ui): Implement TranscriptViewer, InsightPanel, and Controls"
```

