from collections import defaultdict
from typing import Dict, Any
from fastapi import WebSocket
from core.logging import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    def __init__(self):
        # 구조: {room_id: {user_id: WebSocket}}
        # 딕셔너리를 사용하여 특정 사용자 연결에 O(1)로 접근 가능
        self.active_connections: Dict[str, Dict[str, WebSocket]] = defaultdict(dict)

    async def connect(self, websocket: WebSocket, room_id: str, user_id: str):
        await websocket.accept()
        # 해당 방의 사용자 목록에 웹소켓 추가 (중복 접속 시 덮어쓰기 처리됨)
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

            # 방에 아무도 없으면 방 키 삭제 (메모리 누수 방지)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    async def send_personal_message(
        self, message: Dict[str, Any], room_id: str, user_id: str
    ):
        """[DNA Fix] 특정 사용자에게만 메시지를 전송합니다 (시스템 알림 등)."""
        if (
            room_id in self.active_connections
            and user_id in self.active_connections[room_id]
        ):
            websocket = self.active_connections[room_id][user_id]
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(
                    "personal_message_failed",
                    room_id=room_id,
                    user_id=user_id,
                    error=str(e),
                )
                # 전송 실패 시 연결이 끊긴 것으로 간주할 수도 있으나,
                # 여기서는 disconnect를 명시적으로 호출하지 않고 예외만 로깅

    async def broadcast(self, message: Dict[str, Any], room_id: str):
        """특정 방에 있는 모든 사용자에게 메시지 전송"""
        if room_id not in self.active_connections:
            return

        # 방 안의 모든 연결에 대해 전송
        # 연결 끊김 에러 처리는 호출하는 쪽이나 별도 루프에서 처리 (Step 6 리팩토링 대상)
        # 딕셔너리 변경 안전을 위해 리스트 복사본으로 순회
        active_users = list(self.active_connections[room_id].items())

        for user_id, connection in active_users:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(
                    "broadcast_failed", room_id=room_id, user_id=user_id, error=str(e)
                )
                self.disconnect(room_id, user_id)


# 싱글톤 인스턴스
manager = ConnectionManager()
