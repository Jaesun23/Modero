import pytest
import uuid
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock
from fastapi import WebSocket
import asyncio

from core.security import get_current_user_ws, TokenPayload
from api.dependencies import (
    get_audio_service,
    get_stt_client,
    get_gemini_client,
    get_connection_manager,
    get_meeting_orchestrator,
)
from domain.services.audio_service import AudioService
from infrastructure.external.google_stt import GoogleSTTClient
from infrastructure.external.gemini_client import GeminiClient
from core.websocket.manager import ConnectionManager
from domain.services.meeting_orchestrator import MeetingOrchestrator # ADDED
from fastapi.testclient import TestClient # For websocket_connect

@pytest.mark.asyncio
async def test_e2e_websocket_pipeline_flow(app, mocker):
    """
    E2E 테스트: WebSocket을 통해 오디오 데이터를 보내고 STT/Gemini 결과가
    정상적으로 브로드캐스트되는지 확인합니다.
    """
    # --- Setup Mocks and Overrides ---
    mock_audio_service = mocker.MagicMock(spec=AudioService)
    mock_stt_client = mocker.MagicMock(spec=GoogleSTTClient)
    mock_gemini_client = mocker.MagicMock(spec=GeminiClient)
    mock_manager = mocker.MagicMock(spec=ConnectionManager)

    # AudioService.get_audio_stream을 모킹하여 오케스트레이터가 소비할 스트림을 제어
    async def mock_audio_stream_for_orchestrator():
        # 오케스트레이터에게 전달될 가상의 오디오 청크
        yield b"simulated_audio_chunk_for_orchestrator"
        yield None # 오케스트레이터의 스트림 종료 신호
    mock_audio_service.get_audio_stream.return_value = mock_audio_stream_for_orchestrator()

    # Mock STT transcribe to yield one final result
    async def mock_stt_transcribe_generator(audio_stream):
        async for chunk in audio_stream:
            if chunk is None:
                break
            # 첫 번째 청크 이후에 Final STT 결과 yield
            yield {"text": "hello final", "is_final": True, "type": "final"}
            break # Consume one chunk and then return final, for simple test

    mock_stt_client.transcribe.side_effect = mock_stt_transcribe_generator

    # Mock Gemini generate_insight
    mock_gemini_client.generate_insight.return_value = {
        "type": "SUMMARY", "content": "mocked insight"
    }

    # Override dependencies
    app.dependency_overrides[get_audio_service] = lambda: mock_audio_service
    app.dependency_overrides[get_stt_client] = lambda: mock_stt_client
    app.dependency_overrides[get_gemini_client] = lambda: mock_gemini_client
    app.dependency_overrides[get_connection_manager] = lambda: mock_manager
    app.dependency_overrides[get_meeting_orchestrator] = lambda: MeetingOrchestrator(
        audio_service=mock_audio_service,
        stt_client=mock_stt_client,
        gemini_client=mock_gemini_client,
        manager=mock_manager,
    )


    # Mock get_current_user_ws for authentication
    async def mock_get_current_user_ws():
        return TokenPayload(sub="test_user_e2e", name="E2E User", room_id="test_room_e2e", exp=9999999999)
    app.dependency_overrides[get_current_user_ws] = mock_get_current_user_ws

    room_id = "test_room_e2e"
    user_id = "test_user_e2e"
    
    # --- Test Flow ---
    with TestClient(app) as client:
        with client.websocket_connect(f"/ws/audio/{room_id}?token=fake_token") as websocket:
            # 1. Simulate sending audio data
            # 이 데이터는 websocket_endpoint를 통해 mock_audio_service.push_audio로 전달됨
            audio_data_from_client = b"client_audio_chunk"
            websocket.send_bytes(audio_data_from_client)

            # 오케스트레이터가 오디오를 소비하고, STT, Gemini 처리 후 브로드캐스트할 시간을 줌
            await asyncio.sleep(0.5) # 충분한 시간 부여 (STT, Gemini 모킹 지연 고려)

            # 2. Verify audio service received push from endpoint
            mock_audio_service.push_audio.assert_called_once_with(user_id, audio_data_from_client)
            
            # 3. Verify audio_service.get_audio_stream was called by orchestrator
            mock_audio_service.get_audio_stream.assert_called_once_with(user_id)
            
            # 4. Verify STT client transcribe was called
            mock_stt_client.transcribe.assert_called_once()
            
            # 5. Verify Gemini client was called (because STT result was final)
            mock_gemini_client.generate_insight.assert_called_once_with("hello final")

            # 6. Verify manager broadcast was called for STT and Gemini results
            # Note: broadcast is called twice, once for STT, once for Gemini
            assert mock_manager.broadcast.call_count == 2
            
            # Additional assertions for broadcast content
            # (requires exact dict match, can be complex with timestamp)
            # You can check call args if needed.
            
            # Ensure orchestrator task is done (stream finished)
            # The process_task will be cancelled on WebSocketDisconnect or finish when stream ends.
            # Here it should finish as audio_stream_for_orchestrator yields None.
            
    # --- Cleanup ---
    # Dependency overrides should be automatically cleaned up by pytest,
    # but explicit cleanup ensures isolation.
    app.dependency_overrides = {}
