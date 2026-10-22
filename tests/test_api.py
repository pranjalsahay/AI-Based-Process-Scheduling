"""Integration tests for FastAPI backend API endpoints."""

import os
os.environ["TESTING"] = "1"

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database.connection import Base, engine


@pytest.fixture(scope="module")
def client():
    """Provides a TestClient with clean test tables."""
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c


def test_health_check(client):
    """Test health check endpoint."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert "services" in data
    assert "hardware" in data


def test_session_lifecycle(client):
    """Test session creation, listing, retrieval, and deletion."""
    # 1. Create session
    create_res = client.post("/api/sessions", json={"title": "Test FCFS", "topic": "FCFS"})
    assert create_res.status_code == 201
    s_data = create_res.json()
    session_id = s_data["session_id"]
    assert s_data["title"] == "Test FCFS"
    assert s_data["topic"] == "FCFS"

    # 2. List sessions
    list_res = client.get("/api/sessions")
    assert list_res.status_code == 200
    all_sessions = list_res.json()
    assert any(s["session_id"] == session_id for s in all_sessions)

    # 3. Get session detail
    detail_res = client.get(f"/api/sessions/{session_id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["session_id"] == session_id

    # 4. Delete session
    del_res = client.delete(f"/api/sessions/{session_id}")
    assert del_res.status_code == 200

    # 5. Verify 404 after deletion
    get_after_del = client.get(f"/api/sessions/{session_id}")
    assert get_after_del.status_code == 404


def test_scheduling_calculate_endpoint(client):
    """Test deterministic scheduling calculation via API."""
    payload = {
        "algorithm": "fcfs",
        "processes": [
            {"pid": "P1", "arrival_time": 0, "burst_time": 10},
            {"pid": "P2", "arrival_time": 2, "burst_time": 5}
        ]
    }
    res = client.post("/api/scheduling/calculate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["algorithm"] == "fcfs"
    assert len(data["processes"]) == 2
    assert "ascii_gantt" in data
    assert data["avg_waiting_time"] is not None


def test_scheduling_compare_endpoint(client):
    """Test multi-algorithm comparison via API."""
    payload = {
        "processes": [
            {"pid": "P1", "arrival_time": 0, "burst_time": 8, "priority": 2},
            {"pid": "P2", "arrival_time": 1, "burst_time": 4, "priority": 1}
        ],
        "time_quantum": 2.0
    }
    res = client.post("/api/scheduling/compare", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "summary" in data
    assert "best_for_waiting_time" in data


def test_knowledge_sources_endpoint(client):
    """Test knowledge sources retrieval."""
    res = client.get("/api/knowledge/sources")
    assert res.status_code == 200
    data = res.json()
    assert "total_chunks" in data
    assert "sources" in data


def test_frontend_serving(client):
    """Test that static frontend files and root index are properly served."""
    root_res = client.get("/")
    assert root_res.status_code == 200
    assert "SchedulAI" in root_res.text

    css_res = client.get("/static/styles.css")
    assert css_res.status_code == 200
    assert "--bg-primary" in css_res.text

    js_res = client.get("/static/app.js")
    assert js_res.status_code == 200
    assert "SchedulAI Frontend Application" in js_res.text


def test_chat_and_progress_integration(client):
    """Test sending a chat message turn and reading updated learner progress."""
    chat_payload = {
        "message": "Hello, I want to learn FCFS from the beginning.",
        "topic": "FCFS"
    }
    res = client.post("/api/chat", json=chat_payload)
    assert res.status_code == 200
    data = res.json()

    assert "session_id" in data
    assert "message" in data
    assert data["topic"] == "FCFS"
    assert "mode" in data
    session_id = data["session_id"]

    # Check progress endpoint
    prog_res = client.get(f"/api/progress/{session_id}")
    assert prog_res.status_code == 200
    prog_data = prog_res.json()
    assert prog_data["session_id"] == session_id
    assert prog_data["questions_attempted"] >= 1
    assert "accuracy_percentage" in prog_data
    assert "mastery_score" in prog_data


def test_api_conversational_turn_requirements(client):
    """Verify that all Section 1.A conversational requirements execute accurately over the API."""
    # 1. Greeting
    r1 = client.post("/api/chat", json={"message": "Hello"})
    assert r1.status_code == 200
    d1 = r1.json()
    assert "Hey! What are we learning today?" in d1["message"]
    assert d1["action"] == "chat"
    assert "**Question:**" not in d1["message"]
    assert "syllabus" not in d1["message"].lower()
    session_id = d1["session_id"]

    # 2. General Goal
    r2 = client.post("/api/chat", json={"session_id": session_id, "message": "I'm studying CPU scheduling."})
    assert r2.status_code == 200
    d2 = r2.json()
    assert "Nice. Which part are you working on?" in d2["message"]
    assert d2["action"] == "chat"

    # 3. New Concept Inquiry
    r3 = client.post("/api/chat", json={"session_id": session_id, "message": "I want to understand preemptive and non-preemptive scheduling."})
    assert r3.status_code == 200
    d3 = r3.json()
    assert "Sure. Before I explain, what do you already know about the difference?" in d3["message"]
    assert d3["action"] == "ask_question"

    # 4. Zero Knowledge
    r4 = client.post("/api/chat", json={"session_id": session_id, "message": "I don't know anything about it."})
    assert r4.status_code == 200
    d4 = r4.json()
    assert "desk" in d4["message"].lower() or "pause" in d4["message"].lower()
    assert d4["action"] == "explain_concept"

    # 5. Partial Understanding
    r5 = client.post("/api/chat", json={"session_id": session_id, "message": "I know that preemptive scheduling can interrupt a running process."})
    assert r5.status_code == 200
    d5 = r5.json()
    assert "Exactly" in d5["message"]
    assert "quick example" in d5["message"].lower()

    # 6. Direct Explanation Request
    r6 = client.post("/api/chat", json={"session_id": session_id, "message": "Just explain it directly."})
    assert r6.status_code == 200
    d6 = r6.json()
    assert "Preemptive Scheduling" in d6["message"]
    assert "Non-Preemptive" in d6["message"]
    assert d6["action"] == "explain_concept"
    assert d6["question"] is None

    # 7. Comparison: FCFS vs SJF
    r7 = client.post("/api/chat", json={"session_id": session_id, "message": "What is the difference between FCFS and SJF?"})
    assert r7.status_code == 200
    d7 = r7.json()
    assert "FCFS" in d7["message"] and "SJF" in d7["message"]
    assert "Convoy Effect" in d7["message"]
    assert "starvation" in d7["message"].lower()

    # 8. Gratitude
    r8 = client.post("/api/chat", json={"session_id": session_id, "message": "Thanks."})
    assert r8.status_code == 200
    d8 = r8.json()
    assert "You're welcome!" in d8["message"]
    assert d8["action"] == "chat"
    assert d8["question"] is None

    # 9. Explicit Syllabus
    r9 = client.post("/api/chat", json={"session_id": session_id, "message": "What is on the syllabus?"})
    assert r9.status_code == 200
    d9 = r9.json()
    assert "topics we cover" in d9["message"].lower()
    assert "Non-Preemptive Algorithms" in d9["message"]
    assert "Preemptive Algorithms" in d9["message"]


def test_api_round_robin_sequence(client):
    """Verify the Section 1 & Section 7 conversation flow over the FastAPI chat endpoint."""
    # 1. Hello
    r1 = client.post("/api/chat", json={"message": "hello"})
    assert r1.status_code == 200
    d1 = r1.json()
    assert "Hey! What are we learning today?" in d1["message"]
    sid = d1["session_id"]

    # 2. General Goal: Process Scheduling
    r2 = client.post("/api/chat", json={"session_id": sid, "message": "i want to learn process scheduling"})
    assert r2.status_code == 200
    d2 = r2.json()
    assert "Nice. Which part are you working on?" in d2["message"]

    # 3. Explore Round Robin
    r3 = client.post("/api/chat", json={"session_id": sid, "message": "i want to explore round robin"})
    assert r3.status_code == 200
    d3 = r3.json()
    assert "Round Robin" in d3["message"]
    assert "time quantum" in d3["message"].lower()
    assert "equivalent" in d3["message"].lower()
    assert d3["topic"] == "Round Robin"

    # 4. Student doesn't know the answer
    r4 = client.post("/api/chat", json={"session_id": sid, "message": "i dont know the answer"})
    assert r4.status_code == 200
    d4 = r4.json()
    assert "First-Come, First-Served" in d4["message"] or "FCFS" in d4["message"]
    assert "desk" not in d4["message"].lower()

    # 5. Worked Example request
    r5 = client.post("/api/chat", json={"session_id": sid, "message": "take an example for the round robin and elaborate"})
    assert r5.status_code == 200
    d5 = r5.json()
    assert "Worked Example: Round Robin" in d5["message"]
    assert "Ready Queue Evolution" in d5["message"]
    assert "Average Turnaround Time" in d5["message"]
    assert "7.33 ms" in d5["message"]
    assert "Average Waiting Time" in d5["message"]
    assert "4.33 ms" in d5["message"]
    assert "CPU Utilization" in d5["message"]
    assert "100.0%" in d5["message"]
    assert d5["gantt_chart_ascii"] is not None

    # 6. Direct Equivalence Question
    r6 = client.post("/api/chat", json={"session_id": sid, "message": "Which algorithm does Round Robin become equivalent to when the time quantum is larger than the longest CPU burst?"})
    assert r6.status_code == 200
    d6 = r6.json()
    assert "First-Come, First-Served" in d6["message"] or "FCFS" in d6["message"]
    assert "Gantt Chart" not in d6["message"]

    # 7. Topic switch to SJF
    r7 = client.post("/api/chat", json={"session_id": sid, "message": "Let's learn SJF instead."})
    assert r7.status_code == 200
    d7 = r7.json()
    assert "Shortest Job First" in d7["message"] or "SJF" in d7["message"]
    assert d7["topic"] == "SJF"


def test_api_scenario_a_fcfs_beginner(client):
    """Verify Scenario A (FCFS Beginner Socratic Conversation) over API."""
    # 1. Ask about FCFS
    r1 = client.post("/api/chat", json={"message": "What is FCFS?"})
    assert r1.status_code == 200
    d1 = r1.json()
    assert "Before we get into it, what do you already know about FCFS?" in d1["message"]
    sid = d1["session_id"]

    # 2. Student knows nothing
    r2 = client.post("/api/chat", json={"session_id": sid, "message": "Nothing at all, completely new to me"})
    assert r2.status_code == 200
    d2 = r2.json()
    assert "canteen" in d2["message"].lower() or "queue" in d2["message"].lower()

    # 3. Misconception: shorter process skips ahead
    r3 = client.post("/api/chat", json={"session_id": sid, "message": "I think the shorter process can just skip ahead and execute first"})
    assert r3.status_code == 200
    d3 = r3.json()
    assert "non-preemptive" in d3["message"].lower()
    assert "waiting time" in d3["message"].lower()

    # 4. Correct answer: convoy effect / high waiting time
    r4 = client.post("/api/chat", json={"session_id": sid, "message": "Their waiting time increases a lot because of the convoy effect"})
    assert r4.status_code == 200
    d4 = r4.json()
    assert "Convoy Effect" in d4["message"]


def test_api_scenario_b_fcfs_prior_knowledge(client):
    """Verify Scenario B (FCFS Prior Knowledge) over API."""
    # 1. Ask about FCFS
    r1 = client.post("/api/chat", json={"message": "Teach me FCFS"})
    assert r1.status_code == 200
    sid = r1.json()["session_id"]

    # 2. Prior knowledge
    r2 = client.post("/api/chat", json={"session_id": sid, "message": "I already know that FCFS executes jobs strictly in the order of arrival without preemption."})
    assert r2.status_code == 200
    d2 = r2.json()
    assert "Correct" in d2["message"] or "convoy effect" in d2["message"].lower()
    assert "canteen" not in d2["message"].lower()


def test_api_scenario_d_interactive_quiz(client):
    """Verify Scenario D (Interactive Quiz Mode with turn-by-turn adaptation and summary) over API."""
    # 1. Trigger Quiz
    r1 = client.post("/api/chat", json={"message": "Quiz me on Round Robin"})
    assert r1.status_code == 200
    d1 = r1.json()
    assert "Interactive Quiz: Round Robin" in d1["message"]
    assert "Question 1 of 3" in d1["message"]
    sid = d1["session_id"]

    # 2. Answer Q1
    r2 = client.post("/api/chat", json={"session_id": sid, "message": "time quantum"})
    assert r2.status_code == 200
    d2 = r2.json()
    assert "Correct!" in d2["message"] or "time quantum" in d2["message"].lower()
    assert "Question 2 of 3" in d2["message"]

    # 3. Answer Q2
    r3 = client.post("/api/chat", json={"session_id": sid, "message": "FCFS"})
    assert r3.status_code == 200
    d3 = r3.json()
    assert "Correct!" in d3["message"] or "FCFS" in d3["message"]
    assert "Question 3 of 3" in d3["message"]

    # 4. Answer Q3
    r4 = client.post("/api/chat", json={"session_id": sid, "message": "context switch overhead"})
    assert r4.status_code == 200
    d4 = r4.json()
    assert "Quiz Complete: Round Robin" in d4["message"]
    assert "| Metric | Result |" in d4["message"]
    assert "Questions Attempted" in d4["message"]
    assert "Score" in d4["message"]


def test_api_scenario_f_direct_formula(client):
    """Verify Scenario F (Direct Formula Request) over API."""
    r = client.post("/api/chat", json={"message": "What is the formula for waiting time? Just give me the formula."})
    assert r.status_code == 200
    d = r.json()
    assert "Waiting Time (WT)" in d["message"]
    assert "Turnaround Time (TAT)" in d["message"]
    assert d["action"] == "explain_concept"
    assert d["question"] is None


