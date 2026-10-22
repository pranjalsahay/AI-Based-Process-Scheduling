"""Schemas for learner progress, mastery, and difficulty reporting."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from app.schemas.chat import TutoringMode


class LearnerProgressResponse(BaseModel):
    session_id: str
    current_topic: str
    current_mode: TutoringMode
    difficulty_level: str  # beginner, intermediate, advanced
    concepts_understood: List[str]
    concepts_needing_review: List[str]
    recent_misconceptions: List[str]
    questions_attempted: int
    correct_answers: int
    partial_answers: int
    incorrect_answers: int
    hints_used: int
    accuracy_percentage: float
    mastery_score: float  # 0.0 - 100.0%
    last_reviewed: datetime
