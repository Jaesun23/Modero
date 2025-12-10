# src/core/security/jwt.py
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt
from fastapi import WebSocket, Query, status
from pydantic import BaseModel

from core.config import get_settings
from core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class TokenPayload(BaseModel):
    sub: str  # User ID
    name: str  # User Name (Display)
    room_id: str  # Chat Room ID
    exp: int


def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=1)  # 기본 1시간

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_secret_key.get_secret_value(), algorithm="HS256"
    )
    return encoded_jwt


def verify_token(token: str) -> TokenPayload:
    """토큰을 검증하고 페이로드를 반환합니다."""
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key.get_secret_value(), algorithms=["HS256"]
        )
        return TokenPayload(**payload)
    except jwt.ExpiredSignatureError:
        logger.warning("token_expired")
        raise ValueError("Token expired")
    except jwt.PyJWTError as e:
        logger.warning("token_invalid", error=str(e))
        raise ValueError("Invalid token")


async def get_current_user_ws(
    websocket: WebSocket, token: str = Query(...)
) -> TokenPayload:
    """WebSocket 연결 시 Query Param으로 토큰을 검증합니다."""
    try:
        payload = verify_token(token)
        return payload
    except ValueError:
        # 연결 전 거부 (403)
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise
