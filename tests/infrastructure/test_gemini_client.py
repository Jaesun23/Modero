import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from infrastructure.external.gemini_client import GeminiClient

# DNA 원칙: Mock을 활용하여 외부 비용/의존성 제거 및 빠른 피드백 확보


@pytest.mark.asyncio
async def test_generate_insight_success():
    """
    Scenario: Gemini가 유효한 JSON 문자열을 반환했을 때 Dict로 잘 변환되는지 확인
    """
    # Given
    mock_model = MagicMock()
    
    # generate_content_async는 비동기 메서드이므로 AsyncMock으로 설정
    mock_async_method = AsyncMock()
    mock_model.generate_content_async = mock_async_method
    
    # 응답 객체 (await 결과)
    mock_response_obj = MagicMock()
    expected_json = {
        "type": "SUMMARY",
        "content": "참여자 A가 프로젝트 일정을 논의했습니다.",
    }
    mock_response_obj.text = json.dumps(expected_json)
    
    mock_async_method.return_value = mock_response_obj

    # When
    # 테스트용으로 주입된 mock_model을 사용하는 클라이언트 생성
    client = GeminiClient(model=mock_model)
    result = await client.generate_insight("회의 발언 내용입니다.")

    # Then
    assert result == expected_json
    assert result["type"] == "SUMMARY"
    # generate_content_async가 호출되었는지 확인
    mock_async_method.assert_called_once()


@pytest.mark.asyncio
async def test_generate_insight_api_error():
    """
    Scenario: Gemini API 호출 중 예외가 발생했을 때 적절한 에러 응답을 반환하는지 확인
    """
    # Given
    mock_model = MagicMock()
    # API 호출 시 예외 발생 설정
    mock_async_method = AsyncMock()
    mock_model.generate_content_async = mock_async_method
    mock_async_method.side_effect = Exception("API Error")

    # When
    client = GeminiClient(model=mock_model)
    result = await client.generate_insight("발언 내용")

    # Then
    # 에러 발생 시 프로그램이 죽지 않고 에러 타입의 Dict를 반환해야 함 (Fail-safe)
    assert result["type"] == "ERROR"
    assert "Analysis failed" in result["content"]


@pytest.mark.asyncio
async def test_generate_insight_invalid_json():
    """
    Scenario: Gemini가 JSON이 아닌 문자열을 반환했을 때 처리 확인
    """
    # Given
    mock_model = MagicMock()
    
    mock_async_method = AsyncMock()
    mock_model.generate_content_async = mock_async_method
    
    mock_response_obj = MagicMock()
    mock_response_obj.text = "This is not JSON"  # 잘못된 응답
    mock_async_method.return_value = mock_response_obj

    # When
    client = GeminiClient(model=mock_model)
    result = await client.generate_insight("발언 내용")

    # Then
    assert result["type"] == "ERROR"
    assert "JSON parsing failed" in result["content"]