import pytest
from unittest.mock import AsyncMock
from fastapi import WebSocket
from core.websocket.manager import ConnectionManager


@pytest.mark.asyncio
async def test_connect_and_disconnect():
    manager = ConnectionManager()
    websocket = AsyncMock(spec=WebSocket)
    room_id = "room_1"
    user_id = "user_1"

    # Connect
    await manager.connect(websocket, room_id, user_id)
    assert room_id in manager.active_connections
    assert user_id in manager.active_connections[room_id]
    assert manager.active_connections[room_id][user_id] == websocket

    # Disconnect
    manager.disconnect(room_id, user_id)
    
    # Verify room is gone (because it's empty)
    # Note: accessing manager.active_connections[room_id] would recreate it due to defaultdict
    assert room_id not in manager.active_connections


@pytest.mark.asyncio
async def test_broadcast_to_room_only():
    manager = ConnectionManager()

    # Room 1 Users
    ws_a = AsyncMock(spec=WebSocket)
    ws_b = AsyncMock(spec=WebSocket)

    # Room 2 User
    ws_c = AsyncMock(spec=WebSocket)

    # Setup Connections
    await manager.connect(ws_a, "room_1", "user_a")
    await manager.connect(ws_b, "room_1", "user_b")
    await manager.connect(ws_c, "room_2", "user_c")

    # Broadcast to Room 1
    message = {"type": "chat", "content": "Hello Room 1"}
    await manager.broadcast(message, "room_1")

    # Assertions
    # Room 1 인원은 메시지를 받아야 함
    ws_a.send_json.assert_called_with(message)
    ws_b.send_json.assert_called_with(message)

    # Room 2 인원은 메시지를 받지 말아야 함
    ws_c.send_json.assert_not_called()