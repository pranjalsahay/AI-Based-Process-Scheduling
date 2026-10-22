"""Database repository for CRUD operations on sessions, messages, and learner states."""

import uuid
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from sqlalchemy import text
from app.database.connection import engine, Base
from app.database.models import SessionModel, MessageModel, LearnerStateModel, PracticeAttemptModel


def init_db():
    """Initializes database tables and safely migrates new columns if they do not exist."""
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        try:
            res = conn.execute(text("PRAGMA table_info(learner_states)")).fetchall()
            existing_cols = {row[1] for row in res}
            new_cols = [
                ("lesson_stage", "VARCHAR(32) DEFAULT 'knowledge_assessment'"),
                ("concepts_partially_understood_json", "TEXT DEFAULT '[]'"),
                ("concepts_not_assessed_json", "TEXT DEFAULT '[]'"),
                ("last_question_asked", "TEXT"),
                ("pending_question", "TEXT"),
                ("current_subtopic", "VARCHAR(64)"),
                ("last_concept_explained", "VARCHAR(128)"),
                ("next_teaching_step", "VARCHAR(128)"),
                ("conversation_summary", "TEXT DEFAULT ''"),
                ("topic_progress_json", "TEXT DEFAULT '{}'"),
                ("quiz_state_json", "TEXT DEFAULT '{}'")
            ]
            for col_name, col_def in new_cols:
                if col_name not in existing_cols:
                    conn.execute(text(f"ALTER TABLE learner_states ADD COLUMN {col_name} {col_def}"))
            conn.commit()
        except Exception as e:
            pass


class DatabaseRepository:
    """Encapsulates data access methods for SchedulAI."""

    def __init__(self, db: Session):
        self.db = db

    def create_session(
        self,
        session_id: Optional[str] = None,
        title: str = "New Learning Session",
        topic: str = "Fundamentals"
    ) -> SessionModel:
        sid = session_id or str(uuid.uuid4())
        session_obj = SessionModel(
            session_id=sid,
            title=title,
            topic=topic,
            is_active=True
        )
        self.db.add(session_obj)

        # Create accompanying learner state
        learner_state = LearnerStateModel(
            session_id=sid,
            current_topic=topic,
            current_mode="diagnostic",
            difficulty_level="beginner"
        )
        self.db.add(learner_state)
        self.db.commit()
        self.db.refresh(session_obj)
        return session_obj

    def get_session(self, session_id: str) -> Optional[SessionModel]:
        return self.db.query(SessionModel).filter(SessionModel.session_id == session_id).first()

    def list_sessions(self) -> List[SessionModel]:
        return self.db.query(SessionModel).order_by(SessionModel.updated_at.desc()).all()

    def delete_session(self, session_id: str) -> bool:
        session_obj = self.get_session(session_id)
        if session_obj:
            self.db.delete(session_obj)
            self.db.commit()
            return True
        return False

    def reset_session(self, session_id: str) -> Optional[SessionModel]:
        session_obj = self.get_session(session_id)
        if not session_obj:
            return None

        # Delete messages and reset learner state
        self.db.query(MessageModel).filter(MessageModel.session_id == session_id).delete()
        learner_state = self.get_or_create_learner_state(session_id)
        learner_state.current_mode = "diagnostic"
        learner_state.difficulty_level = "beginner"
        learner_state.concepts_understood = []
        learner_state.concepts_needing_review = []
        learner_state.recent_misconceptions = []
        learner_state.pending_question = None
        learner_state.last_question_asked = None
        learner_state.current_subtopic = None
        learner_state.last_concept_explained = None
        learner_state.next_teaching_step = None
        learner_state.quiz_state_json = "{}"
        learner_state.questions_attempted = 0
        learner_state.correct_answers = 0
        learner_state.partial_answers = 0
        learner_state.incorrect_answers = 0
        learner_state.hints_used = 0
        learner_state.numerical_score = 0.0
        learner_state.last_reviewed = datetime.utcnow()

        session_obj.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(session_obj)
        return session_obj

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        mode: str = "socratic",
        structured_json: Optional[str] = None
    ) -> MessageModel:
        msg = MessageModel(
            session_id=session_id,
            role=role,
            content=content,
            mode=mode,
            structured_json=structured_json
        )
        self.db.add(msg)
        
        # Touch session updated_at
        session_obj = self.get_session(session_id)
        if session_obj:
            session_obj.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(msg)
        return msg

    def get_messages(self, session_id: str, limit: Optional[int] = None) -> List[MessageModel]:
        q = (
            self.db.query(MessageModel)
            .filter(MessageModel.session_id == session_id)
            .order_by(MessageModel.timestamp.asc())
        )
        if limit:
            q = q.limit(limit)
        return q.all()

    def get_or_create_learner_state(self, session_id: str) -> LearnerStateModel:
        state = self.db.query(LearnerStateModel).filter(LearnerStateModel.session_id == session_id).first()
        if not state:
            state = LearnerStateModel(
                session_id=session_id,
                current_topic="Fundamentals",
                current_mode="diagnostic",
                difficulty_level="beginner"
            )
            self.db.add(state)
            self.db.commit()
            self.db.refresh(state)
        return state

    def record_practice_attempt(
        self,
        session_id: str,
        topic: str,
        student_answer: str,
        is_correct: bool,
        algorithm: Optional[str] = None,
        verified_answer_json: Optional[str] = None,
        feedback: Optional[str] = None
    ) -> PracticeAttemptModel:
        attempt = PracticeAttemptModel(
            session_id=session_id,
            topic=topic,
            algorithm=algorithm,
            student_answer=student_answer,
            verified_answer_json=verified_answer_json,
            is_correct=is_correct,
            feedback=feedback
        )
        self.db.add(attempt)
        self.db.commit()
        self.db.refresh(attempt)
        return attempt
