import sys
sys.path.insert(0, ".")
from app.core.tutoring_engine import TutoringEngine
from app.schemas.chat import TutoringMode

engine = TutoringEngine()

test_topics = [
    ("FCFS", "take an example for FCFS and elaborate"),
    ("SJF", "take an example for SJF and elaborate"),
    ("SRTF", "take an example for SRTF and elaborate"),
    ("Priority", "take an example for Priority and elaborate"),
    ("Round Robin", "take an example for Round Robin and elaborate"),
    ("HRRN", "take an example for HRRN and elaborate"),
    ("MLFQ", "take an example for MLFQ and elaborate"),
    ("Linux CFS", "take an example for CFS and elaborate"),
    ("Real-Time", "take an example for real-time scheduling and elaborate"),
    ("Multiprocessor", "take an example for multiprocessor scheduling and elaborate"),
    ("Stride Scheduling", "take an example for stride scheduling and elaborate"),
]

for name, q in test_topics:
    summary, gantt, md = engine._attempt_deterministic_solve(q, name, TutoringMode.SOCRATIC, is_example_intent=True)
    assert md is not None, f"Failed for {name}"
    assert "Tutor Check:" in md, f"Missing Tutor Check in {name}"
    print(f"PASSED {name}: {summary.splitlines()[0]}")
