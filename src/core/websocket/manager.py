from collections import defaultdict
from typing import Dict, Any
from fastapi import WebSocket
from core.logging import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    def __init__(self):
        # 구조: {room_id: {user_id: WebSocket}}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = defaultdict(dict)

    async def connect(self, websocket: WebSocket, room_id: str, user_id: str):
        await websocket.accept()
        self.active_connections[room_id][user_id] = websocket
        logger.info(
            "websocket_connected",
            room_id=room_id,
            user_id=user_id,
            total_users=len(self.active_connections[room_id]),
        )

    def disconnect(self, room_id: str, user_id: str):
        if room_id in self.active_connections:
            if user_id in self.active_connections[room_id]:
                del self.active_connections[room_id][user_id]
                logger.info("websocket_disconnected", room_id=room_id, user_id=user_id)

            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    async def send_personal_message(
        self, message: Dict[str, Any], room_id: str, user_id: str
    ):
        """[DNA Fix] 특정 사용자에게 메시지 전송"""
        if (
            room_id in self.active_connections
            and user_id in self.active_connections[room_id]
        ):
            try:
                websocket = self.active_connections[room_id][user_id]
                await websocket.send_json(message)
            except Exception as e:
                logger.error("personal_message_failed", error=str(e), user_id=user_id)

    async def broadcast(self, message: Dict[str, Any], room_id: str):
        """방 내 모든 사용자에게 브로드캐스트"""
        if room_id not in self.active_connections:
            return

        active_users = list(self.active_connections[room_id].items())

        for user_id, connection in active_users:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error("broadcast_failed", error=str(e), user_id=user_id)
                self.disconnect(room_id, user_id)

    async def disconnect_room(self, room_id: str):
        """
        [DNA Fix] CRITICAL-001: 특정 방의 모든 연결을 강제로 종료합니다.
        회의가 종료되었을 때 호출됩니다.
        """
        if room_id not in self.active_connections:
            return

        # 시스템 메시지 전송
        close_msg = {
            "type": "system",
            "payload": {"event": "meeting_closed", "message": "Meeting closed by host"},
        }
        await self.broadcast(close_msg, room_id)

        # 소켓 연결 해제
        active_users = list(self.active_connections[room_id].items())
        for user_id, connection in active_users:
            try:
                await connection.close(code=1000)
            except Exception:
                pass  # 이미 닫힌 경우 무시
            finally:
                self.disconnect(room_id, user_id)

        logger.info("room_connections_closed", room_id=room_id)


manager = ConnectionManager()
