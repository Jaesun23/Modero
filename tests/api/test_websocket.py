import pytest
from fastapi.testclient import TestClient
from core.security import get_current_user_ws, TokenPayload
from domain.services.audio_service import audio_service # 실제 서비스 인스턴스 사용
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

# GoogleSTTClient와 GeminiClient 클래스를 Mocking하기 위해 import
from infrastructure.external.google_stt import GoogleSTTClient
from infrastructure.external.gemini_client import GeminiClient


@pytest.mark.asyncio
async def test_websocket_audio_flow(app, monkeypatch, mocker):
    # Dependency Override
    async def mock_get_current_user_ws():
        return TokenPayload(sub="ws_user", name="WS User", room_id="ws_room", exp=9999999999)

    app.dependency_overrides[get_current_user_ws] = mock_get_current_user_ws

    room_id = "ws_room"
    user_id = "ws_user"

    # --- Start Mocking GoogleSTTClient and GeminiClient ---
    mock_stt_instance = MagicMock(spec=GoogleSTTClient)
    mock_gemini_instance = AsyncMock(spec=GeminiClient)

    async def mock_stt_transcribe_gen(audio_stream):
        # CRITICAL: 스트림을 전부 소비하면 무한루프 발생!
        # 실제 STT처럼 첫 chunk만 소비하고 즉시 결과 반환
        try:
            _ = await audio_stream.__anext__()  # noqa: F841
        except StopAsyncIteration:
            pass
        yield {"text": "mocked stt", "is_final": True, "type": "final"}
    mock_stt_instance.transcribe.side_effect = mock_stt_transcribe_gen

    mock_gemini_instance.generate_insight.return_value = {
        "type": "SUMMARY", "content": "mocked gemini insight"
    }

    # 클래스를 Mock으로 대체 (인스턴스 생성 시 Mock 인스턴스가 반환되도록)
    monkeypatch.setattr("api.routes.websocket.GoogleSTTClient", MagicMock(return_value=mock_stt_instance))
    monkeypatch.setattr("api.routes.websocket.GeminiClient", MagicMock(return_value=mock_gemini_instance))
    # --- End Mocking ---


    # Clean up audio_service before test to ensure isolation
    if user_id in audio_service._queues:
        await audio_service.stop_stream(user_id)

    with TestClient(app) as client:
        with client.websocket_connect(f"/ws/audio/{room_id}?token=dummy_token") as websocket:
            # 1. Send Audio Data
            audio_data = b"\x00\x01\x02"
            websocket.send_bytes(audio_data)

            # 2. Verify Data in Service Queue (push_audio)
            # websocket_endpoint가 audio_service.push_audio를 호출할 시간을 줌
            await asyncio.sleep(0.1) # 짧은 지연

            # 오케스트레이터가 STT를 호출하고, STT가 audio_stream을 소비할 것임.
            # E2E 테스트에서 오케스트레이터는 audio_service.get_audio_stream을 통해 실제 큐를 사용.
            # 따라서 audio_service의 큐가 비워져 있어야 함.
            assert audio_service._queues[user_id].qsize() == 0

            # 3. STT 결과 수신 대기 (mock_stt_transcribe_gen이 반환한 결과)
            stt_result = websocket.receive_json()
            assert stt_result["type"] == "stt_result"
            assert stt_result["payload"]["text"] == "mocked stt"

            # 4. Gemini 결과 수신 대기 (mock_gemini_instance.generate_insight가 반환한 결과)
            gemini_result = websocket.receive_json()
            assert gemini_result["type"] == "ai_response"
            assert gemini_result["payload"]["content"] == "mocked gemini insight"

    # 5. Disconnect and Cleanup
    await asyncio.sleep(0.1) # Give time for disconnect handler to run
    assert user_id not in audio_service._queues # Verify cleanup