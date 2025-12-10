import pytest
from core.security import create_access_token, verify_token
from core.websocket.schemas import WebSocketMessage
from core.websocket.manager import ConnectionManager

@pytest.mark.asyncio
async def test_jwt_generation_and_validation():
    """JWT 토큰 생성 및 검증 테스트"""
    user_id = "test_user_id"
    payload_data = {"sub": user_id, "name": "Test User", "room_id": "test_room"}
    token = create_access_token(payload_data)
    
    decoded_payload = verify_token(token)
    assert decoded_payload.sub == user_id

@pytest.mark.asyncio
async def test_connection_manager():
    """Connection Manager의 연결/해제/브로드캐스트 로직 테스트 (Mock 사용)"""
    manager = ConnectionManager()

    # Mock WebSocket (AsyncMock 필요, 여기서는 개념적으로 설명)
    class MockWebSocket:
        def __init__(self):
            self.sent_data = None
            self.accepted = False

        async def accept(self):
            self.accepted = True

        async def send_json(self, data): # send_json 메서드 추가
            self.sent_data = data

        async def close(self, code: int = 1000):
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
    # manager.broadcast는 pydantic 모델이 아닌 dict를 받으므로 model_dump 사용
    await manager.broadcast(msg.model_dump(mode="json"), room_id)

    # Check if sent (실제 환경에서는 json string 확인)
    assert ws1.sent_data == msg.model_dump(mode="json")
    assert ws2.sent_data == msg.model_dump(mode="json")

    # Disconnect
    manager.disconnect(room_id, "user1")
    assert len(manager.active_connections[room_id]) == 1
    manager.disconnect(room_id, "user2")
    assert room_id not in manager.active_connections # 방이 비었으면 방 자체가 삭제되어야 함