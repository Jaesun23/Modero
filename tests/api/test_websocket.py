import pytest
from fastapi.testclient import TestClient
from core.security import get_current_user_ws, TokenPayload
from domain.services.audio_service import audio_service
import asyncio
import time

@pytest.mark.asyncio
async def test_websocket_audio_flow(app):
    # Dependency Override
    async def mock_get_current_user_ws():
        return TokenPayload(sub="ws_user", name="WS User", room_id="ws_room", exp=9999999999)

    app.dependency_overrides[get_current_user_ws] = mock_get_current_user_ws

    room_id = "ws_room"
    user_id = "ws_user"

    # Clean up before test
    if user_id in audio_service._queues:
        await audio_service.stop_stream(user_id)

    with TestClient(app) as client:
        with client.websocket_connect(f"/ws/audio/{room_id}") as websocket:
            # 1. Send Audio Data
            audio_data = b"\x00\x01\x02"
            websocket.send_bytes(audio_data)

            # 2. Verify Data in Service Queue
            # Poll for data arrival
            max_retries = 10
            found = False
            for _ in range(max_retries):
                if user_id in audio_service._queues:
                    queue = audio_service._queues[user_id]
                    if queue.qsize() > 0:
                        found = True
                        break
                await asyncio.sleep(0.05)
            
            assert found, f"Queue empty after wait. Active queues: {list(audio_service._queues.keys())}"
            
            queue = audio_service._queues[user_id]
            # Verify content if possible (peek or assuming order)
            # Since we can't easily await get() across threads/loops without issues sometimes, 
            # and we just want to verify ingestion works:
            assert queue.qsize() >= 1

    # 3. Disconnect happens on context exit
    await asyncio.sleep(0.1)
    
    # Verify cleanup
    assert user_id not in audio_service._queues