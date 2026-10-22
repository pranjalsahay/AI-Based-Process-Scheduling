import asyncio
import sys
sys.path.insert(0, ".")

from app.core.tutoring_engine import TutoringEngine
from app.database.models import LearnerStateModel
from app.schemas.chat import TutoringMode

engine = TutoringEngine()

dialogues = [
    ("FCFS", "waiting effect called in fcfs", "that is the convoy effect"),
    ("Round Robin", "quantum were made very large", "it becomes FCFS"),
    ("SJF", "shortest burst minimize", "shorter jobs leave the queue earliest"),
    ("SRTF", "burst 8 ms instead", "no preemption would occur"),
    ("Priority", "priority 0 arrived", "it would preempt immediately"),
    ("HRRN", "which one gets chosen first", "the process that waited longer"),
    ("MLFQ", "demoted jobs in q2 do not starve", "priority boost"),
    ("Linux CFS", "negative nice value make vruntime grow faster or slower", "it grows slower"),
    ("Real-Time", "what would happen under preemptive rms", "tau_1 would preempt tau_2"),
    ("Multiprocessor", "what trade-off occurs when p4 migrates from core 1 to core 0", "cache affinity loss and cache misses"),
    ("Stride", "smaller stride cause a process to be selected more frequently or less frequently", "selected more frequently"),
]

for name, pending_phrase, student_answer in dialogues:
    state = LearnerStateModel(
        session_id=f"test_{name}",
        current_topic=name,
        pending_question=f"Here is a check question: {pending_phrase}?",
        last_question_asked=f"Here is a check question: {pending_phrase}?"
    )
    resp = asyncio.run(engine.generate_tutor_turn(f"sess_{name}", student_answer, [], state))
    assert resp.action in ("ask_question", "evaluate_answer", "explain_concept"), f"Unexpected action {resp.action} for {name}"
    assert any(w in resp.message.lower() for w in ["spot on", "exactly", "precisely", "correct", "great", "right"]), f"Expected warm acknowledgment in {name}: {resp.message[:100]}"
    print(f"PASSED {name}: Acknowledged warmly! '{resp.message[:60]}...' Next Q: '{resp.question}'")
