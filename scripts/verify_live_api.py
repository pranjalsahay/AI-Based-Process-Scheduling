import httpx
import time

base_url = "http://127.0.0.1:8000"

client = httpx.Client(base_url=base_url, timeout=30.0)

# 1. Health
h = client.get("/api/health").json()
print("Health:", h["status"])

# 2. Session
s = client.post("/api/sessions", json={"title": "Test Session", "topic": "Fundamentals"}).json()
session_id = s["session_id"]
print("Session ID:", session_id)

test_queries = [
    ("difference between process and program", ["Text Segment", "Data Segment", "Heap", "Stack", "cookbook"]),
    ("what is dispatch latency and context switch?", ["Dispatch Latency", "Scheduler vs. Dispatcher", "Cache Effects"]),
    ("what is shortest remaining time first?", ["Shortest Remaining Time First", "preempted", "remaining"]),
    ("what is starvation and aging?", ["Starvation", "Aging", "IBM 7094"]),
    ("how does multilevel feedback queue work?", ["Multilevel Feedback Queue", "migrate", "Queue 0"]),
    ("what is the 80% rule in time quantum?", ["80% Rule", "Time Quantum", "Round Robin"]),
    ("what are the formulas for turnaround time and waiting time?", ["TAT", "Completion Time", "Waiting Time"]),
    ("what is rate monotonic scheduling?", ["Rate Monotonic", "static-priority", "period"]),
    ("what is kernel preemption?", ["Preemptive Kernel", "Kernel Mode", "real-time"])
]

for q, expected_tokens in test_queries:
    t0 = time.time()
    res = client.post("/api/chat", json={"session_id": session_id, "message": q})
    elapsed = time.time() - t0
    data = res.json()
    msg = data.get("message", "")
    action = data.get("action")
    topic = data.get("topic")
    has_all_tokens = all(tok.lower() in msg.lower() for tok in expected_tokens)
    print(f"\nQuery: '{q}'")
    print(f"  Elapsed: {elapsed:.2f}s | Status: {res.status_code} | Action: {action} | Topic: {topic}")
    print(f"  Tokens Verified ({has_all_tokens}): {expected_tokens}")
    print(f"  Question: {data.get('question')}")
