"""Independent test suite verifying conversation memory, context construction, and session persistence."""

import pytest
from app.database.connection import get_db, SessionLocal
from app.database.repository import DatabaseRepository, init_db
from app.database.models import SessionModel, MessageModel, LearnerStateModel
from app.core.conversation_memory import ConversationMemoryManager
from app.core.learner_model import LearnerModelManager
from app.schemas.chat import TutoringMode, TutorAction, TutorStructuredResponse


@pytest.fixture(autouse=True)
def setup_database():
    init_db()
    yield


def test_session_isolation():
    """Verify that different sessions maintain completely isolated messages and state."""
    db = SessionLocal()
    try:
        repo = DatabaseRepository(db)
        s1 = repo.create_session(title="Session 1", topic="FCFS")
        s2 = repo.create_session(title="Session 2", topic="Round Robin")

        repo.add_message(s1.session_id, role="user", content="Hello in session 1")
        repo.add_message(s2.session_id, role="user", content="Hello in session 2")

        msgs1 = repo.get_messages(s1.session_id)
        msgs2 = repo.get_messages(s2.session_id)

        assert len(msgs1) == 1
        assert len(msgs2) == 1
        assert msgs1[0].content == "Hello in session 1"
        assert msgs2[0].content == "Hello in session 2"
        assert s1.session_id != s2.session_id
    finally:
        db.close()


def test_message_persistence_across_reloads():
    """Verify conversations survive database disconnections / simulated restarts."""
    db1 = SessionLocal()
    try:
        repo1 = DatabaseRepository(db1)
        s = repo1.create_session(title="Persistence Session", topic="Fundamentals")
        sid = s.session_id

        repo1.add_message(sid, role="user", content="What is a process?")
        repo1.add_message(sid, role="assistant", content="A process is an active program in execution.")
    finally:
        db1.close()

    # Re-open fresh DB session (simulating backend restart or refresh)
    db2 = SessionLocal()
    try:
        repo2 = DatabaseRepository(db2)
        loaded = repo2.get_session(sid)
        assert loaded is not None
        messages = repo2.get_messages(sid)
        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[1].role == "assistant"
        assert "active program" in messages[1].content
    finally:
        db2.close()


def test_topic_switching_and_return():
    """Verify that switching topics preserves prior progress and returns to it cleanly."""
    state = LearnerStateModel(
        session_id="test_switch",
        current_topic="FCFS",
        current_mode="socratic",
        lesson_stage="guided_practice",
        difficulty_level="intermediate"
    )
    state.concepts_understood = ["fcfs_fifo_order"]
    state.recent_misconceptions = ["confused arrival with burst"]

    # Switch to Round Robin
    LearnerModelManager.handle_topic_switch(state, "Round Robin")
    assert state.current_topic == "Round Robin"
    assert state.lesson_stage == "knowledge_assessment"
    assert "time_quantum_selection" in state.concepts_not_assessed

    # Switch back to FCFS
    LearnerModelManager.handle_topic_switch(state, "FCFS")
    assert state.current_topic == "FCFS"
    assert state.lesson_stage == "guided_practice"
    assert "fcfs_fifo_order" in state.concepts_understood
    assert "confused arrival with burst" in state.recent_misconceptions
    assert state.difficulty_level == "intermediate"


def test_summarization_preserves_critical_details():
    """Verify that conversation summarization preserves weaknesses, examples, and answers."""
    messages = [
        MessageModel(session_id="s1", role="user", content="My main weakness is calculating average turnaround time."),
        MessageModel(session_id="s1", role="assistant", content="We will focus on turnaround time. Here is an example with P1 burst 4 and P2 burst 3."),
        MessageModel(session_id="s1", role="user", content="Under FCFS, arrival order determines priority."),
        MessageModel(session_id="s1", role="assistant", content="Spot on! Arrival time is the sole determinant.")
    ]

    state = LearnerStateModel(
        session_id="s1",
        current_topic="FCFS",
        current_mode="socratic",
        lesson_stage="guided_inquiry"
    )
    state.concepts_understood = ["fcfs_fifo_order"]

    summary = ConversationMemoryManager.build_or_update_summary("", messages, state)
    assert "turnaround time" in summary.lower()
    assert "fcfs" in summary.lower()
    assert "weakness" in summary.lower()


def test_prompt_assembly_includes_summary_and_window():
    """Verify that prompt assembly packages system prompt, summary, and recent messages."""
    summary = "### Session Conversation Summary:\n- Student weakness: turnaround time calculations."
    recent = [
        {"role": "user", "content": "What is turnaround time?"},
        {"role": "assistant", "content": "Turnaround time is Completion Time minus Arrival Time."}
    ]
    latest_msg = "Can we calculate P2's turnaround time?"

    payload = ConversationMemoryManager.assemble_prompt_messages(
        system_prompt="You are SchedulAI.",
        conversation_summary=summary,
        recent_messages=recent,
        latest_user_message=latest_msg,
        tutoring_state_dict={"current_topic": "Metrics", "lesson_stage": "guided_practice"}
    )

    # Check payload structure: unified single system prompt + recent messages + latest user message
    assert len(payload) == 4
    assert payload[0]["role"] == "system"
    assert "STRUCTURED TUTORING STATE" in payload[0]["content"]
    assert "EARLIER CONVERSATION SUMMARY" in payload[0]["content"]
    assert "turnaround time calculations" in payload[0]["content"]
    assert payload[1]["role"] == "user"
    assert payload[1]["content"] == "What is turnaround time?"
    assert payload[2]["role"] == "assistant"
    assert payload[3]["role"] == "user"
    assert payload[3]["content"] == latest_msg
