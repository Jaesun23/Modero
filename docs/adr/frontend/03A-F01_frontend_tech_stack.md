# ADR-F01: Frontend Tech Stack Selection

> Status: Accepted
> Date: 2025-12-10
> Deciders: User, Gemini
> Context: Real-time Audio Streaming Application

## Context
Modero는 실시간 오디오 처리 및 시각화가 필요한 애플리케이션입니다. 
따라서 빠른 렌더링 속도, 타입 안정성, 그리고 빈번한 상태 업데이트를 효율적으로 처리할 수 있는 기술 스택이 필요합니다.

## Decision
다음과 같은 프론트엔드 기술 스택을 채택합니다:

1. **Framework**: React + Vite + TypeScript
2. **State Management**: Zustand
3. **Styling**: Tailwind CSS
4. **Audio Processing**: Native MediaRecorder API

## Consequences
### Positive
- **Vite**: 빠른 HMR(Hot Module Replacement)로 개발 생산성 향상.
- **TypeScript**: 엄격한 타입 검사를 통해 WebSocket 메시지 구조의 정합성 보장.
- **Zustand**: Redux 대비 코드가 간결하며, WebSocket 이벤트 핸들러 외부에서도 상태 접근이 용이함 (Transient updates).
- **Tailwind CSS**: 클래스명 고민 없이 빠른 UI 프로토타이핑 및 일관된 디자인 적용 가능.
- **MediaRecorder**: 외부 라이브러리 없이 브라우저 표준 API를 사용하여 번들 사이즈 최소화.

### Negative
- **Browser Compatibility**: Safari 등 일부 브라우저에서 MediaRecorder의 MIME Type 지원 범위가 다를 수 있음 (필요 시 polyfill 고려).