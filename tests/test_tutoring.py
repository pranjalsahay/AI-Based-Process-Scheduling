"""Tests for tutoring behavior, mode switching, structured responses, and learner state."""

import pytest
from app.schemas.chat import (
    TutoringMode,
    TutorAction,
    TutorStructuredResponse
)
from app.core.response_parser import parse_and_validate_response, repair_common_json_flaws
from app.core.tutoring_engine import TutoringEngine
from app.core.learner_model import LearnerModelManager
from app.database.models import LearnerStateModel, MessageModel


def test_structured_response_validation():
    """Verify standard valid JSON parses correctly into TutorStructuredResponse."""
    raw = """
    {
      "message": "FCFS schedules processes in arrival order.",
      "mode": "socratic",
      "topic": "FCFS",
      "action": "ask_question",
      "question": "What happens if P1 has a burst of 100 and P2 has a burst of 1?",
      "hint": "Think about waiting time.",
      "misconception": null,
      "concepts_demonstrated": ["fcfs_concept"],
      "concepts_needing_review": [],
      "source_ids": ["01_fcfs_algorithm_p1_c0"],
      "requires_calculation": false
    }
    """
    obj, is_fallback = parse_and_validate_response(raw)
    assert not is_fallback
    assert obj.topic == "FCFS"
    assert obj.mode == TutoringMode.SOCRATIC
    assert obj.action == TutorAction.ASK_QUESTION
    assert "fcfs_concept" in obj.concepts_demonstrated


def test_trailing_comma_repair():
    """Verify JSON with trailing commas is repaired and parsed without errors."""
    raw_with_commas = """
    {
      "message": "Here is an explanation.",
      "mode": "explanation",
      "topic": "Round Robin",
      "action": "explain_concept",
      "question": null,
      "hint": null,
      "misconception": null,
      "concepts_demonstrated": ["rr_quantum",],
      "concepts_needing_review": [],
      "source_ids": [],
      "requires_calculation": false,
    }
    """
    obj, is_fallback = parse_and_validate_response(raw_with_commas)
    assert not is_fallback
    assert obj.mode == TutoringMode.EXPLANATION


def test_mode_intent_detection():
    """Verify that student explicit intents trigger the appropriate tutoring modes."""
    engine = TutoringEngine()

    # Request direct explanation
    mode = engine.detect_mode_intent("Explain directly to me, I don't understand", TutoringMode.SOCRATIC)
    assert mode == TutoringMode.EXPLANATION

    # Request practice problem
    mode = engine.detect_mode_intent("Give me a numerical problem to practice", TutoringMode.SOCRATIC)
    assert mode == TutoringMode.GUIDED_PRACTICE

    # Request diagnostic assessment
    mode = engine.detect_mode_intent("Test my knowledge from the beginning", TutoringMode.SOCRATIC)
    assert mode == TutoringMode.DIAGNOSTIC

    # Request revision
    mode = engine.detect_mode_intent("Let's review my mistakes and weak points", TutoringMode.SOCRATIC)
    assert mode == TutoringMode.REVISION


def test_learner_adaptive_difficulty():
    """Verify difficulty progression and regression in LearnerState."""
    state = LearnerStateModel(
        session_id="test_session",
        current_topic="FCFS",
        current_mode="socratic",
        difficulty_level="beginner"
    )

    # Simulate 3 successful turns
    for _ in range(3):
        resp = TutorStructuredResponse(
            message="Good job",
            mode=TutoringMode.SOCRATIC,
            topic="FCFS",
            action=TutorAction.ASK_QUESTION,
            concepts_demonstrated=["concept_a", "concept_b"],
            concepts_needing_review=[],
            source_ids=[]
        )
        LearnerModelManager.update_state_from_turn(state, resp, "Arrival order")

    # Should be promoted to intermediate
    assert state.difficulty_level == "intermediate"

    # Simulate accumulation of errors
    for _ in range(4):
        resp_err = TutorStructuredResponse(
            message="Not quite",
            mode=TutoringMode.SOCRATIC,
            topic="FCFS",
            action=TutorAction.PROVIDE_HINT,
            misconception="Confused waiting time with burst time",
            hint="Try again",
            concepts_demonstrated=[],
            concepts_needing_review=["waiting_time"]
        )
        LearnerModelManager.update_state_from_turn(state, resp_err, "Burst time")

    # Should demote back to beginner
    assert state.difficulty_level == "beginner"


def test_knowledge_catalog_coverage():
    """Verify that comprehensive concepts across Modules A, B, C, D are present and match."""
    from app.core.knowledge_catalog import find_knowledge_entry

    test_queries = [
        "what is preemptive and non preemptive?",
        "what are process states and transitions?",
        "what is the difference between process and program?",
        "what is the convoy effect?",
        "what is shortest job first?",
        "what is shortest remaining time first?",
        "explain priority scheduling and aging",
        "how does round robin work?",
        "what are the 3 types of schedulers?",
        "what is completely fair scheduler cfs?",
        "what is rate monotonic scheduling?"
    ]

    for q in test_queries:
        match = find_knowledge_entry(q)
        assert match is not None, f"Query '{q}' should match a knowledge entry"
        assert len(match["message"]) > 100
        assert match["question"] is not None


def test_catalog_answer_evaluation():
    """Verify that canonical student answers to understanding checks are evaluated accurately."""
    from app.core.knowledge_catalog import evaluate_catalog_answer

    # Test preemption question
    q_preempt = "Under which specific operating circumstance does an algorithm switch from running to ready: a voluntary I/O request or an asynchronous timer interrupt?"
    eval_correct = evaluate_catalog_answer(q_preempt, "an asynchronous timer interrupt")
    assert eval_correct is not None
    assert eval_correct["action"] == "evaluate_answer"
    assert "timer interrupt" in eval_correct["message"].lower()

    eval_incorrect = evaluate_catalog_answer(q_preempt, "voluntary i/o request")
    assert eval_incorrect is not None
    assert eval_incorrect["misconception"] is not None


def test_conversation_greeting():
    """Test 1: 'Hello' receives a short, natural greeting without syllabus dump or academic questions."""
    import asyncio
    engine = TutoringEngine()
    state = LearnerStateModel(session_id="s_greet", current_topic="Fundamentals", current_mode="socratic")
    resp = asyncio.run(engine.generate_tutor_turn("s_greet", "Hello", [], state))
    assert "Hey! What are we learning today?" in resp.message
    assert resp.action == TutorAction.CHAT
    assert resp.question is None
    assert "syllabus" not in resp.message.lower()
    assert "algorithms" not in resp.message.lower()
    assert "**Question:**" not in resp.message
    assert state.questions_attempted == 0


def test_conversation_general_goal():
    """Test 2: 'I'm studying CPU scheduling.' receives 'Nice. Which part are you working on?'"""
    import asyncio
    engine = TutoringEngine()
    state = LearnerStateModel(session_id="s_goal", current_topic="Fundamentals", current_mode="socratic")
    resp = asyncio.run(engine.generate_tutor_turn("s_goal", "I'm studying CPU scheduling.", [], state))
    assert "Nice. Which part are you working on?" in resp.message
    assert resp.action == TutorAction.CHAT
    assert resp.question is None
    assert "syllabus" not in resp.message.lower()
    assert "**Question:**" not in resp.message


def test_conversation_new_concept_inquiry():
    """Test 3: 'I want to understand preemptive and non-preemptive scheduling.' assesses baseline with one short question."""
    import asyncio
    engine = TutoringEngine()
    state = LearnerStateModel(session_id="s_preempt", current_topic="Fundamentals", current_mode="socratic")
    resp = asyncio.run(engine.generate_tutor_turn("s_preempt", "I want to understand preemptive and non-preemptive scheduling.", [], state))
    assert "Sure. Before I explain, what do you already know about the difference?" in resp.message
    assert resp.action == TutorAction.ASK_QUESTION
    assert "**Question:**" not in resp.message


def test_conversation_zero_knowledge():
    """Test 4: 'I don't know anything about it.' starts with simple everyday analogy (desk/task) without interrogating."""
    import asyncio
    engine = TutoringEngine()
    state = LearnerStateModel(session_id="s_zero", current_topic="Preemption", current_mode="socratic")
    resp = asyncio.run(engine.generate_tutor_turn("s_zero", "I don't know anything about it.", [], state))
    assert "desk" in resp.message.lower() or "pause" in resp.message.lower()
    assert resp.action == TutorAction.EXPLAIN_CONCEPT
    assert resp.mode == TutoringMode.EXPLANATION
    assert "**Question:**" not in resp.message


def test_conversation_partial_understanding():
    """Test 5: 'I know that preemptive scheduling can interrupt a running process.' acknowledges and focuses on next step."""
    import asyncio
    engine = TutoringEngine()
    state = LearnerStateModel(session_id="s_part", current_topic="Preemption", current_mode="socratic")
    resp = asyncio.run(engine.generate_tutor_turn("s_part", "I know that preemptive scheduling can interrupt a running process.", [], state))
    assert "Exactly" in resp.message
    assert "ready" in resp.message.lower()
    assert "quick example" in resp.message.lower()
    assert "**Question:**" not in resp.message


def test_conversation_direct_explanation():
    """Test 6: 'Just explain it directly.' delivers clear explanation without diagnostic questions."""
    import asyncio
    engine = TutoringEngine()
    state = LearnerStateModel(session_id="s_direct", current_topic="Preemption", current_mode="socratic")
    resp = asyncio.run(engine.generate_tutor_turn("s_direct", "Just explain it directly.", [], state))
    assert "Preemptive Scheduling" in resp.message
    assert "Non-Preemptive" in resp.message
    assert resp.action == TutorAction.EXPLAIN_CONCEPT
    assert resp.question is None

    assert "**Question:**" not in resp.message


def test_conversation_concept_comparison():
    """Test 7: 'What is the difference between FCFS and SJF?' explains distinction, trade-offs, and short example."""
    import asyncio
    engine = TutoringEngine()
    state = LearnerStateModel(session_id="s_comp", current_topic="Fundamentals", current_mode="socratic")
    resp = asyncio.run(engine.generate_tutor_turn("s_comp", "What is the difference between FCFS and SJF?", [], state))
    assert "FCFS" in resp.message and "SJF" in resp.message
    assert "Convoy Effect" in resp.message
    assert "starvation" in resp.message.lower()
    assert "Example" in resp.message
    assert "**Question:**" not in resp.message


def test_conversation_gratitude():
    """Test 8: 'Thanks.' receives 'You're welcome!' without new lessons or academic questions."""
    import asyncio
    engine = TutoringEngine()
    state = LearnerStateModel(session_id="s_thx", current_topic="FCFS", current_mode="socratic")
    resp = asyncio.run(engine.generate_tutor_turn("s_thx", "Thanks.", [], state))
    assert "You're welcome!" in resp.message
    assert resp.action == TutorAction.CHAT
    assert resp.question is None
    assert "**Question:**" not in resp.message


def test_syllabus_shown_only_on_explicit_request():
    """Test 9: Syllabus is shown ONLY when explicitly asked, never on casual greetings."""
    import asyncio
    engine = TutoringEngine()
    state = LearnerStateModel(session_id="s_syl", current_topic="Fundamentals", current_mode="socratic")

    # Casual greeting should NOT have syllabus
    resp_greet = asyncio.run(engine.generate_tutor_turn("s_syl", "Hello", [], state))
    assert "syllabus" not in resp_greet.message.lower()
    assert "algorithms" not in resp_greet.message.lower()

    # Explicit syllabus request SHOULD have syllabus
    resp_syl = asyncio.run(engine.generate_tutor_turn("s_syl", "What is on the syllabus?", [], state))
    assert "topics we cover" in resp_syl.message.lower()
    assert "Non-Preemptive Algorithms" in resp_syl.message
    assert "Preemptive Algorithms" in resp_syl.message


def test_round_robin_conversation_sequence():
    """
    Verifies the full 7-step conversational sequence from Section 1 & Section 7:
    1. Student: hello -> Short, natural greeting.
    2. Student: i want to learn process scheduling -> Short goal acknowledgement.
    3. Student: i want to explore round robin -> Introduces RR and asks large-quantum equivalence question.
    4. Student: i dont know the answer -> Recognizes response to pending question, explains FCFS equivalence and why.
    5. Student: take an example for the round robin and elaborate -> Deterministic worked numerical example with ready queue, Gantt, and metrics.
    6. Student: Which algorithm does Round Robin become equivalent to when the time quantum is larger than the longest CPU burst? -> Direct FCFS answer.
    7. Student: Let's learn SJF instead. -> Topic switch to SJF.
    """
    import asyncio
    from app.database.models import MessageModel

    engine = TutoringEngine()
    session_id = "test_rr_sequence_session"
    state = LearnerStateModel(session_id=session_id, current_topic="Fundamentals", current_mode="socratic")
    history = []

    # Step 1: Greeting
    resp1 = asyncio.run(engine.generate_tutor_turn(session_id, "hello", history, state))
    assert "Hey! What are we learning today?" in resp1.message
    assert resp1.action == TutorAction.CHAT
    history.append(MessageModel(session_id=session_id, role="user", content="hello"))
    history.append(MessageModel(session_id=session_id, role="assistant", content=resp1.message))

    # Step 2: General Goal
    resp2 = asyncio.run(engine.generate_tutor_turn(session_id, "i want to learn process scheduling", history, state))
    assert "Nice. Which part are you working on?" in resp2.message
    assert resp2.action == TutorAction.CHAT
    history.append(MessageModel(session_id=session_id, role="user", content="i want to learn process scheduling"))
    history.append(MessageModel(session_id=session_id, role="assistant", content=resp2.message))

    # Step 3: Explore Round Robin
    resp3 = asyncio.run(engine.generate_tutor_turn(session_id, "i want to explore round robin", history, state))
    assert "Round Robin" in resp3.message
    assert "time quantum" in resp3.message.lower()
    assert "equivalent" in resp3.message.lower()
    assert state.pending_question is not None
    assert "equivalent" in state.pending_question.lower()
    assert state.current_topic == "Round Robin"
    history.append(MessageModel(session_id=session_id, role="user", content="i want to explore round robin"))
    history.append(MessageModel(session_id=session_id, role="assistant", content=resp3.message))

    # Step 4: Responding to pending question with "i dont know the answer"
    resp4 = asyncio.run(engine.generate_tutor_turn(session_id, "i dont know the answer", history, state))
    assert "First-Come, First-Served" in resp4.message or "FCFS" in resp4.message
    assert "preempted" in resp4.message.lower()
    # It should NOT be the desk preemption analogy
    assert "desk" not in resp4.message.lower()
    history.append(MessageModel(session_id=session_id, role="user", content="i dont know the answer"))
    history.append(MessageModel(session_id=session_id, role="assistant", content=resp4.message))

    # Step 5: Worked Example
    resp5 = asyncio.run(engine.generate_tutor_turn(session_id, "take an example for the round robin and elaborate", history, state))
    assert "Worked Example: Round Robin" in resp5.message
    assert "Ready Queue Evolution" in resp5.message
    assert "Gantt Chart" in resp5.message
    assert "Average Turnaround Time" in resp5.message
    assert "7.33 ms" in resp5.message
    assert "Average Waiting Time" in resp5.message
    assert "4.33 ms" in resp5.message
    assert "CPU Utilization" in resp5.message
    assert "100.0%" in resp5.message
    assert resp5.gantt_chart_ascii is not None
    history.append(MessageModel(session_id=session_id, role="user", content="take an example for the round robin and elaborate"))
    history.append(MessageModel(session_id=session_id, role="assistant", content=resp5.message))

    # Step 6: Direct Equivalence Question
    resp6 = asyncio.run(engine.generate_tutor_turn(session_id, "Which algorithm does Round Robin become equivalent to when the time quantum is larger than the longest CPU burst?", history, state))
    assert "First-Come, First-Served" in resp6.message or "FCFS" in resp6.message
    assert resp6.action == TutorAction.EXPLAIN_CONCEPT
    assert "Gantt Chart" not in resp6.message  # Should not repeat the entire example/lecture
    history.append(MessageModel(session_id=session_id, role="user", content="Which algorithm does Round Robin become equivalent to when the time quantum is larger than the longest CPU burst?"))
    history.append(MessageModel(session_id=session_id, role="assistant", content=resp6.message))

    # Step 7: Topic Switch to SJF
    resp7 = asyncio.run(engine.generate_tutor_turn(session_id, "Let's learn SJF instead.", history, state))
    assert "Shortest Job First" in resp7.message or "SJF" in resp7.message
    assert state.current_topic == "SJF"
    assert "non-preemptive" in resp7.message.lower() or "srtf" in resp7.message.lower()


def test_round_robin_worked_example_metrics():
    """
    Verifies Section 7 Benchmark exact metrics:
    Processes: P1(0, 5), P2(0, 3), P3(0, 1) with q = 2 ms.
    Completion Times: P1=9, P2=8, P3=5.
    Avg TAT: 7.33 ms, Avg WT: 4.33 ms, CPU Util: 100%.
    """
    import asyncio
    engine = TutoringEngine()
    session_id = "test_rr_metrics_session"
    state = LearnerStateModel(session_id=session_id, current_topic="Round Robin", current_mode="explanation")

    resp = asyncio.run(engine.generate_tutor_turn(session_id, "give an example of round robin", [], state))
    assert "Worked Example: Round Robin" in resp.message
    assert "P1" in resp.message and "P2" in resp.message and "P3" in resp.message
    assert "7.33 ms" in resp.message
    assert "4.33 ms" in resp.message
    assert "100.0%" in resp.message
    assert resp.gantt_chart_ascii is not None
    assert "P1" in resp.gantt_chart_ascii and "P2" in resp.gantt_chart_ascii and "P3" in resp.gantt_chart_ascii


def test_scenario_a_fcfs_beginner_dialogue():
    """
    Scenario A (Section 16): Beginner learning FCFS.
    Turn 1: Student: "What is FCFS?" -> Tutor asks prior knowledge.
    Turn 2: Student: "Nothing at all" -> Tutor gives Canteen analogy and asks check question.
    Turn 3: Student: "The short processes skip ahead" -> Tutor detects misconception, clarifies non-preemptive rule, asks waiting time impact.
    Turn 4: Student: "Waiting times increase massively (convoy effect)" -> Tutor acknowledges convoy effect.
    """
    import asyncio
    from app.database.models import MessageModel
    engine = TutoringEngine()
    session_id = "test_scenario_a_session"
    state = LearnerStateModel(session_id=session_id, current_topic="Fundamentals", current_mode="socratic")
    history = []

    # Turn 1: Opening
    resp1 = asyncio.run(engine.generate_tutor_turn(session_id, "What is FCFS?", history, state))
    assert "Before we get into it, what do you already know about FCFS?" in resp1.message
    assert resp1.action == TutorAction.ASK_QUESTION
    assert state.current_topic == "FCFS"
    history.append(MessageModel(session_id=session_id, role="user", content="What is FCFS?"))
    history.append(MessageModel(session_id=session_id, role="assistant", content=resp1.message))

    # Turn 2: Student knows nothing
    resp2 = asyncio.run(engine.generate_tutor_turn(session_id, "Nothing at all, completely new to me", history, state))
    assert "canteen" in resp2.message.lower() or "queue" in resp2.message.lower()
    assert "really long time to finish" in resp2.message.lower() or "long time" in resp2.message.lower()
    assert resp2.action == TutorAction.ASK_QUESTION
    history.append(MessageModel(session_id=session_id, role="user", content="Nothing at all, completely new to me"))
    history.append(MessageModel(session_id=session_id, role="assistant", content=resp2.message))

    # Turn 3: Student holds misconception that shorter processes can skip ahead
    resp3 = asyncio.run(engine.generate_tutor_turn(session_id, "I guess the shorter processes can skip ahead and run first", history, state))
    assert "non-preemptive" in resp3.message.lower()
    assert "waiting time" in resp3.message.lower()
    assert resp3.action == TutorAction.ASK_QUESTION
    history.append(MessageModel(session_id=session_id, role="user", content="I guess the shorter processes can skip ahead and run first"))
    history.append(MessageModel(session_id=session_id, role="assistant", content=resp3.message))

    # Turn 4: Student realizes waiting time increases / convoy effect
    resp4 = asyncio.run(engine.generate_tutor_turn(session_id, "Their waiting times increase a lot, like a convoy", history, state))
    assert "Convoy Effect" in resp4.message
    assert "Gantt chart" in resp4.message or "worked example" in resp4.message
    history.append(MessageModel(session_id=session_id, role="user", content="Their waiting times increase a lot, like a convoy"))
    history.append(MessageModel(session_id=session_id, role="assistant", content=resp4.message))


def test_scenario_b_fcfs_prior_knowledge():
    """
    Scenario B (Section 16): Student demonstrates prior knowledge.
    Tutor acknowledges understanding, avoids redundant lecturing, advances to Convoy Effect.
    """
    import asyncio
    from app.database.models import MessageModel
    engine = TutoringEngine()
    session_id = "test_scenario_b_session"
    state = LearnerStateModel(session_id=session_id, current_topic="Fundamentals", current_mode="socratic")
    history = []

    # Turn 1: Opening
    resp1 = asyncio.run(engine.generate_tutor_turn(session_id, "Teach me FCFS", history, state))
    history.append(MessageModel(session_id=session_id, role="user", content="Teach me FCFS"))
    history.append(MessageModel(session_id=session_id, role="assistant", content=resp1.message))

    # Turn 2: Prior knowledge stated
    resp2 = asyncio.run(engine.generate_tutor_turn(session_id, "I already know that FCFS executes jobs strictly in the order of arrival without preemption.", history, state))
    assert "Correct" in resp2.message or "Exactly" in resp2.message
    assert "convoy effect" in resp2.message.lower()
    # It should NOT repeat the canteen analogy since learner already knows the basics
    assert "canteen" not in resp2.message.lower()


def test_scenario_d_interactive_quiz_flow():
    """
    Scenario D (Section 16 & Section 10): Interactive Quiz Mode.
    Turn 1: Student triggers quiz on Round Robin.
    Turn 2: Student answers Q1 correctly -> Tutor provides feedback and gives Q2.
    Turn 3: Student answers Q2 correctly -> Tutor provides feedback and gives Q3.
    Turn 4: Student answers Q3 -> Tutor concludes with Markdown summary table.
    """
    import asyncio
    engine = TutoringEngine()
    session_id = "test_scenario_d_session"
    state = LearnerStateModel(session_id=session_id, current_topic="Round Robin", current_mode="socratic")
    history = []

    # Turn 1: Quiz trigger
    resp1 = asyncio.run(engine.generate_tutor_turn(session_id, "Quiz me on Round Robin", history, state))
    assert "Interactive Quiz: Round Robin" in resp1.message
    assert "Question 1 of 3" in resp1.message
    assert state.quiz_state.get("is_active") is True
    assert resp1.action == TutorAction.ASK_QUESTION

    # Turn 2: Answer Q1 ("time quantum")
    resp2 = asyncio.run(engine.generate_tutor_turn(session_id, "It is called the time quantum", history, state))
    assert "Correct!" in resp2.message or "time quantum" in resp2.message.lower()
    assert "Question 2 of 3" in resp2.message
    assert state.quiz_state.get("is_active") is True

    # Turn 3: Answer Q2 ("FCFS")
    resp3 = asyncio.run(engine.generate_tutor_turn(session_id, "It becomes equivalent to FCFS", history, state))
    assert "Correct!" in resp3.message or "FCFS" in resp3.message
    assert "Question 3 of 3" in resp3.message
    assert state.quiz_state.get("is_active") is True

    # Turn 4: Answer Q3 ("context switch overhead")
    resp4 = asyncio.run(engine.generate_tutor_turn(session_id, "Context switch overhead increases dramatically", history, state))
    assert "Quiz Complete: Round Robin" in resp4.message
    assert "| Metric | Result |" in resp4.message
    assert "Questions Attempted" in resp4.message
    assert "Score" in resp4.message
    assert "Demonstrated Concepts" in resp4.message
    assert "Recommended Next Step" in resp4.message
    assert state.quiz_state.get("is_active") is False


def test_scenario_f_direct_formula_request():
    """
    Scenario F (Section 16): Direct formula inquiry.
    Tutor immediately returns formulas without forcing Socratic diagnostic questions.
    """
    import asyncio
    engine = TutoringEngine()
    session_id = "test_scenario_f_session"
    state = LearnerStateModel(session_id=session_id, current_topic="Fundamentals", current_mode="socratic")
    history = []

    resp = asyncio.run(engine.generate_tutor_turn(session_id, "What is the formula for waiting time? Just give me the formula.", history, state))
    assert "Waiting Time (WT)" in resp.message
    assert "Turnaround Time (TAT)" in resp.message
    assert "Burst Time (BT)" in resp.message
    assert resp.action == TutorAction.EXPLAIN_CONCEPT
    assert resp.question is None


def test_section_14_test_a_new_concept():
    """Test A (Section 14): 'What is Round Robin?' starts with a guiding question, not a textbook dump."""
    import asyncio
    engine = TutoringEngine()
    state = LearnerStateModel(session_id="test_a", current_topic="Fundamentals", current_mode="socratic")
    resp = asyncio.run(engine.generate_tutor_turn("test_a", "What is Round Robin?", [], state))
    assert resp.action == TutorAction.ASK_QUESTION
    assert "computer" in resp.message.lower() or "share" in resp.message.lower()
    # It must NOT dump the full definition or answer its own question in the opening
    assert "time quantum is defined as" not in resp.message.lower()
    assert state.pending_question is not None


def test_section_14_test_b_student_does_not_know():
    """Test B (Section 14): Student says 'I don't know' -> tutor explains with simpler analogy, doesn't restart."""
    import asyncio
    from app.database.models import MessageModel
    engine = TutoringEngine()
    state = LearnerStateModel(session_id="test_b", current_topic="Fundamentals", current_mode="socratic")
    resp1 = asyncio.run(engine.generate_tutor_turn("test_b", "What is Round Robin?", [], state))

    history = [
        MessageModel(session_id="test_b", role="user", content="What is Round Robin?"),
        MessageModel(session_id="test_b", role="assistant", content=resp1.message)
    ]
    resp2 = asyncio.run(engine.generate_tutor_turn("test_b", "I don't know", history, state))
    assert resp2.action == TutorAction.ASK_QUESTION
    assert "board game" in resp2.message.lower() or "timer" in resp2.message.lower() or "swing" in resp2.message.lower()
    assert state.pending_question is not None


def test_section_14_test_c_correct_response():
    """Test C (Section 14): Student gives correct answer -> tutor acknowledges and introduces next concept."""
    import asyncio
    from app.database.models import MessageModel
    engine = TutoringEngine()
    state = LearnerStateModel(session_id="test_c", current_topic="Fundamentals", current_mode="socratic")
    resp1 = asyncio.run(engine.generate_tutor_turn("test_c", "What is Round Robin?", [], state))

    history = [
        MessageModel(session_id="test_c", role="user", content="What is Round Robin?"),
        MessageModel(session_id="test_c", role="assistant", content=resp1.message)
    ]
    resp2 = asyncio.run(engine.generate_tutor_turn("test_c", "They should take turns with a timer", history, state))
    assert resp2.action == TutorAction.ASK_QUESTION
    assert "time quantum" in resp2.message.lower()
    assert "ready queue" in resp2.message.lower() or "back of the queue" in resp2.message.lower() or "expires" in resp2.message.lower()


def test_section_14_test_d_incorrect_response():
    """Test D (Section 14): Student gives incorrect answer -> tutor identifies misconception and offers hint."""
    import asyncio
    from app.database.models import MessageModel
    engine = TutoringEngine()
    state = LearnerStateModel(session_id="test_d", current_topic="Fundamentals", current_mode="socratic")
    resp1 = asyncio.run(engine.generate_tutor_turn("test_d", "What is Round Robin?", [], state))

    history = [
        MessageModel(session_id="test_d", role="user", content="What is Round Robin?"),
        MessageModel(session_id="test_d", role="assistant", content=resp1.message)
    ]
    resp2 = asyncio.run(engine.generate_tutor_turn("test_d", "Kick them off the computer permanently", history, state))
    assert resp2.action == TutorAction.ASK_QUESTION
    assert resp2.misconception is not None
    assert "permanently" in resp2.message.lower() or "unfinished work" in resp2.message.lower()


def test_section_14_test_e_request_for_example():
    """Test E (Section 14): Student asks for an example -> tutor provides worked example immediately."""
    import asyncio
    engine = TutoringEngine()
    state = LearnerStateModel(session_id="test_e", current_topic="Round Robin", current_mode="socratic")
    resp = asyncio.run(engine.generate_tutor_turn("test_e", "Give me an example of Round Robin", [], state))
    assert "Worked Example: Round Robin" in resp.message
    assert resp.gantt_chart_ascii is not None
    assert "7.33 ms" in resp.message


def test_section_14_test_f_direct_answer():
    """Test F (Section 14): Student says 'Just give me the definition' -> tutor provides definition directly."""
    import asyncio
    engine = TutoringEngine()
    state = LearnerStateModel(session_id="test_f", current_topic="Fundamentals", current_mode="socratic")
    resp = asyncio.run(engine.generate_tutor_turn("test_f", "Just give me the definition of Round Robin", [], state))
    assert resp.action == TutorAction.EXPLAIN_CONCEPT
    assert "Round Robin (RR)" in resp.message
    assert resp.question is None


def test_section_14_test_g_topic_change():
    """Test G (Section 14): Student switches from FCFS to SRTF -> preserves progress, switches cleanly."""
    import asyncio
    engine = TutoringEngine()
    state = LearnerStateModel(session_id="test_g", current_topic="FCFS", current_mode="socratic")
    resp = asyncio.run(engine.generate_tutor_turn("test_g", "Let's learn SRTF instead.", [], state))
    assert "SRTF" in resp.message or "Shortest Remaining Time First" in resp.message
    assert state.current_topic == "SRTF"


def test_section_14_test_h_quiz():
    """Test H (Section 14): Student says 'Quiz me on scheduling' -> conducts quiz one question at a time."""
    import asyncio
    engine = TutoringEngine()
    state = LearnerStateModel(session_id="test_h", current_topic="Fundamentals", current_mode="socratic")
    resp = asyncio.run(engine.generate_tutor_turn("test_h", "Quiz me on FCFS", [], state))
    assert "Interactive Quiz: FCFS" in resp.message
    assert "Question 1 of" in resp.message
    assert state.quiz_state.get("is_active") is True


def test_section_14_test_i_long_conversation_15_turns():
    """
    Test I (Section 14): 15-turn complete pedagogical conversation.
    Verifies context retention, pending questions memory, latest message responsiveness,
    no repeated boilerplate, and coherent learner state across topics and quizzes.
    """
    import asyncio
    from app.database.models import MessageModel
    engine = TutoringEngine()
    session_id = "test_long_conv_15"
    state = LearnerStateModel(session_id=session_id, current_topic="Fundamentals", current_mode="socratic")
    history = []

    script = [
        # Turn 1: Greeting
        ("Hello", lambda r: "Hey! What are we learning today?" in r.message),
        # Turn 2: Goal
        ("I'm studying CPU scheduling.", lambda r: "Nice. Which part are you working on?" in r.message),
        # Turn 3: New Concept: Round Robin
        ("What is Round Robin?", lambda r: "share one computer" in r.message.lower()),
        # Turn 4: Answer Q1
        ("Give each person a timer to take turns", lambda r: "time quantum" in r.message.lower()),
        # Turn 5: Answer Q2
        ("The unfinished process goes to the back of the queue", lambda r: "Ready Queue" in r.message or "equivalent" in r.message.lower()),
        # Turn 6: Answer Q3
        ("It becomes FCFS", lambda r: "concrete numerical example" in r.message.lower() or "FCFS" in r.message),
        # Turn 7: Request worked example
        ("take an example for the round robin and elaborate", lambda r: "Worked Example: Round Robin" in r.message),
        # Turn 8: Ask for formula directly
        ("What is the formula for waiting time? Just give me the formula.", lambda r: "Waiting Time (WT)" in r.message and r.question is None),
        # Turn 9: Topic switch to SJF
        ("Let's switch to SJF instead.", lambda r: "Shortest Job First" in r.message or "SJF" in r.message),
        # Turn 10: Inquire about SJF
        ("What is SJF?", lambda r: "service desk" in r.message.lower() or "shortest" in r.message.lower()),
        # Turn 11: Answer SJF check
        ("1 min, 2 min, 5 min, then 30 min", lambda r: "starvation" in r.message.lower() or "Shortest Job First" in r.message),
        # Turn 12: Answer starvation check
        ("It starves and never gets to run", lambda r: "starvation" in r.message.lower() and "priority" in r.message.lower()),
        # Turn 13: Answer aging check
        ("Aging increases priority over time", lambda r: "concrete numerical example" in r.message.lower() or "Aging" in r.message),
        # Turn 14: Start a quiz
        ("Quiz me on Round Robin", lambda r: "Interactive Quiz: Round Robin" in r.message and "Question 1 of 3" in r.message),
        # Turn 15: Answer Quiz Q1
        ("time quantum", lambda r: "Correct!" in r.message or "Question 2 of 3" in r.message)
    ]

    for turn_idx, (user_text, check_fn) in enumerate(script, start=1):
        resp = asyncio.run(engine.generate_tutor_turn(session_id, user_text, history, state))
        assert check_fn(resp), f"Turn {turn_idx} failed for input '{user_text}'. Response:\n{resp.message}"
        history.append(MessageModel(session_id=session_id, role="user", content=user_text))
        history.append(MessageModel(session_id=session_id, role="assistant", content=resp.message))

    # Verification of final state
    assert len(history) == 30  # 15 user + 15 assistant
    assert state.quiz_state.get("is_active") is True
    assert state.questions_attempted >= 1


def test_hrrn_socratic_and_worked_example():
    """Verify Socratic curriculum dialogue and coaching worked example for HRRN."""
    import asyncio
    engine = TutoringEngine()
    session_id = "test_hrrn_session"
    state = LearnerStateModel(session_id=session_id, current_topic="Fundamentals", current_mode="socratic")
    history = []

    # Turn 1: Socratic Opening for HRRN
    resp1 = asyncio.run(engine.generate_tutor_turn(session_id, "I want to learn HRRN", history, state))
    assert "bakery" in resp1.message.lower() or "balance" in resp1.message.lower()
    assert resp1.action == TutorAction.ASK_QUESTION
    history.append(MessageModel(session_id=session_id, role="user", content="I want to learn HRRN"))
    history.append(MessageModel(session_id=session_id, role="assistant", content=resp1.message))

    # Turn 2: Student gives intuitive answer balancing wait and service
    resp2 = asyncio.run(engine.generate_tutor_turn(session_id, "balance waiting time and service time", history, state))
    assert "Response Ratio" in resp2.message or "R =" in resp2.message
    assert "preemptive" in resp2.message.lower()
    history.append(MessageModel(session_id=session_id, role="user", content="balance waiting time and service time"))
    history.append(MessageModel(session_id=session_id, role="assistant", content=resp2.message))

    # Turn 3: Answer non-preemptive
    resp3 = asyncio.run(engine.generate_tutor_turn(session_id, "it is non-preemptive", history, state))
    assert "non-preemptive" in resp3.message.lower()
    assert "what algorithm does HRRN behave exactly like" in resp3.message or "sjf" in resp3.message.lower() or "same moment" in resp3.message.lower()
    history.append(MessageModel(session_id=session_id, role="user", content="it is non-preemptive"))
    history.append(MessageModel(session_id=session_id, role="assistant", content=resp3.message))

    # Turn 4: Answer SJF equivalence
    resp4 = asyncio.run(engine.generate_tutor_turn(session_id, "it behaves like SJF", history, state))
    assert "concrete numerical example" in resp4.message.lower() or "gantt" in resp4.message.lower()
    history.append(MessageModel(session_id=session_id, role="user", content="it behaves like SJF"))
    history.append(MessageModel(session_id=session_id, role="assistant", content=resp4.message))

    # Turn 5: Worked Example
    resp5 = asyncio.run(engine.generate_tutor_turn(session_id, "take an example for HRRN and elaborate", history, state))
    assert "Worked Example: HRRN" in resp5.message
    assert "Gantt Chart" in resp5.message
    assert "Tutor Check" in resp5.message
    history.append(MessageModel(session_id=session_id, role="user", content="take an example for HRRN and elaborate"))
    history.append(MessageModel(session_id=session_id, role="assistant", content=resp5.message))

    # Turn 6: Answer tutor check question
    resp6 = asyncio.run(engine.generate_tutor_turn(session_id, "the process that waited longer has the higher response ratio", history, state))
    assert "Spot on!" in resp6.message
    assert "starvation" in resp6.message.lower()


def test_cfs_socratic_dialogue():
    """Verify Socratic curriculum dialogue for Linux Completely Fair Scheduler (CFS)."""
    import asyncio
    engine = TutoringEngine()
    session_id = "test_cfs_session"
    state = LearnerStateModel(session_id=session_id, current_topic="Fundamentals", current_mode="socratic")
    history = []

    # Turn 1: Socratic Opening for CFS
    resp1 = asyncio.run(engine.generate_tutor_turn(session_id, "What is CFS?", history, state))
    assert "computer" in resp1.message.lower() or "track" in resp1.message.lower() or "equal" in resp1.message.lower()
    assert resp1.action == TutorAction.ASK_QUESTION
    history.append(MessageModel(session_id=session_id, role="user", content="What is CFS?"))
    history.append(MessageModel(session_id=session_id, role="assistant", content=resp1.message))

    # Turn 2: Track usage / virtual time
    resp2 = asyncio.run(engine.generate_tutor_turn(session_id, "track who spent the least time", history, state))
    assert "vruntime" in resp2.message.lower()
    assert "binary search tree" in resp2.message.lower() or "data structure" in resp2.message.lower()
    history.append(MessageModel(session_id=session_id, role="user", content="track who spent the least time"))
    history.append(MessageModel(session_id=session_id, role="assistant", content=resp2.message))

    # Turn 3: Red-black tree
    resp3 = asyncio.run(engine.generate_tutor_turn(session_id, "red-black tree", history, state))
    assert "red-black tree" in resp3.message.lower() or "rbtree" in resp3.message.lower()
    assert "nice" in resp3.message.lower()


def test_real_time_rms_edf_dialogue():
    """Verify Socratic curriculum dialogue for Real-Time Scheduling (RMS and EDF)."""
    import asyncio
    engine = TutoringEngine()
    session_id = "test_rt_session"
    state = LearnerStateModel(session_id=session_id, current_topic="Fundamentals", current_mode="socratic")
    history = []

    # Turn 1: Opening
    resp1 = asyncio.run(engine.generate_tutor_turn(session_id, "Teach me real-time scheduling", history, state))
    assert "flight controller" in resp1.message.lower() or "pacemaker" in resp1.message.lower()
    history.append(MessageModel(session_id=session_id, role="user", content="Teach me real-time scheduling"))
    history.append(MessageModel(session_id=session_id, role="assistant", content=resp1.message))

    # Turn 2: Catastrophic consequences / deadline
    resp2 = asyncio.run(engine.generate_tutor_turn(session_id, "catastrophic failure if deadline is missed", history, state))
    assert "Hard Real-Time" in resp2.message or "Soft Real-Time" in resp2.message
    assert "Rate Monotonic" in resp2.message or "RMS" in resp2.message
    history.append(MessageModel(session_id=session_id, role="user", content="catastrophic failure if deadline is missed"))
    history.append(MessageModel(session_id=session_id, role="assistant", content=resp2.message))

    # Turn 3: RMS static priority
    resp3 = asyncio.run(engine.generate_tutor_turn(session_id, "shorter period gets higher priority", history, state))
    assert "EDF" in resp3.message or "Earliest Deadline First" in resp3.message
    assert "utilization" in resp3.message.lower()
    history.append(MessageModel(session_id=session_id, role="user", content="shorter period gets higher priority"))
    history.append(MessageModel(session_id=session_id, role="assistant", content=resp3.message))

    # Turn 4: EDF 100% bound
    resp4 = asyncio.run(engine.generate_tutor_turn(session_id, "100%", history, state))
    assert "concrete numerical example" in resp4.message.lower() or "nailed the core concept" in resp4.message.lower()


def test_multiprocessor_dialogue():
    """Verify Socratic curriculum dialogue for Multiprocessor Scheduling."""
    import asyncio
    engine = TutoringEngine()
    session_id = "test_multi_session"
    state = LearnerStateModel(session_id=session_id, current_topic="Fundamentals", current_mode="socratic")
    history = []

    # Turn 1: Opening
    resp1 = asyncio.run(engine.generate_tutor_turn(session_id, "Explain multiprocessor scheduling", history, state))
    assert "cook" in resp1.message.lower() or "kitchen" in resp1.message.lower() or "queue" in resp1.message.lower()
    history.append(MessageModel(session_id=session_id, role="user", content="Explain multiprocessor scheduling"))
    history.append(MessageModel(session_id=session_id, role="assistant", content=resp1.message))

    # Turn 2: Separate per-cook queues
    resp2 = asyncio.run(engine.generate_tutor_turn(session_id, "each cook should have their own queue", history, state))
    assert "SQMS" in resp2.message or "MQMS" in resp2.message
    assert "cache" in resp2.message.lower() or "affinity" in resp2.message.lower()
    history.append(MessageModel(session_id=session_id, role="user", content="each cook should have their own queue"))
    history.append(MessageModel(session_id=session_id, role="assistant", content=resp2.message))

    # Turn 3: Processor affinity
    resp3 = asyncio.run(engine.generate_tutor_turn(session_id, "processor affinity", history, state))
    assert "Affinity" in resp3.message
    assert "Core 1" in resp3.message or "queue" in resp3.message.lower()
    history.append(MessageModel(session_id=session_id, role="user", content="processor affinity"))
    history.append(MessageModel(session_id=session_id, role="assistant", content=resp3.message))

    # Turn 4: Work stealing
    resp4 = asyncio.run(engine.generate_tutor_turn(session_id, "work stealing", history, state))
    assert "concrete numerical example" in resp4.message.lower() or "nailed the core concept" in resp4.message.lower()


def test_worked_example_coaching_and_check_question_dialogues():
    """Verify tutor coaching and follow-up check question validation across FCFS, SJF, and SRTF."""
    import asyncio
    engine = TutoringEngine()

    # 1. FCFS Worked Example & Check Question
    s_fcfs = LearnerStateModel(session_id="s_fcfs", current_topic="FCFS", current_mode="socratic")
    resp_fcfs = asyncio.run(engine.generate_tutor_turn("s_fcfs", "take an example for FCFS and elaborate", [], s_fcfs))
    assert "Worked Example: FCFS" in resp_fcfs.message
    assert "Tutor Check:" in resp_fcfs.message
    assert "waiting effect called in FCFS" in resp_fcfs.message
    # Student responds to the check question
    resp_fcfs_ans = asyncio.run(engine.generate_tutor_turn("s_fcfs", "that is the convoy effect", [], s_fcfs))
    assert "Convoy Effect" in resp_fcfs_ans.message
    assert "Exactly right!" in resp_fcfs_ans.message

    # 2. SJF Worked Example & Check Question
    s_sjf = LearnerStateModel(session_id="s_sjf", current_topic="SJF", current_mode="socratic")
    resp_sjf = asyncio.run(engine.generate_tutor_turn("s_sjf", "take an example for SJF and elaborate", [], s_sjf))
    assert "SJF" in resp_sjf.message
    assert "Tutor Check:" in resp_sjf.message
    # Student responds to the check question
    resp_sjf_ans = asyncio.run(engine.generate_tutor_turn("s_sjf", "P3 has the shortest burst time", [], s_sjf))
    assert "Spot on!" in resp_sjf_ans.message
    assert "minimizes" in resp_sjf_ans.message.lower()

    # 3. SRTF Worked Example & Check Question
    s_srtf = LearnerStateModel(session_id="s_srtf", current_topic="SRTF", current_mode="socratic")
    resp_srtf = asyncio.run(engine.generate_tutor_turn("s_srtf", "take an example for SRTF and elaborate", [], s_srtf))
    assert "SRTF" in resp_srtf.message
    assert "Tutor Check:" in resp_srtf.message
    # Student responds to the check question
    resp_srtf_ans = asyncio.run(engine.generate_tutor_turn("s_srtf", "there would be no preemption because 8 is larger than 6", [], s_srtf))
    assert "Spot on!" in resp_srtf_ans.message
    assert "preemption" in resp_srtf_ans.message.lower()





