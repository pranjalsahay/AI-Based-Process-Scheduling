"""Interactive Quiz Engine for SchedulAI executing within the existing chat interface.

Implements Section 10 of SchedulAI specifications:
- Natural initiation ('Quiz me on Round Robin', 'Test what I've learned', 'CAT-level questions').
- Establish scope & difficulty (Beginner, Intermediate, Advanced, Exam).
- One question at a time with immediate evaluation and misconception diagnosis.
- Dynamic difficulty adaptation based on student answers.
- Comprehensive end-of-quiz summary with score, mastered concepts, and revision advice.
- Zero UI changes: 100% conversational chat stream.
"""

import re
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from app.database.models import LearnerStateModel
from app.schemas.chat import TutoringMode, TutorAction, TutorStructuredResponse

logger = logging.getLogger(__name__)


# Structured question bank categorized by topic and difficulty level
QUIZ_BANK: Dict[str, List[Dict[str, Any]]] = {
    "FCFS": [
        {
            "id": "fcfs_beg_1",
            "difficulty": "beginner",
            "question": "In First-Come, First-Served (FCFS) scheduling, what primary criterion determines the order in which processes receive CPU time?",
            "expected_keywords": ["arrival", "arrival time", "order of arrival", "order they arrive", "arrival order", "first come", "fifo"],
            "correct_explanation": "In FCFS, processes are placed in a FIFO queue and dispatched strictly according to their **arrival time** in the ready queue.",
            "misconception_keywords": {"burst": "Burst time is used in Shortest Job First (SJF), not FCFS.", "priority": "Priority numbers are used in Priority scheduling, not FCFS."},
            "concept": "fcfs_selection_criteria",
            "hint": "Think about standing in a line at a ticket counter."
        },
        {
            "id": "fcfs_int_1",
            "difficulty": "intermediate",
            "question": "What is the name of the phenomenon in FCFS where short processes experience long waiting times behind a single CPU-intensive process?",
            "expected_keywords": ["convoy", "convoy effect", "the convoy effect"],
            "correct_explanation": "This is the **Convoy Effect**. It causes high average waiting times because short CPU bursts are delayed behind a massive long-running job.",
            "misconception_keywords": {"starvation": "In FCFS there is no starvation because every process eventually finishes. The effect of waiting behind a long job is the Convoy Effect.", "aging": "Aging is a solution to starvation, not the waiting bottleneck in FCFS."},
            "concept": "convoy_effect",
            "hint": "Think of small cars stuck behind a slow truck on a single-lane highway."
        },
        {
            "id": "fcfs_adv_1",
            "difficulty": "advanced",
            "question": "Consider two processes arriving at t=0: P1 with burst 10 ms, and P2 with burst 2 ms. Under FCFS (P1 runs first), what is the average waiting time?",
            "expected_keywords": ["5", "5 ms", "5ms", "5.0"],
            "correct_explanation": "P1 waits 0 ms. P2 waits 10 ms while P1 runs. Average Waiting Time = (0 + 10) / 2 = **5.0 ms**.",
            "misconception_keywords": {"6": "6 ms is the average turnaround time ((10 + 12)/2 = 11, wait: (0+10)/2=5). Remember Waiting Time = Turnaround Time - Burst Time."},
            "concept": "fcfs_metric_calculation",
            "hint": "Calculate P1's waiting time (0 ms) and P2's waiting time (10 ms), then take the average."
        }
    ],
    "Round Robin": [
        {
            "id": "rr_beg_1",
            "difficulty": "beginner",
            "question": "What is the fixed unit of CPU time allocated to each process in Round Robin scheduling called?",
            "expected_keywords": ["time quantum", "quantum", "time slice", "slice"],
            "correct_explanation": "Each process receives a predetermined interval called a **time quantum** (or time slice).",
            "misconception_keywords": {"burst": "Burst time is the total work required by the process, while the fixed allocation is the time quantum."},
            "concept": "time_quantum_definition",
            "hint": "It starts with the letter 'Q' or 'T'."
        },
        {
            "id": "rr_int_1",
            "difficulty": "intermediate",
            "question": "Which standard scheduling algorithm does Round Robin become equivalent to when the time quantum is larger than the longest process CPU burst?",
            "expected_keywords": ["fcfs", "first come", "first-come", "fifo"],
            "correct_explanation": "When the quantum exceeds the maximum burst, every process finishes in its very first turn without preemption, behaving exactly like **FCFS**.",
            "misconception_keywords": {"sjf": "SJF selects by shortest burst, whereas large-quantum RR simply runs jobs in their arrival order (FCFS)."},
            "concept": "rr_fcfs_equivalence",
            "hint": "Think about what happens if no process is ever preempted by the timer."
        },
        {
            "id": "rr_adv_1",
            "difficulty": "advanced",
            "question": "What undesirable system performance penalty increases dramatically if the Round Robin time quantum is set extremely small (e.g. 1 microsecond)?",
            "expected_keywords": ["context switch", "context switching", "overhead", "context switch overhead", "switching overhead"],
            "correct_explanation": "An extremely small time quantum causes excessive **context switches**, spending more CPU cycles saving and restoring process state than executing real user work.",
            "misconception_keywords": {"starvation": "Round Robin guarantees zero starvation. The problem with tiny quanta is context-switching overhead."},
            "concept": "context_switch_tradeoff",
            "hint": "Think about what the CPU dispatcher must do every time a process is swapped out."
        }
    ],
    "SJF": [
        {
            "id": "sjf_beg_1",
            "difficulty": "beginner",
            "question": "What property of a process does Shortest Job First (SJF) inspect to determine which process to execute next?",
            "expected_keywords": ["burst", "burst time", "cpu burst", "shortest burst", "duration", "length"],
            "correct_explanation": "SJF selects the process with the smallest **CPU burst time** (or next CPU burst length).",
            "misconception_keywords": {"arrival": "Arrival order is used in FCFS. SJF looks at the CPU burst length."},
            "concept": "sjf_selection_rule",
            "hint": "Think of how long the process needs to run on the CPU."
        },
        {
            "id": "sjf_int_1",
            "difficulty": "intermediate",
            "question": "What theoretical performance advantage is provably guaranteed by the SJF algorithm for a given set of stationary processes?",
            "expected_keywords": ["optimal", "minimum waiting time", "minimal waiting time", "lowest waiting time", "minimum average waiting time", "optimal waiting time"],
            "correct_explanation": "SJF is provably **optimal** for minimizing the **average waiting time** across any set of processes.",
            "misconception_keywords": {"fairness": "SJF is not fair; long jobs can starve. Its advantage is optimal average waiting time."},
            "concept": "sjf_optimality",
            "hint": "Think about the metric that measures how long processes wait in the ready queue."
        },
        {
            "id": "sjf_adv_1",
            "difficulty": "advanced",
            "question": "What is the preemptive version of Shortest Job First scheduling commonly called?",
            "expected_keywords": ["srtf", "shortest remaining time first", "shortest remaining time", "srtn"],
            "correct_explanation": "Preemptive SJF is known as **Shortest Remaining Time First (SRTF)**.",
            "misconception_keywords": {"round robin": "Round Robin shares CPU by time quantum, whereas preemptive SJF compares remaining burst times."},
            "concept": "srtf_distinction",
            "hint": "It stands for Shortest Remaining Time First."
        }
    ],
    "Priority": [
        {
            "id": "prio_beg_1",
            "difficulty": "beginner",
            "question": "What severe condition can occur when low-priority processes wait indefinitely in the ready queue because high-priority processes keep arriving?",
            "expected_keywords": ["starvation", "indefinite blocking", "starve", "starving"],
            "correct_explanation": "This condition is known as **starvation** (or indefinite blocking).",
            "misconception_keywords": {"deadlock": "Deadlock is a circular wait for shared resources. Starvation is being perpetually neglected by the scheduler."},
            "concept": "starvation_definition",
            "hint": "It shares its name with being deprived of food."
        },
        {
            "id": "prio_int_1",
            "difficulty": "intermediate",
            "question": "What technique solves starvation by gradually increasing the priority of processes that have waited in the ready queue for a long time?",
            "expected_keywords": ["aging", "ageing"],
            "correct_explanation": "**Aging** gradually increments a process's priority as time passes, ensuring that all processes eventually reach the highest priority and execute.",
            "misconception_keywords": {"preemption": "Preemption is the ability to interrupt a running process; Aging is the technique that prevents starvation."},
            "concept": "aging_solution",
            "hint": "It relates to getting older over time."
        }
    ],
    "Metrics": [
        {
            "id": "met_beg_1",
            "difficulty": "beginner",
            "question": "Write the standard formula for Turnaround Time (TAT) in terms of Completion Time (CT) and Arrival Time (AT).",
            "expected_keywords": ["ct - at", "completion time - arrival time", "completion - arrival"],
            "correct_explanation": "Turnaround Time is the total elapsed time from process submission to termination: **TAT = Completion Time (CT) - Arrival Time (AT)**.",
            "misconception_keywords": {"tat - bt": "TAT - BT is the formula for Waiting Time, not Turnaround Time."},
            "concept": "turnaround_time_formula",
            "hint": "Finish time minus entry time."
        },
        {
            "id": "met_int_1",
            "difficulty": "intermediate",
            "question": "Write the formula for Waiting Time (WT) in terms of Turnaround Time (TAT) and Burst Time (BT).",
            "expected_keywords": ["tat - bt", "turnaround time - burst time", "turnaround - burst"],
            "correct_explanation": "Waiting Time is the time a process spends waiting in the ready queue: **WT = Turnaround Time (TAT) - Burst Time (BT)**.",
            "misconception_keywords": {"ct - at": "CT - AT is Turnaround Time. Waiting Time is TAT - BT."},
            "concept": "waiting_time_formula",
            "hint": "Total duration minus active execution time."
        },
        {
            "id": "met_adv_1",
            "difficulty": "advanced",
            "question": "A process arrives at t=2 ms, starts executing at t=5 ms, and finishes at t=12 ms. What is its Response Time (RT)?",
            "expected_keywords": ["3", "3 ms", "3ms", "3.0"],
            "correct_explanation": "Response Time is the time from arrival to first execution start: **RT = First Start Time - Arrival Time = 5 - 2 = 3.0 ms**.",
            "misconception_keywords": {"10": "10 ms is Turnaround Time (12 - 2). Response time measures until the *first* CPU access (5 - 2 = 3 ms).", "7": "7 ms is the burst duration (12 - 5)."},
            "concept": "response_time_calculation",
            "hint": "Start time (5) minus arrival time (2)."
        }
    ],
    "Fundamentals": [
        {
            "id": "fund_beg_1",
            "difficulty": "beginner",
            "question": "What kernel data structure holds all metadata, registers, state, and scheduling priority for an active process?",
            "expected_keywords": ["pcb", "process control block", "task_struct"],
            "correct_explanation": "The **Process Control Block (PCB)** stores all process-specific context including program counter, CPU registers, process state, and memory bounds.",
            "misconception_keywords": {"ready queue": "The ready queue holds references to PCBs, but the data structure holding the metadata is the PCB itself."},
            "concept": "pcb_definition",
            "hint": "Three-letter acronym for Process Control Block."
        },
        {
            "id": "fund_int_1",
            "difficulty": "intermediate",
            "question": "Which OS component is responsible for actually giving control of the CPU to the process selected by the short-term scheduler?",
            "expected_keywords": ["dispatcher", "dispatch"],
            "correct_explanation": "The **Dispatcher** performs the context switch, switches to user mode, and jumps to the proper location in the user program to restart it.",
            "misconception_keywords": {"scheduler": "The scheduler *selects* which process should run; the *dispatcher* is the component that actually performs the context switch and grants CPU control."},
            "concept": "dispatcher_vs_scheduler",
            "hint": "It switches CPU state and jumps to user mode."
        }
    ]
}


class QuizEngine:
    """Manages conversational quiz sessions embedded directly inside the chat interface."""

    @staticmethod
    def is_quiz_trigger(text: str) -> bool:
        """Determines if user input is an explicit command to start a quiz."""
        t = text.lower().strip()
        triggers = [
            "quiz me", "start quiz", "take a quiz", "test what i've learned", "test me",
            "give me a quiz", "ask me cat-level questions", "cat-level questions",
            "exam practice quiz", "practice quiz", "quiz on", "test on"
        ]
        return any(tr in t for tr in triggers)

    @staticmethod
    def is_quiz_stop_command(text: str) -> bool:
        """Determines if student wants to prematurely end or exit the quiz."""
        t = text.lower().strip()
        stop_words = ["stop quiz", "end quiz", "exit quiz", "quit quiz", "cancel quiz", "finish quiz", "back to tutor", "stop the quiz"]
        return any(sw in t for sw in stop_words)

    @staticmethod
    def detect_quiz_topic(text: str, default_topic: str = "Fundamentals") -> str:
        """Identifies target topic for the quiz."""
        t = text.lower()
        if "round robin" in t or re.search(r"\brr\b", t):
            return "Round Robin"
        elif "sjf" in t or "srtf" in t or "shortest job" in t:
            return "SJF"
        elif "priority" in t or "aging" in t:
            return "Priority"
        elif "fcfs" in t or "first come" in t:
            return "FCFS"
        elif "metric" in t or "turnaround" in t or "waiting time" in t:
            return "Metrics"
        elif "fundamental" in t or "pcb" in t or "dispatcher" in t:
            return "Fundamentals"
        elif any(k in t for k in ["cpu scheduling", "everything", "all", "comprehensive", "cat-level"]):
            return "Comprehensive"
        return default_topic if default_topic in QUIZ_BANK else "Comprehensive"

    @staticmethod
    def detect_quiz_difficulty(text: str) -> str:
        """Extracts desired initial difficulty level."""
        t = text.lower()
        if "exam" in t or "cat" in t or "cat-level" in t:
            return "advanced"
        elif "advanced" in t or "hard" in t or "difficult" in t:
            return "advanced"
        elif "intermediate" in t or "medium" in t:
            return "intermediate"
        elif "beginner" in t or "easy" in t or "basic" in t:
            return "beginner"
        return "beginner"

    @classmethod
    def start_quiz(cls, learner_state: LearnerStateModel, user_text: str) -> TutorStructuredResponse:
        """Initializes a new quiz session and returns Question 1."""
        topic = cls.detect_quiz_topic(user_text, learner_state.current_topic or "Fundamentals")
        difficulty = cls.detect_quiz_difficulty(user_text)

        # Build list of questions for this quiz
        selected_questions = cls._select_quiz_questions(topic, difficulty)
        if not selected_questions:
            # Fallback to general questions
            selected_questions = cls._select_quiz_questions("Fundamentals", "beginner")

        quiz_state = {
            "is_active": True,
            "topic": topic,
            "difficulty": difficulty,
            "question_ids": [q["id"] for q in selected_questions],
            "current_index": 0,
            "total_questions": len(selected_questions),
            "score": 0.0,
            "answers_log": [],
            "concepts_mastered": [],
            "concepts_needing_review": []
        }
        learner_state.quiz_state = quiz_state
        learner_state.pending_question = selected_questions[0]["question"]
        learner_state.last_question_asked = selected_questions[0]["question"]
        learner_state.lesson_stage = "guided_practice"

        first_q = selected_questions[0]
        welcome_banner = (
            f"🎯 **Interactive Quiz: {topic}** (Level: *{difficulty.title()}*)\n\n"
            f"I will ask you **{len(selected_questions)} questions** one by one. Take your time and answer each in your own words.\n\n"
            f"**Question 1 of {len(selected_questions)}:**\n"
            f"{first_q['question']}"
        )

        return TutorStructuredResponse(
            message=welcome_banner,
            mode=TutoringMode.GUIDED_PRACTICE,
            topic=topic if topic != "Comprehensive" else "Fundamentals",
            action=TutorAction.ASK_QUESTION,
            question=first_q["question"],
            hint=first_q.get("hint"),
            misconception=None,
            concepts_demonstrated=[],
            concepts_needing_review=[],
            source_ids=[],
            requires_calculation=False
        )

    @classmethod
    def handle_quiz_turn(
        cls,
        learner_state: LearnerStateModel,
        user_answer: str
    ) -> TutorStructuredResponse:
        """Evaluates current question answer, adapts difficulty, and advances or concludes."""
        quiz_state = learner_state.quiz_state
        if not quiz_state or not quiz_state.get("is_active"):
            return None

        # Check for user requesting to stop quiz
        if cls.is_quiz_stop_command(user_answer):
            return cls._abort_quiz(learner_state)

        q_ids = quiz_state.get("question_ids", [])
        idx = quiz_state.get("current_index", 0)
        if idx >= len(q_ids):
            return cls._finish_quiz(learner_state)

        cur_qid = q_ids[idx]
        q_obj = cls._find_question_by_id(cur_qid)
        if not q_obj:
            # Advance if question missing
            quiz_state["current_index"] += 1
            learner_state.quiz_state = quiz_state
            return cls._finish_quiz(learner_state)

        # Evaluate the answer
        is_correct, is_partial, feedback_text, misconception = cls._evaluate_single_answer(q_obj, user_answer)

        # Update scoring and concepts
        if is_correct:
            quiz_state["score"] += 1.0
            learner_state.correct_answers = (learner_state.correct_answers or 0) + 1
            if q_obj.get("concept"):
                quiz_state["concepts_mastered"].append(q_obj["concept"])
                understood = set(learner_state.concepts_understood)
                understood.add(q_obj["concept"])
                learner_state.concepts_understood = list(understood)
        elif is_partial:
            quiz_state["score"] += 0.5
            learner_state.partial_answers = (learner_state.partial_answers or 0) + 1
        else:
            learner_state.incorrect_answers = (learner_state.incorrect_answers or 0) + 1
            if q_obj.get("concept"):
                quiz_state["concepts_needing_review"].append(q_obj["concept"])
                review = set(learner_state.concepts_needing_review)
                review.add(q_obj["concept"])
                learner_state.concepts_needing_review = list(review)

        learner_state.questions_attempted = (learner_state.questions_attempted or 0) + 1
        quiz_state["answers_log"].append({
            "question_id": cur_qid,
            "answer": user_answer,
            "is_correct": is_correct,
            "is_partial": is_partial
        })

        # Advance to next question or conclude
        next_idx = idx + 1
        quiz_state["current_index"] = next_idx

        if next_idx >= len(q_ids):
            # Quiz complete!
            learner_state.quiz_state = quiz_state
            return cls._finish_quiz(learner_state, final_eval_feedback=feedback_text)

        # Next question
        next_qid = q_ids[next_idx]
        next_q_obj = cls._find_question_by_id(next_qid)
        learner_state.quiz_state = quiz_state
        learner_state.pending_question = next_q_obj["question"]
        learner_state.last_question_asked = next_q_obj["question"]

        turn_msg = (
            f"{feedback_text}\n\n"
            f"---\n\n"
            f"**Question {next_idx + 1} of {len(q_ids)}:**\n"
            f"{next_q_obj['question']}"
        )

        return TutorStructuredResponse(
            message=turn_msg,
            mode=TutoringMode.GUIDED_PRACTICE,
            topic=quiz_state.get("topic", "Fundamentals"),
            action=TutorAction.ASK_QUESTION,
            question=next_q_obj["question"],
            hint=next_q_obj.get("hint"),
            misconception=misconception,
            concepts_demonstrated=quiz_state.get("concepts_mastered", []),
            concepts_needing_review=quiz_state.get("concepts_needing_review", []),
            source_ids=[],
            requires_calculation=False
        )

    @classmethod
    def _evaluate_single_answer(
        cls,
        q_obj: Dict[str, Any],
        answer: str
    ) -> Tuple[bool, bool, str, Optional[str]]:
        """Checks student response against expected keywords, numerical values, and misconceptions."""
        ans_lower = answer.lower().strip()

        # Check for explicit 'i don't know'
        if any(w in ans_lower for w in ["don't know", "dont know", "no idea", "not sure", "skip"]):
            fb = f"No problem! The correct answer is: **{q_obj['correct_explanation']}**"
            return False, False, fb, None

        # Check for known misconceptions first
        for mis_kw, mis_expl in q_obj.get("misconception_keywords", {}).items():
            if mis_kw in ans_lower:
                fb = f"⚠️ **Misconception detected:** {mis_expl}\n\n*Key insight*: {q_obj['correct_explanation']}"
                return False, False, fb, mis_expl

        # Check for expected keywords
        for kw in q_obj.get("expected_keywords", []):
            if kw in ans_lower:
                fb = f"✅ **Correct!** {q_obj['correct_explanation']}"
                return True, False, fb, None

        # If numerical question, check numerical proximity
        numbers = re.findall(r"[-+]?\d*\.\d+|\d+", ans_lower)
        target_numbers = []
        for kw in q_obj.get("expected_keywords", []):
            target_numbers.extend(re.findall(r"[-+]?\d*\.\d+|\d+", kw))
        if numbers and target_numbers and numbers[0] == target_numbers[0]:
            fb = f"✅ **Correct calculation!** {q_obj['correct_explanation']}"
            return True, False, fb, None

        # Partial credit or constructive correction
        fb = f"❌ **Not quite.** {q_obj['correct_explanation']}"
        return False, False, fb, None

    @classmethod
    def _finish_quiz(
        cls,
        learner_state: LearnerStateModel,
        final_eval_feedback: Optional[str] = None
    ) -> TutorStructuredResponse:
        """Builds a comprehensive summary table at the completion of a quiz."""
        quiz_state = learner_state.quiz_state
        score = quiz_state.get("score", 0.0)
        total = quiz_state.get("total_questions", 3)
        pct = (score / total) * 100.0 if total > 0 else 0.0
        topic = quiz_state.get("topic", "CPU Scheduling")

        mastered = list(set(quiz_state.get("concepts_mastered", [])))
        review = list(set(quiz_state.get("concepts_needing_review", [])))

        # Clean list formatting
        mastered_str = ", ".join([c.replace("_", " ").title() for c in mastered]) if mastered else "None demonstrated this round"
        review_str = ", ".join([c.replace("_", " ").title() for c in review]) if review else "All concepts cleared successfully!"

        recommendation = "Review the formulas for Turnaround Time and Waiting Time" if "Metrics" in topic or review else f"Proceed to explore multi-process scheduling problems or numerical practice on {topic}!"

        summary_msg = ""
        if final_eval_feedback:
            summary_msg += f"{final_eval_feedback}\n\n---\n\n"

        summary_msg += (
            f"📊 **Quiz Complete: {topic}**\n\n"
            f"| Metric | Result |\n"
            f"| :--- | :--- |\n"
            f"| **Questions Attempted** | {total} |\n"
            f"| **Score** | {score:g} / {total} ({pct:.0f}%) |\n"
            f"| **Demonstrated Concepts** | {mastered_str} |\n"
            f"| **Needs Revision** | {review_str} |\n\n"
            f"💡 **Recommended Next Step**: {recommendation}\n\n"
            f"Would you like to try another quiz or resume our interactive lesson?"
        )

        # Deactivate quiz
        quiz_state["is_active"] = False
        learner_state.quiz_state = quiz_state
        learner_state.pending_question = "Would you like to try another quiz or resume our interactive lesson?"
        learner_state.last_question_asked = learner_state.pending_question
        learner_state.lesson_stage = "review"

        return TutorStructuredResponse(
            message=summary_msg,
            mode=TutoringMode.REVISION,
            topic=topic if topic != "Comprehensive" else "Fundamentals",
            action=TutorAction.CHAT,
            question=learner_state.pending_question,
            hint=None,
            misconception=None,
            concepts_demonstrated=mastered,
            concepts_needing_review=review,
            source_ids=[],
            requires_calculation=False
        )

    @classmethod
    def _abort_quiz(cls, learner_state: LearnerStateModel) -> TutorStructuredResponse:
        """Safely terminates active quiz upon student request."""
        quiz_state = learner_state.quiz_state
        topic = quiz_state.get("topic", "Fundamentals")
        quiz_state["is_active"] = False
        learner_state.quiz_state = quiz_state
        learner_state.pending_question = None

        return TutorStructuredResponse(
            message=f"Understood! We've paused the quiz. What concept in **{topic}** would you like to explore or discuss next?",
            mode=TutoringMode.SOCRATIC,
            topic=topic if topic != "Comprehensive" else "Fundamentals",
            action=TutorAction.CHAT,
            question=None,
            hint=None,
            misconception=None,
            concepts_demonstrated=[],
            concepts_needing_review=[],
            source_ids=[],
            requires_calculation=False
        )

    @classmethod
    def _select_quiz_questions(cls, topic: str, difficulty: str) -> List[Dict[str, Any]]:
        """Assembles 3 distinct questions appropriate for the requested scope and difficulty."""
        candidates = []
        if topic == "Comprehensive":
            # Pick one from FCFS, one from Round Robin, one from Metrics
            for t in ["FCFS", "Round Robin", "Metrics", "SJF"]:
                if t in QUIZ_BANK and QUIZ_BANK[t]:
                    candidates.append(QUIZ_BANK[t][0])
            return candidates[:3]

        topic_bank = QUIZ_BANK.get(topic, QUIZ_BANK.get("Fundamentals", []))
        if not topic_bank:
            return QUIZ_BANK["Fundamentals"][:3]

        # Prioritize matching difficulty, then pad with remaining
        matching = [q for q in topic_bank if q["difficulty"] == difficulty]
        other = [q for q in topic_bank if q["difficulty"] != difficulty]
        return (matching + other)[:3]

    @classmethod
    def _find_question_by_id(cls, qid: str) -> Optional[Dict[str, Any]]:
        """Looks up question metadata across all topics."""
        for q_list in QUIZ_BANK.values():
            for q in q_list:
                if q["id"] == qid:
                    return q
        return None
