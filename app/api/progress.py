"""API router for querying learner proficiency and progress metrics."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.repository import DatabaseRepository
from app.schemas.learner import LearnerProgressResponse
from app.schemas.chat import TutoringMode
from app.core.learner_model import LearnerModelManager

router = APIRouter(prefix="/api/progress", tags=["progress"])


@router.get("/{session_id}", response_model=LearnerProgressResponse)
def get_learner_progress(session_id: str, db: Session = Depends(get_db)):
    """Retrieves quantified learner mastery and progress for a session."""
    repo = DatabaseRepository(db)
    session_obj = repo.get_session(session_id)
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")

    state = repo.get_or_create_learner_state(session_id)
    metrics = LearnerModelManager.calculate_metrics(state)

    mode_val = TutoringMode(state.current_mode) if state.current_mode in TutoringMode._value2member_map_ else TutoringMode.SOCRATIC

    return LearnerProgressResponse(
        session_id=session_id,
        current_topic=state.current_topic or "Fundamentals",
        current_mode=mode_val,
        difficulty_level=state.difficulty_level or "beginner",
        concepts_understood=state.concepts_understood,
        concepts_needing_review=state.concepts_needing_review,
        recent_misconceptions=state.recent_misconceptions,
        questions_attempted=state.questions_attempted or 0,
        correct_answers=state.correct_answers or 0,
        partial_answers=state.partial_answers or 0,
        incorrect_answers=state.incorrect_answers or 0,
        hints_used=state.hints_used or 0,
        accuracy_percentage=metrics["accuracy_percentage"],
        mastery_score=metrics["mastery_score"],
        last_reviewed=state.last_reviewed
    )
