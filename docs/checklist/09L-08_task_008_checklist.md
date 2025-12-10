# 09L-08_task_008_checklist

> **Task ID**: T008
> **Task 명**: 오디오 처리 코어 모듈 구현 (AudioRecorder)
> **관련 문서**: 07B-02 (Sec 4.2), T007 완료
> **예상 소요**: 2 hours

---

## Step 1: 목표 이해 ✅

### 1.1 Task 목표

- 마이크 권한 획득 및 오디오 스트림 캡처.
- `MediaRecorder`로 250ms 간격의 바이너리 청크 생성.
- `AudioContext`로 실시간 볼륨 레벨 계산.

### 1.2 성공 기준

- [ ] `AudioRecorder` 클래스 구현 완료.
- [ ] `start()` 호출 시 데이터 콜백이 주기적으로 실행됨.
- [ ] `getVolume()` 호출 시 0~100 사이 값 반환.

---

## Step 2: 테스트 작성 (TDD) 🧪

*브라우저 API는 Mocking이 필수입니다.*

```typescript
// src/lib/audio/__tests__/AudioRecorder.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AudioRecorder } from '../AudioRecorder';

describe('AudioRecorder', () => {
  let recorder: AudioRecorder;

  beforeEach(() => {
    // Mock MediaRecorder and AudioContext
    global.MediaRecorder = vi.fn().mockImplementation(() => ({
      start: vi.fn(),
      stop: vi.fn(),
      ondataavailable: null,
    }));
    recorder = new AudioRecorder();
  });

  it('should start recording', async () => {
    const onData = vi.fn();
    await recorder.start(onData);
    expect(onData).not.toHaveBeenCalled(); // Should be called when data available
  });
});
```

## Step 3: 구현 (Implementation) 🔨

### 3.1 인터페이스 정의 (Inline Spec)

*`src/lib/audio/AudioRecorder.ts`*

```TypeScript
export class AudioRecorder {
  private mediaRecorder: MediaRecorder | null = null;
  private audioContext: AudioContext | null = null;
  private analyser: AnalyserNode | null = null;
  private stream: MediaStream | null = null;

  /**
   * 녹음을 시작하고 데이터 청크를 콜백으로 전달합니다.
   * @param onData 바이너리 데이터(Blob/ArrayBuffer) 수신 콜백
   */
  async start(onData: (data: Blob) => void): Promise<void> {
    // 1. Get User Media (audio: true)
    // 2. Init AudioContext & Analyser for volume
    // 3. Init MediaRecorder with MIME type (webm/opus preferred)
    // 4. Set ondataavailable -> call onData
    // 5. mediaRecorder.start(250) // 250ms timeslice
  }

  /**
   * 녹음을 중지하고 스트림을 해제합니다.
   */
  stop(): void {
    // 1. mediaRecorder.stop()
    // 2. stream.getTracks().forEach(track => track.stop())
    // 3. audioContext.close()
  }

  /**
   * 현재 볼륨(0~100)을 반환합니다.
   */
  getVolume(): number {
    // Use AnalyserNode.getByteFrequencyData
    // Calculate RMS or Average -> Normalize to 0-100
    return 0;
  }
}
```

### 3.2 구현 가이드

- **MIME Type**: `MediaRecorder.isTypeSupported`로 `audio/webm;codecs=opus` 지원 여부 확인 후 사용.
- **Volume**: `getByteFrequencyData` 배열의 평균값을 사용하여 0~100으로 정규화.

------

## Step 4: 정적 검증 🔍

- [ ] `npm run lint`
- [ ] `npx tsc --noEmit`

------

## Step 5: 단위 테스트 실행 ✅

- [ ] `npm run test` 통과 확인.

------

## Step 6: 리팩토링 ✨

- [ ] 리소스 해제(Cleanup) 로직이 `stop()`에 누락되지 않았는지 확인.

------

## Step 7: 통합 확인 (Manual) 🔗

- `App.tsx`에 임시 버튼 추가하여 실제 마이크 동작(주소창 빨간 점) 및 콘솔 로그 확인.

------

## Step 8: 문서화 📝

- 메서드별 JSDoc 작성.

------

## Step 9: 커밋 ✅

```bash
git add src/lib/audio/
git commit -m "feat(audio): Implement AudioRecorder with volume analysis"
```

