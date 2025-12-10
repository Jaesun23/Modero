import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi.testclient import TestClient
# from main import app # app fixture를 사용하므로 이 임포트는 필요 없습니다.

# 의존성 임포트 (src. 접두사 제거)
from infrastructure.external.google_stt import GoogleSTTClient
from infrastructure.external.gemini_client import GeminiClient
from core.security import get_current_user_ws, TokenPayload

# MeetingOrchestrator는 DI를 통해 주입되므로 여기서 직접 import 하지 않아도 됩니다.
# 하지만 테스트에서 인스턴스를 직접 생성하기 위해 import 해야 합니다.


@pytest.fixture
def mock_dependencies(monkeypatch):
    """
    Orchestrator가 사용하는 외부 의존성을 Mocking합니다.
    """
    # 1. Mock Google STT
    mock_stt = MagicMock(spec=GoogleSTTClient)
    
    async def stt_transcribe_gen(stream):
        # CRITICAL: 실제 STT 클라이언트는 스트림을 비동기적으로 소비하면서
        # 실시간으로 결과를 yield 합니다.
        # 스트림을 "전부 소비한 후"에 yield하면 안 됩니다!
        #
        # ❌ 잘못된 방법: async for _ in stream: pass  -> 무한루프 발생!
        # ✅ 올바른 방법: 첫 chunk만 소비하고 즉시 결과 반환
        try:
            chunk = await stream.__anext__() # noqa: F841
        except StopAsyncIteration: # 스트림이 비어있으면 이 예외 발생 가능
            pass # 오디오 스트림이 종료되었음을 의미
        
        # 1. Interim 결과 반환
        yield {
            "text": "테스트",
            "is_final": False,
            "language_code": "ko-KR",
            "type": "interim"
        }
        # 2. Final 결과 반환 (이때 Gemini가 호출되어야 함)
        yield {
            "text": "테스트 문장입니다.",
            "is_final": True,
            "language_code": "ko-KR",
            "type": "final"
        }
    
    mock_stt.transcribe.side_effect = stt_transcribe_gen
    
    # 2. Mock Gemini Client
    mock_gemini = AsyncMock(spec=GeminiClient)
    mock_gemini.generate_insight.return_value = {
        "type": "SUMMARY",
        "content": "이것은 테스트 요약입니다."
    }

    # 3. 의존성 주입 (Orchestrator가 내부적으로 생성하는 객체들을 가로채기 위해)
    # src.api.routes.websocket에서 GoogleSTTClient와 GeminiClient를 직접 임포트하므로
    # 해당 경로의 클래스들을 monkeypatch로 교체합니다.
    # 클래스 자체를 Mock으로 교체해야 인스턴스 생성 시 Mock이 반환됩니다.
    monkeypatch.setattr("api.routes.websocket.GoogleSTTClient", MagicMock(return_value=mock_stt))
    monkeypatch.setattr("api.routes.websocket.GeminiClient", MagicMock(return_value=mock_gemini))
    
    return mock_stt, mock_gemini

def test_websocket_e2e_flow(mock_dependencies, app): # app fixture 추가
    """
    WebSocket 연결 -> 오디오 전송 -> STT 결과 수신 -> Gemini 결과 수신
    전체 파이프라인을 검증합니다.
    """
    mock_stt, mock_gemini = mock_dependencies
    
    room_id = "test_room_e2e"
    
    # 토큰 검증 의존성 오버라이드
    app.dependency_overrides[get_current_user_ws] = lambda: TokenPayload(sub="test_user", name="Test User", exp=9999999999)

    with TestClient(app) as client:
        # token 파라미터를 넘겨주지 않으면 get_current_user_ws가 에러 발생.
        # dummy token이라도 넘겨줘야 함.
        with client.websocket_connect(f"/ws/audio/{room_id}?token=dummy_token") as websocket:
            # 1. 오디오 데이터 전송 (바이너리)
            # 이 데이터는 AudioService 큐로 들어가고 -> Orchestrator가 소비 -> Mock STT로 전달됨
            websocket.send_bytes(b"dummy_audio_data")
            
            # 2. STT Interim 결과 수신 대기
            data_1 = websocket.receive_json()
            assert data_1["type"] == "stt_result"
            assert data_1["payload"]["text"] == "테스트"
            assert data_1["payload"]["is_final"] is False
            
            # 3. STT Final 결과 수신 대기
            data_2 = websocket.receive_json()
            assert data_2["type"] == "stt_result"
            assert data_2["payload"]["text"] == "테스트 문장입니다."
            assert data_2["payload"]["is_final"] is True
            
            # 4. Gemini Insight 결과 수신 대기 (Final 이후 자동으로 트리거됨)
            data_3 = websocket.receive_json()
            assert data_3["type"] == "ai_response"
            assert data_3["payload"]["type"] == "SUMMARY"
            assert data_3["payload"]["content"] == "이것은 테스트 요약입니다."
            
            # 5. 연결 종료
            websocket.close()

    # 검증: Mock 객체들이 실제로 호출되었는지 확인
    assert mock_gemini.generate_insight.called
    assert mock_gemini.generate_insight.call_args[0][0] == "테스트 문장입니다."