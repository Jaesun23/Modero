import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class CreateRoomRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="회의실 제목")


class RoomResponse(BaseModel):
    id: uuid.UUID
    title: str
    host_id: uuid.UUID
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True  # ORM 모드 (Pydantic v2)
