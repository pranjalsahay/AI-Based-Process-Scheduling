"""Pydantic schemas for chat interactions and structured LLM responses."""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class TutoringMode(str, Enum):
    """Pedagogical tutoring modes required by SchedulAI."""
    DIAGNOSTIC = "diagnostic"
    SOCRATIC = "socratic"
    EXPLANATION = "explanation"
    GUIDED_PRACTICE = "guided_practice"
    INDEPENDENT_PRACTICE = "independent_practice"
    REVISION = "revision"


class TutorAction(str, Enum):
    """Action executed by the tutor in the current turn."""
    CHAT = "chat"
    ASK_QUESTION = "ask_question"
    PROVIDE_HINT = "provide_hint"
    EXPLAIN_CONCEPT = "explain_concept"
    EVALUATE_ANSWER = "evaluate_answer"
    PRESENT_PROBLEM = "present_problem"
    VERIFY_RESULT = "verify_result"
    SUMMARIZE_REVISION = "summarize_revision"


class TutorStructuredResponse(BaseModel):
    """
    Structured output contract produced by the LLM and validated by the backend.
    """
    message: str = Field(..., description="Text shown to the learner")
    mode: TutoringMode = Field(..., description="Current tutoring mode")
    topic: str = Field(..., description="Operating systems topic (e.g. FCFS, SJF, SRTF, Round Robin)")
    action: TutorAction = Field(..., description="Pedagogical action taken in this turn")
    question: Optional[str] = Field(None, description="The next single question, if any")
    hint: Optional[str] = Field(None, description="Pedagogical hint guiding the student")
    misconception: Optional[str] = Field(None, description="Identified misconception, if any")
    concepts_demonstrated: List[str] = Field(default_factory=list, description="List of concepts student showed mastery of")
    concepts_needing_review: List[str] = Field(default_factory=list, description="List of concepts student struggled with")
    source_ids: List[str] = Field(default_factory=list, description="Referenced chunk IDs from the knowledge base")
    requires_calculation: bool = Field(default=False, description="Whether this question involves numerical scheduling calculations")
    gantt_chart_ascii: Optional[str] = Field(None, description="Optional text Gantt chart if relevant")


class ChatRequest(BaseModel):
    """Student incoming chat message."""
    session_id: Optional[str] = Field(None, description="Existing session UUID, or None to create a new session")
    message: str = Field(..., min_length=1, max_length=4000, description="Student's message text")
    topic: Optional[str] = Field(None, description="Explicit topic change requested by student")
    mode_override: Optional[TutoringMode] = Field(None, description="Explicit mode override if selected by student")


class ChatResponse(BaseModel):
    """Complete backend response sent to frontend UI."""
    session_id: str
    message: str
    mode: TutoringMode
    topic: str
    action: TutorAction
    question: Optional[str] = None
    hint: Optional[str] = None
    misconception: Optional[str] = None
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    gantt_chart_ascii: Optional[str] = None
    concepts_demonstrated: List[str] = Field(default_factory=list)
    concepts_needing_review: List[str] = Field(default_factory=list)
    difficulty_level: str = "beginner"
    is_fallback: bool = False
