"""API router for managing learning sessions."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.repository import DatabaseRepository
from app.schemas.session import SessionCreate, SessionSummary, SessionDetail, MessageItem

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("", response_model=SessionSummary, status_code=status.HTTP_201_CREATED)
def create_session(data: SessionCreate, db: Session = Depends(get_db)):
    """Creates a new learning session."""
    repo = DatabaseRepository(db)
    session_obj = repo.create_session(title=data.title or "New Learning Session", topic=data.topic or "Fundamentals")
    return SessionSummary(
        session_id=session_obj.session_id,
        title=session_obj.title,
        topic=session_obj.topic,
        created_at=session_obj.created_at,
        updated_at=session_obj.updated_at,
        is_active=session_obj.is_active,
        message_count=0
    )


@router.get("", response_model=List[SessionSummary])
def list_sessions(db: Session = Depends(get_db)):
    """Lists all stored learning sessions."""
    repo = DatabaseRepository(db)
    sessions = repo.list_sessions()
    return [
        SessionSummary(
            session_id=s.session_id,
            title=s.title,
            topic=s.topic,
            created_at=s.created_at,
            updated_at=s.updated_at,
            is_active=s.is_active,
            message_count=len(s.messages)
        )
        for s in sessions
    ]


@router.get("/{session_id}", response_model=SessionDetail)
def get_session(session_id: str, db: Session = Depends(get_db)):
    """Retrieves session details and chronological message history."""
    repo = DatabaseRepository(db)
    session_obj = repo.get_session(session_id)
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = [
        MessageItem(
            id=m.id,
            role=m.role,
            content=m.content,
            mode=m.mode or "socratic",
            timestamp=m.timestamp,
            structured_json=m.structured_json
        )
        for m in session_obj.messages
    ]

    return SessionDetail(
        session_id=session_obj.session_id,
        title=session_obj.title,
        topic=session_obj.topic,
        created_at=session_obj.created_at,
        updated_at=session_obj.updated_at,
        is_active=session_obj.is_active,
        messages=messages
    )


@router.delete("/{session_id}", status_code=status.HTTP_200_OK)
def delete_session(session_id: str, db: Session = Depends(get_db)):
    """Deletes a learning session and associated records."""
    repo = DatabaseRepository(db)
    success = repo.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Session deleted successfully", "session_id": session_id}


@router.post("/{session_id}/reset", status_code=status.HTTP_200_OK)
def reset_session(session_id: str, db: Session = Depends(get_db)):
    """Resets conversation messages and restarts learner state for the current session."""
    repo = DatabaseRepository(db)
    session_obj = repo.reset_session(session_id)
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Session reset successfully", "session_id": session_id}
