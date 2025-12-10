# src/core/websocket/manager.py
from collections import defaultdict
from typing import Dict, List

from fastapi import WebSocket

from core.logging import get_logger, bind_context
from .schemas import WebSocketMessage

logger = get_logger(__name__)


class ConnectionManager:
    def __init__(self):
        # Room ID -> List[WebSocket] 매핑
        self.active_connections: Dict[str, List[WebSocket]] = defaultdict(list)

    async def connect(self, websocket: WebSocket, room_id: str, user_id: str):
        await websocket.accept()
        self.active_connections[room_id].append(websocket)

        # 로깅 컨텍스트에 연결 정보 추가
        bind_context(room_id=room_id, user_id=user_id)
        logger.info(
            "websocket_connected", total_in_room=len(self.active_connections[room_id])
        )

    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.active_connections:
            if websocket in self.active_connections[room_id]:
                self.active_connections[room_id].remove(websocket)
                logger.info(
                    "websocket_disconnected",
                    remaining=len(self.active_connections[room_id]),
                )

            # 방이 비었으면 메모리 정리
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    async def broadcast(self, message: WebSocketMessage, room_id: str):
        """같은 방에 있는 모든 사용자에게 메시지 전송"""
        if room_id not in self.active_connections:
            return

        # 직렬화는 한 번만 수행 (성능 최적화)
        json_msg = message.model_dump_json()

        # 연결 끊긴 소켓 자동 정리 리스트
        disconnected_sockets = []

        for connection in self.active_connections[room_id]:
            try:
                await connection.send_text(json_msg)
            except Exception as e:
                logger.warning("broadcast_failed", error=str(e))
                disconnected_sockets.append(connection)

        # 죽은 연결 정리
        for dead_ws in disconnected_sockets:
            self.disconnect(dead_ws, room_id)


# 싱글톤 인스턴스
manager = ConnectionManager()
