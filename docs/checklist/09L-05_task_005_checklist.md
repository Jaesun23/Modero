# 09L-05_task_005_checklist

> Task ID: T005
>
> Task 명: Gemini 실시간 인사이트 서비스 구현
>
> 예상 소요: 3 hours
>
> 관련 문서: 03A-002 (ADR: Gemini), 07B-01 (Section 2.1)

------

## Step 1: 목표 이해 (Goal Understanding) ✅

### 1.1 Task 목표

- 확정된(Final) 발언 텍스트를 Gemini 1.5 Flash에 전송하여 분석한다.
- 회의 맥락에 맞는 인사이트(요약, 경고, 제안)를 **JSON 포맷**으로 생성한다.

### 1.2 입력 (Inputs)

- **Config**: `GEMINI_API_KEY` (`core.config`)
- **Model**: `gemini-1.5-flash` (속도 최적화)
- **Input**: 사용자 발언 텍스트 (STT 결과)

### 1.3 성공 기준 (Acceptance Criteria)

- [ ] Gemini API 호출이 `async_generate_content`를 사용하여 비동기로 처리되어야 함.
- [ ] 응답 포맷이 반드시 JSON이어야 하며, 파싱 실패 시 재시도하거나 에러 처리해야 함.
- [ ] 프롬프트에 시스템 페르소나("공정한 중재자")가 포함되어야 함.

------

## Step 2: 테스트 작성 (Test First) 🧪

### 2.1 테스트 시나리오

1. **JSON 응답 파싱**: Gemini가 준 JSON 문자열을 파이썬 Dict/Model로 변환하는지 테스트.
2. **프롬프트 생성**: 입력 텍스트가 프롬프트 템플릿에 올바르게 삽입되는지 확인.
3. **API 호출 모킹**: `generate_content_async` 호출 시 Mock 응답을 반환하고, 서비스가 이를 잘 처리하는지 확인.

### 2.2 테스트 파일 생성

- 파일: `tests/infrastructure/test_gemini_client.py`
- 코드 스켈레톤:

Python

```
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.infrastructure.external.gemini_client import GeminiClient

@pytest.mark.asyncio
async def test_generate_insight_returns_json():
    # Mock Gemini Response
    mock_model = MagicMock()
    mock_response = AsyncMock()
    mock_response.text = '{"type": "SUMMARY", "content": "테스트 요약"}'
    mock_model.generate_content_async.return_value = mock_response
    
    client = GeminiClient(model=mock_model)
    result = await client.generate_insight("회의 내용입니다.")
    
    assert result["type"] == "SUMMARY"
    assert result["content"] == "테스트 요약"
```

------

## Step 3: 구현 (Implementation) 🔨

### 3.1 구현 위치

- `src/infrastructure/external/gemini_client.py`
- `src/domain/services/insight_service.py`

### 3.2 구현 힌트 (GeminiClient)

Python

```
import json
import google.generativeai as genai
from core.config import get_settings
from core.logging import get_logger

logger = get_logger(__name__)

class GeminiClient:
    def __init__(self, model=None):
        settings = get_settings()
        if not model:
            genai.configure(api_key=settings.gemini_api_key.get_secret_value())
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = model

    async def generate_insight(self, text: str) -> dict:
        prompt = f"""
        Analyze the following meeting transcript and provide insight in JSON format.
        Schema: {{ "type": "SUMMARY" | "WARNING" | "SUGGESTION", "content": "string" }}
        Transcript: {text}
        """
        try:
            response = await self.model.generate_content_async(
                prompt, 
                generation_config={"response_mime_type": "application/json"}
            )
            return json.loads(response.text)
        except Exception as e:
            logger.error("gemini_error", error=str(e))
            return {"type": "ERROR", "content": "Analysis failed"}
```

### 3.3 프로젝트 표준 준수

- **의존성**: `google-generativeai` 라이브러리 추가.
- **Logging**: 에러 발생 시 `structlog`로 로깅.

------

## Step 4: 정적 검증 (Static Analysis) 🔍

### 4.1 Linting & Formatting

Bash

```
ruff check src/infrastructure/external/gemini_client.py --fix
ruff format src/infrastructure/external/gemini_client.py
```

### 4.2 Type Checking

Bash

```
mypy src/infrastructure/external/gemini_client.py
```

------

## Step 5: 단위 테스트 실행 (Run Tests) ✅

### 5.1 테스트 실행

Bash

```
pytest tests/infrastructure/test_gemini_client.py -v
```

### 5.2 커버리지 확인

Bash

```
pytest --cov=src/infrastructure/external/gemini_client.py tests/infrastructure/test_gemini_client.py
```

------

## Step 6: 리팩토링 (Refactor) 🔄

- [ ] 프롬프트 텍스트를 별도 상수(`PROMPTS.py`)로 분리하여 관리.
- [ ] JSON 파싱 실패(`json.JSONDecodeError`)에 대한 명시적 예외 처리 추가.

------

## Step 7: 통합 테스트 (Integration Test) 🔗

- [ ] API Key가 설정된 로컬 환경에서 실제 Gemini 호출 테스트 (1회 수행 후 비용 절감 위해 Skip 처리 권장).

------

## Step 8: 문서화 (Documentation) 📝

- [ ] `generate_insight` 메서드의 입출력 형식 및 에러 상황 Docstring 작성.

------

## Step 9: 커밋 (Commit) ✅

### 9.1 Pre-commit 재확인

- [ ] Lint, Test 통과 확인.

### 9.2 Git Commit

Bash

```
git add src/infrastructure/external/gemini_client.py tests/infrastructure/test_gemini_client.py pyproject.toml
git commit -m "feat(infra): Implement Gemini async client with JSON enforcement"
```

------

