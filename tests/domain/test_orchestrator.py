import pytest
from unittest.mock import AsyncMock, MagicMock
from domain.services.meeting_orchestrator import MeetingOrchestrator

@pytest.mark.asyncio
async def test_orchestrator_flow():
    # Mocks
    audio_service = AsyncMock()
    
    stt_client = MagicMock()
    
    gemini_client = AsyncMock()
    manager = AsyncMock()
    
    # STT가 1개의 결과를 주는 상황 모킹
    async def stt_gen(stream):
        yield {"text": "hello", "is_final": True}
        
    stt_client.transcribe.side_effect = stt_gen
    
    orch = MeetingOrchestrator(audio_service, stt_client, gemini_client, manager)
    await orch.start_processing("user1", "room1")
    
    # Assertions
    gemini_client.generate_insight.assert_called_once() # Final이라 호출되어야 함
    assert manager.broadcast.call_count >= 1