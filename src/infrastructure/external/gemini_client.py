import json
import google.generativeai as genai
from typing import Optional, Dict, Any

from core.config import get_settings
from core.logging import get_logger
from core.prompts import SYSTEM_MODERATOR_PROMPT

logger = get_logger(__name__)
settings = get_settings()


class GeminiClient:
    """
    Google Gemini AI와의 통신을 담당하는 비동기 클라이언트
    """

    def __init__(self, model: Optional[Any] = None):
        """
        초기화 시 API Key를 설정하고 모델을 로드합니다.
        테스트를 위해 외부에서 model 객체를 주입받을 수 있습니다.
        """
        if model:
            self.model = model
        else:
            # 실제 운영 환경 설정
            genai.configure(api_key=settings.gemini_api_key.get_secret_value())
            self.model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                # JSON 포맷 강제 설정 (Gemini 1.5 기능)
                generation_config={"response_mime_type": "application/json"},
            )

        # 시스템 페르소나 및 프롬프트 템플릿 정의
        self.system_prompt = SYSTEM_MODERATOR_PROMPT

    async def generate_insight(self, text: str) -> Dict[str, Any]:
        """
        사용자 발언을 분석하여 JSON 형태의 인사이트를 반환합니다.
        """
        prompt = f"{self.system_prompt}\n{text}"
        response_text = "" # for error logging context

        try:
            # 비동기 추론 호출
            response = await self.model.generate_content_async(prompt)

            # 응답 텍스트 추출 및 JSON 파싱
            response_text = response.text
            insight_data = json.loads(response_text)

            # 성공 로그
            logger.info(
                "gemini_insight_generated",
                type=insight_data.get("type"),
                content_preview=insight_data.get("content")[:20],
            )

            return insight_data

        except json.JSONDecodeError as e:
            logger.error(
                "gemini_json_error", error=str(e), response_text=response_text
            )
            return {"type": "ERROR", "content": "JSON parsing failed"}

        except Exception as e:
            logger.error("gemini_api_error", error=str(e))
            return {"type": "ERROR", "content": "Analysis failed"}