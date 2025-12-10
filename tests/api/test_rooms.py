import pytest
import uuid
from httpx import AsyncClient
from unittest.mock import AsyncMock
from fastapi import WebSocket
from core.websocket.manager import manager

# Mock DB Session fixture가 conftest.py에 있다고 가정


@pytest.mark.asyncio
async def test_create_room(client: AsyncClient, db_session):
    """회의실 생성 API 테스트"""
    payload = {"title": "Test Meeting Room"}

    # 인증 헤더가 필요하다면 추가 (여기서는 생략하거나 Mock 처리 가정)
    response = await client.post("/api/v1/rooms", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == payload["title"]
    assert "id" in data
    # UUID 형식 확인
    assert uuid.UUID(data["id"])


@pytest.mark.asyncio
async def test_get_room(client: AsyncClient, db_session):
    """회의실 조회 API 테스트"""
    # 1. 생성
    create_resp = await client.post("/api/v1/rooms", json={"title": "Get Test"})
    room_id = create_resp.json()["id"]

    # 2. 조회
    response = await client.get(f"/api/v1/rooms/{room_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == room_id
    assert data["title"] == "Get Test"
    assert data["is_active"] is True

@pytest.mark.asyncio
async def test_room_creation_and_websocket_connection(client: AsyncClient, db_session):
    """Integration: Create Room -> Connect WebSocket (via Manager)"""
    # 1. Create Room via API
    create_resp = await client.post("/api/v1/rooms", json={"title": "Integration Room"})
    assert create_resp.status_code == 201
    room_id = create_resp.json()["id"]

    # 2. Simulate WebSocket Connection
    mock_ws = AsyncMock(spec=WebSocket)
    user_id = "test_user_integration"
    
    await manager.connect(mock_ws, room_id, user_id)
    
    # 3. Verify
    assert room_id in manager.active_connections
    assert user_id in manager.active_connections[room_id]