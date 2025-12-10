import pytest
import uuid
from httpx import AsyncClient
from unittest.mock import AsyncMock
from fastapi import WebSocket
from core.websocket.manager import manager
from core.security import get_current_user, TokenPayload
from domain.models import User

@pytest.mark.asyncio
async def test_create_room(client: AsyncClient, db_session, app):
    """회의실 생성 API 테스트"""
    # 1. Create a user in DB
    user_id = uuid.uuid4()
    user = User(
        id=user_id, 
        email="test@example.com", 
        nickname="tester", 
        password_hash="hash"
    )
    db_session.add(user)
    await db_session.commit()

    # 2. Override Auth Dependency
    async def mock_get_current_user():
        return TokenPayload(sub=str(user_id), name="tester", exp=9999999999)
    
    app.dependency_overrides[get_current_user] = mock_get_current_user

    payload = {"title": "Test Meeting Room"}

    # 3. Call API
    response = await client.post("/api/v1/rooms", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == payload["title"]
    assert "id" in data
    assert uuid.UUID(data["id"])
    
    # Clean up override
    app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_get_room(client: AsyncClient, db_session, app):
    """회의실 조회 API 테스트"""
    # 1. Setup User & Auth
    user_id = uuid.uuid4()
    user = User(id=user_id, email="get@example.com", nickname="getter", password_hash="hash")
    db_session.add(user)
    await db_session.commit()

    async def mock_get_current_user():
        return TokenPayload(sub=str(user_id), name="getter", exp=9999999999)
    app.dependency_overrides[get_current_user] = mock_get_current_user

    # 2. Create Room
    create_resp = await client.post("/api/v1/rooms", json={"title": "Get Test"})
    room_id = create_resp.json()["id"]

    # 3. Get Room
    response = await client.get(f"/api/v1/rooms/{room_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == room_id
    assert data["title"] == "Get Test"
    
    app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_room_creation_and_websocket_connection(client: AsyncClient, db_session, app):
    """Integration: Create Room -> Connect WebSocket (via Manager)"""
    # 1. Setup Auth
    user_id = uuid.uuid4()
    user = User(id=user_id, email="int@example.com", nickname="int", password_hash="hash")
    db_session.add(user)
    await db_session.commit()

    async def mock_get_current_user():
        return TokenPayload(sub=str(user_id), name="int", exp=9999999999)
    app.dependency_overrides[get_current_user] = mock_get_current_user

    # 2. Create Room
    create_resp = await client.post("/api/v1/rooms", json={"title": "Integration Room"})
    assert create_resp.status_code == 201
    room_id = create_resp.json()["id"]

    # 3. Simulate WebSocket Connection
    mock_ws = AsyncMock(spec=WebSocket)
    
    await manager.connect(mock_ws, room_id, str(user_id))
    
    # 4. Verify
    assert room_id in manager.active_connections
    assert str(user_id) in manager.active_connections[room_id]
    
    app.dependency_overrides = {}
