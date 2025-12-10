import pytest
from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

from core.security import create_access_token, verify_token
from core.websocket import ConnectionManager, WebSocketMessage


def test_jwt_generation_and_validation():
    """JWT 생성 및 검증 테스트"""
    data = {"sub": "user123", "name": "Tester", "room_id": "room1"}
    token = create_access_token(data)

    payload = verify_token(token)
    assert payload.sub == "user123"
    assert payload.room_id == "room1"


@pytest.mark.asyncio
async def test_connection_manager():
    """Connection Manager의 연결/해제/브로드캐스트 로직 테스트 (Mock 사용)"""
    manager = ConnectionManager()

    # Mock WebSocket (AsyncMock 필요, 여기서는 개념적으로 설명)
    class MockWebSocket:
        async def accept(self):
            pass

        async def send_text(self, data):
            self.sent_data = data

        async def close(self):
            pass

    ws1 = MockWebSocket()
    ws2 = MockWebSocket()
    room_id = "test_room"

    # Connect
    await manager.connect(ws1, room_id, "user1")
    await manager.connect(ws2, room_id, "user2")
    assert len(manager.active_connections[room_id]) == 2

    # Broadcast
    msg = WebSocketMessage(type="chat", payload={"text": "hello"})
    await manager.broadcast(msg, room_id)

    # Check if sent (실제 환경에서는 json string 확인)
    assert ws1.sent_data is not None
    assert ws2.sent_data is not None

    # Disconnect
    manager.disconnect(ws1, room_id)
    assert len(manager.active_connections[room_id]) == 1
