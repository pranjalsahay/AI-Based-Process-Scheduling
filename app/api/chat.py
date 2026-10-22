"""API router for conversational turns and tutoring interactions."""

import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.repository import DatabaseRepository
from app.schemas.chat import ChatRequest, ChatResponse, TutoringMode
from app.core.tutoring_engine import TutoringEngine

router = APIRouter(prefix="/api/chat", tags=["chat"])
tutoring_engine = TutoringEngine()


@router.post("", response_model=ChatResponse)
async def chat_turn(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Main tutoring endpoint handling the student-tutor conversational interaction.
    """
    repo = DatabaseRepository(db)

    # 1. Resolve or create session
    session_id = request.session_id
    if not session_id:
        session_obj = repo.create_session(
            title=request.message[:40] if len(request.message) > 5 else "Learning Session",
            topic=request.topic or "Fundamentals"
        )
        session_id = session_obj.session_id
    else:
        session_obj = repo.get_session(session_id)
        if not session_obj:
            session_obj = repo.create_session(
                session_id=session_id,
                title=request.message[:40],
                topic=request.topic or "Fundamentals"
            )

    # Update session topic if explicitly provided
    if request.topic:
        session_obj.topic = request.topic
        db.commit()

    # 2. Retrieve history and learner state
    history = repo.get_messages(session_id, limit=100)
    learner_state = repo.get_or_create_learner_state(session_id)

    # Record user's incoming message
    repo.add_message(
        session_id=session_id,
        role="user",
        content=request.message,
        mode=learner_state.current_mode or "socratic"
    )

    # 3. Execute tutoring cycle
    try:
        response: ChatResponse = await tutoring_engine.generate_tutor_turn(
            session_id=session_id,
            user_message=request.message,
            history=history,
            learner_state=learner_state,
            topic_override=request.topic,
            mode_override=request.mode_override
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        # Fallback safeguard in case of unexpected exceptions
        response = ChatResponse(
            session_id=session_id,
            message="I encountered an unexpected issue while generating the response. Let's refocus: what specific scheduling question or calculation would you like to review?",
            mode=TutoringMode.SOCRATIC,
            topic=learner_state.current_topic or "Fundamentals",
            action="ask_question",
            question="Which scheduling topic or algorithm would you like to work on right now?",
            sources=[],
            is_fallback=True
        )

    # 4. Save tutor assistant message and persist learner state
    repo.add_message(
        session_id=session_id,
        role="assistant",
        content=response.message,
        mode=response.mode.value if hasattr(response.mode, "value") else str(response.mode),
        structured_json=response.model_dump_json()
    )

    db.add(learner_state)
    db.commit()
    db.refresh(learner_state)
    return response
