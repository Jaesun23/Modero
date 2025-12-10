# 06S-02_frontend_standards

> **프로젝트**: Modero (Frontend)
> **적용**: React, TypeScript, Tailwind CSS
> **강제 수단**: ESLint, Prettier, TypeScript Compiler

---

## 1. 코딩 규칙 (Coding Rules)

### 1.1 DNA 시스템 사용 (DO & DON'T)

| 시스템      | DO (권장) ✅                                                  | DON'T (금지) ❌                           |
| :---------- | :----------------------------------------------------------- | :--------------------------------------- |
| **Logging** | `import { logger } from '@/lib/logger'`<br>`logger.info(...)` | `console.log(...)` (ESLint 차단)         |
| **Config**  | `import { env } from '@/lib/env'`<br>`env.VITE_API_URL`      | `import.meta.env.VITE_...` 직접 사용     |
| **API**     | `import { http } from '@/lib/http'`                          | `fetch`, `axios.get` 직접 사용           |
| **Error**   | `throw new AppError(...)`                                    | `throw new Error(...)`, `throw "string"` |

### 1.2 컴포넌트 작성 (React)

- **함수형 컴포넌트**: `const Component = () => {}` 형식을 사용한다.
- **Props 타입**: 반드시 `interface`로 정의하고 컴포넌트 바로 위에 위치시킨다.
- **Export**: `Named Export`를 기본으로 한다. (`export const Component ...`)
- **Hook 규칙**: 최상위 레벨에서만 호출하며, 조건문/반복문 내부에서 호출 금지.

### 1.3 스타일링 (Tailwind CSS)

- **유틸리티 우선**: 별도의 `.css` 파일을 만들지 않고 Tailwind 클래스로 해결한다.
- **조건부 스타일**: `clsx` 또는 `tailwind-merge` 라이브러리를 사용한다.
  ```tsx
  // ✅ DO
  <div className={cn("p-4", isActive && "bg-blue-500")} />
  
  // ❌ DON'T
  <div className={"p-4 " + (isActive ? "bg-blue-500" : "")} />

## 2. 파일 및 네이밍 (Naming Convention)

### 2.1 파일명

- **컴포넌트**: `PascalCase.tsx` (예: `MeetingCard.tsx`)
- **Hooks**: `camelCase.ts` (예: `useSocket.ts`)
- **유틸리티/함수**: `camelCase.ts` (예: `formatDate.ts`)

### 2.2 변수 및 함수

- **상수**: `UPPER_SNAKE_CASE` (예: `MAX_RETRY_COUNT`)
- **Boolean**: `is`, `has`, `should` 접두사 사용 (예: `isLoading`, `hasError`)
- **Event Handler**: `handle` + 동사 + 명사 (예: `handleSubmit`, `handleClick`)
- **Props Event**: `on` + 동사 (예: `onClick`, `onSubmit`)

------

## 3. 품질 기준 (Quality Gates)

### 3.1 Zero Tolerance (타협 불가)

커밋 전 다음 항목은 **반드시 0건**이어야 한다.

1. **Lint Errors**: `npm run lint` 실행 시 Error 0건.
2. **Type Errors**: `npx tsc --noEmit` 실행 시 Error 0건.
3. **Unused Code**: 사용하지 않는 변수, Import는 제거.

### 3.2 테스트 커버리지

- **Unit Test**: 유틸리티 함수(`src/lib`), 복잡한 로직 Hooks는 테스트 필수.
- **UI Test**: 핵심 컴포넌트는 렌더링 테스트 필수.

------

## 4. 디렉토리 구조 (Architecture Enforcement)

```
src/
├── api/          # API 요청 함수 모음 (http.ts 사용)
├── components/   # UI 컴포넌트
│   ├── ui/       # 공통/재사용 컴포넌트 (Button, Input)
│   └── feature/  # 도메인 특화 컴포넌트
├── hooks/        # 커스텀 훅
├── lib/          # DNA 시스템 구현체 (절대 수정 주의)
├── pages/        # 라우트 페이지
├── store/        # 전역 상태 (Zustand)
└── types/        # 공통 타입 정의
```