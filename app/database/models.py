"""SQLAlchemy database models for SchedulAI."""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database.connection import Base


class SessionModel(Base):
    """Represents a conversation/learning session."""
    __tablename__ = "sessions"

    session_id = Column(String(64), primary_key=True, index=True)
    title = Column(String(255), default="New Learning Session")
    topic = Column(String(64), default="Fundamentals")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    messages = relationship("MessageModel", back_populates="session", cascade="all, delete-orphan", order_by="MessageModel.timestamp")
    learner_state = relationship("LearnerStateModel", back_populates="session", uselist=False, cascade="all, delete-orphan")
    practice_attempts = relationship("PracticeAttemptModel", back_populates="session", cascade="all, delete-orphan")


class MessageModel(Base):
    """Represents a single chat message turn."""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), ForeignKey("sessions.session_id"), nullable=False, index=True)
    role = Column(String(16), nullable=False)  # "user", "assistant", "system"
    content = Column(Text, nullable=False)
    mode = Column(String(32), default="socratic")
    structured_json = Column(Text, nullable=True)  # Serialized TutorStructuredResponse
    timestamp = Column(DateTime, default=datetime.utcnow)

    session = relationship("SessionModel", back_populates="messages")


class LearnerStateModel(Base):
    """Persistent model tracking student's knowledge state, lesson stage, and difficulty."""
    __tablename__ = "learner_states"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), ForeignKey("sessions.session_id"), unique=True, nullable=False, index=True)
    current_topic = Column(String(64), default="Fundamentals")
    current_mode = Column(String(32), default="socratic")
    lesson_stage = Column(String(32), default="knowledge_assessment")  # knowledge_assessment, guided_inquiry, explanation, guided_practice, independent_practice, review
    difficulty_level = Column(String(16), default="beginner")  # beginner, intermediate, advanced

    concepts_understood_json = Column(Text, default="[]")
    concepts_partially_understood_json = Column(Text, default="[]")
    concepts_not_assessed_json = Column(Text, default="[]")
    concepts_needing_review_json = Column(Text, default="[]")
    recent_misconceptions_json = Column(Text, default="[]")

    last_question_asked = Column(Text, nullable=True)
    pending_question = Column(Text, nullable=True)
    current_subtopic = Column(String(64), nullable=True)
    last_concept_explained = Column(String(128), nullable=True)
    next_teaching_step = Column(String(128), nullable=True)
    conversation_summary = Column(Text, default="")
    topic_progress_json = Column(Text, default="{}")
    quiz_state_json = Column(Text, default="{}")

    questions_attempted = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    partial_answers = Column(Integer, default=0)
    incorrect_answers = Column(Integer, default=0)
    hints_used = Column(Integer, default=0)
    numerical_score = Column(Float, default=0.0)

    last_reviewed = Column(DateTime, default=datetime.utcnow)

    session = relationship("SessionModel", back_populates="learner_state")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.questions_attempted is None:
            self.questions_attempted = 0
        if self.correct_answers is None:
            self.correct_answers = 0
        if self.partial_answers is None:
            self.partial_answers = 0
        if self.incorrect_answers is None:
            self.incorrect_answers = 0
        if self.hints_used is None:
            self.hints_used = 0
        if self.numerical_score is None:
            self.numerical_score = 0.0
        if not self.lesson_stage:
            self.lesson_stage = "knowledge_assessment"
        if not self.conversation_summary:
            self.conversation_summary = ""

    # Helper getters/setters for JSON fields
    @property
    def concepts_understood(self) -> List[str]:
        try:
            return json.loads(self.concepts_understood_json or "[]")
        except Exception:
            return []

    @concepts_understood.setter
    def concepts_understood(self, val: List[str]):
        self.concepts_understood_json = json.dumps(val or [])

    @property
    def concepts_partially_understood(self) -> List[str]:
        try:
            return json.loads(self.concepts_partially_understood_json or "[]")
        except Exception:
            return []

    @concepts_partially_understood.setter
    def concepts_partially_understood(self, val: List[str]):
        self.concepts_partially_understood_json = json.dumps(val or [])

    @property
    def concepts_not_assessed(self) -> List[str]:
        try:
            return json.loads(self.concepts_not_assessed_json or "[]")
        except Exception:
            return []

    @concepts_not_assessed.setter
    def concepts_not_assessed(self, val: List[str]):
        self.concepts_not_assessed_json = json.dumps(val or [])

    @property
    def concepts_needing_review(self) -> List[str]:
        try:
            return json.loads(self.concepts_needing_review_json or "[]")
        except Exception:
            return []

    @concepts_needing_review.setter
    def concepts_needing_review(self, val: List[str]):
        self.concepts_needing_review_json = json.dumps(val or [])

    @property
    def recent_misconceptions(self) -> List[str]:
        try:
            return json.loads(self.recent_misconceptions_json or "[]")
        except Exception:
            return []

    @recent_misconceptions.setter
    def recent_misconceptions(self, val: List[str]):
        self.recent_misconceptions_json = json.dumps(val or [])

    @property
    def topic_progress(self) -> Dict[str, Any]:
        try:
            return json.loads(self.topic_progress_json or "{}")
        except Exception:
            return {}

    @topic_progress.setter
    def topic_progress(self, val: Dict[str, Any]):
        self.topic_progress_json = json.dumps(val or {})

    @property
    def quiz_state(self) -> Dict[str, Any]:
        try:
            return json.loads(self.quiz_state_json or "{}")
        except Exception:
            return {}

    @quiz_state.setter
    def quiz_state(self, val: Dict[str, Any]):
        self.quiz_state_json = json.dumps(val or {})

    def to_state_dict(self) -> Dict[str, Any]:
        """Returns the structured tutoring state dictionary defined in Section 3.3."""
        return {
            "current_topic": self.current_topic,
            "current_subtopic": self.current_subtopic,
            "current_mode": self.current_mode,
            "lesson_stage": self.lesson_stage or "knowledge_assessment",
            "concepts_understood": self.concepts_understood,
            "concepts_partially_understood": self.concepts_partially_understood,
            "concepts_not_assessed": self.concepts_not_assessed,
            "known_misconceptions": self.recent_misconceptions,
            "last_question_asked": self.last_question_asked,
            "pending_question": self.pending_question,
            "awaiting_answer": bool(self.pending_question and self.pending_question.strip()),
            "last_concept_explained": self.last_concept_explained,
            "next_teaching_step": self.next_teaching_step,
            "difficulty": self.difficulty_level or "beginner",
            "is_quiz_active": bool(self.quiz_state.get("is_active", False))
        }


class PracticeAttemptModel(Base):
    """Tracks numerical and conceptual practice attempts."""
    __tablename__ = "practice_attempts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), ForeignKey("sessions.session_id"), nullable=False, index=True)
    topic = Column(String(64), nullable=False)
    algorithm = Column(String(64), nullable=True)
    student_answer = Column(Text, nullable=False)
    verified_answer_json = Column(Text, nullable=True)
    is_correct = Column(Boolean, default=False)
    feedback = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    session = relationship("SessionModel", back_populates="practice_attempts")
