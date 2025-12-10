# 05D-02_frontend_dna_implementation

> **프로젝트**: Modero (Frontend)
> **작성일**: 2025-12-10
> **목적**: 프론트엔드 핵심 인프라(DNA System) 구현 명세
> **적용**: `src/lib/` 디렉토리

---

## 1. 디렉토리 구조

```text
src/
├── lib/
│   ├── logger.ts       # [DNA 2] Observability
│   ├── env.ts          # [DNA 6] Configuration
│   ├── error.ts        # [DNA 7] Error Handling
│   └── http.ts         # [DNA 9] API System
```

## 2. 구현 상세 (Copy & Paste Ready)

### 2.1 Observability System (Logger)

**파일**: `src/lib/logger.ts`
**목적**: 개발 환경에서는 콘솔 출력, 운영 환경에서는 불필요한 로그 제거 또는 Sentry 전송.

```typescript
const isDev = import.meta.env.DEV;

export const logger = {
  debug: (msg: string, ...args: unknown[]) => {
    if (isDev) console.debug(`🐛 [DEBUG] ${msg}`, ...args);
  },
  info: (msg: string, ...args: unknown[]) => {
    if (isDev) console.info(`ℹ️ [INFO] ${msg}`, ...args);
  },
  warn: (msg: string, ...args: unknown[]) => {
    console.warn(`⚠️ [WARN] ${msg}`, ...args);
  },
  error: (msg: string, error?: unknown) => {
    console.error(`🚨 [ERROR] ${msg}`, error);
    // TODO: Production 환경일 경우 Sentry 등으로 에러 전송 로직 추가
  },
};
```

### 2.2 Configuration System (Env)

파일: src/lib/env.ts

목적: 필수 환경변수 누락 시 앱 실행 즉시 중단(Fail-fast) 및 타입 안전성 보장.

의존성: npm install zod

```TypeScript
import { z } from 'zod';

const envSchema = z.object({
  // Vite 환경변수는 VITE_ 접두사 필수
  VITE_API_URL: z.string().url(),
  VITE_SOCKET_URL: z.string().url(),
  MODE: z.enum(['development', 'production', 'test']),
});

// import.meta.env를 검증
const _env = envSchema.safeParse(import.meta.env);

if (!_env.success) {
  console.error('❌ Invalid environment variables:', _env.error.format());
  throw new Error('Invalid environment variables');
}

export const env = _env.data;
```

### 2.3 Error Handling System

파일: src/lib/error.ts

목적: 애플리케이션 전반에서 사용할 표준 에러 클래스 정의.

```TypeScript
export class AppError extends Error {
  public readonly code: string;
  public readonly isOperational: boolean;

  constructor(message: string, code: string = 'UNKNOWN_ERROR', isOperational = true) {
    super(message);
    this.name = this.constructor.name;
    this.code = code;
    this.isOperational = isOperational; // 예측 가능한 에러 여부
    Error.captureStackTrace(this, this.constructor);
  }
}

export class ApiError extends AppError {
  constructor(message: string, public statusCode: number) {
    super(message, 'API_ERROR');
  }
}
```

### 2.4 API System (HTTP Client)

파일: src/lib/http.ts

목적: Axios 인스턴스를 중앙화하여 인터셉터 및 공통 설정을 관리.

의존성: npm install axios

```typescript
import axios from 'axios';
import { env } from './env';
import { logger } from './logger';

export const http = axios.create({
  baseURL: env.VITE_API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // 10초 타임아웃
});

// Request Interceptor
http.interceptors.request.use(
  (config) => {
    // 예: 토큰 자동 주입 로직
    // const token = sessionStorage.getItem('token');
    // if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor
http.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.message || error.message;
    logger.error(`API Error: ${message}`, error);
    return Promise.reject(error);
  }
);
```

