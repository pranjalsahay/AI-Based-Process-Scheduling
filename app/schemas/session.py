"""Session schemas for FastAPI endpoints."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from app.schemas.chat import TutoringMode


class SessionCreate(BaseModel):
    title: Optional[str] = Field("New Learning Session", description="Session title")
    topic: Optional[str] = Field("Fundamentals", description="Starting OS topic")


class SessionSummary(BaseModel):
    session_id: str
    title: str
    topic: str
    created_at: datetime
    updated_at: datetime
    is_active: bool
    message_count: int = 0


class MessageItem(BaseModel):
    id: int
    role: str
    content: str
    mode: str
    timestamp: datetime
    structured_json: Optional[str] = None


class SessionDetail(BaseModel):
    session_id: str
    title: str
    topic: str
    created_at: datetime
    updated_at: datetime
    is_active: bool
    messages: List[MessageItem] = []
