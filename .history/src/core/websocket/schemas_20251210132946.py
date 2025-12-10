# src/core/websocket/schemas.py
from typing import Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class WebSocketMessage(BaseModel):
    type: Literal["chat", "stt_result", "ai_response", "system"]
    payload: Any
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
