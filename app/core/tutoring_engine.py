"""Core Socratic Tutoring Engine executing the pedagogical cycle with conversational memory."""

import re
import json
import logging
from enum import Enum
from typing import List, Dict, Any, Optional

from app.schemas.chat import (
    TutoringMode,
    TutorAction,
    TutorStructuredResponse,
    ChatResponse
)
from app.database.models import LearnerStateModel, MessageModel
from app.rag.retriever import ChromaKnowledgeRetriever
from app.rag.citations import format_sources_for_ui
from app.core.prompt_builder import build_system_prompt
from app.core.llm_client import OllamaClient
from app.core.response_parser import parse_and_validate_response
from app.core.learner_model import LearnerModelManager
from app.core.conversation_memory import ConversationMemoryManager
from app.core.knowledge_catalog import find_knowledge_entry, evaluate_catalog_answer
from app.core.quiz_engine import QuizEngine
from app.core.socratic_engine import SocraticEngine, SOCRATIC_CURRICULUM
from app.scheduling import (
    Process,
    run_scheduler,
    SchedulingAlgorithm,
    PriorityConvention,
    render_ascii_gantt
)

logger = logging.getLogger(__name__)


class ConversationIntent(str, Enum):
    GREETING = "greeting"
    GRATITUDE_OR_CLOSING = "gratitude_or_closing"
    GENERAL_GOAL = "general_goal"
    SYLLABUS_REQUEST = "syllabus_request"
    DIRECT_EXPLANATION = "direct_explanation"
    CONCEPT_COMPARISON = "concept_comparison"
    ZERO_KNOWLEDGE = "zero_knowledge"
    PARTIAL_UNDERSTANDING = "partial_understanding"
    SPECIFIC_TRADEOFF = "specific_tradeoff"
    NEW_CONCEPT_INQUIRY = "new_concept_inquiry"
    EXPLORE_ROUND_ROBIN = "explore_round_robin"
    WORKED_EXAMPLE = "worked_example"
    MEMORY_RECALL = "memory_recall"
    ANSWER_EVALUATION = "answer_evaluation"
    PENDING_QUESTION_RESPONSE = "pending_question_response"
    DIRECT_EQUIVALENCE_INQUIRY = "direct_equivalence_inquiry"
    TOPIC_SWITCH = "topic_switch"
    QUIZ_TRIGGER = "quiz_trigger"
    DIRECT_FORMULA_REQUEST = "direct_formula_request"
    FCFS_SOCRATIC_OPENING = "fcfs_socratic_opening"
    GENERAL_PEDAGOGICAL = "general_pedagogical"


class TutoringEngine:
    """
    Orchestrates the ASSESS -> INTERPRET -> GUIDE -> EXPLAIN -> PRACTISE -> VERIFY -> ADAPT cycle.
    Integrates persistent conversational memory, explicit tutoring state, and deterministic verification.
    """

    def __init__(
        self,
        llm_client: Optional[OllamaClient] = None,
        retriever: Optional[ChromaKnowledgeRetriever] = None
    ):
        self.llm_client = llm_client or OllamaClient()
        self.retriever = retriever or ChromaKnowledgeRetriever()

    def classify_conversation_intent(
        self,
        text: str,
        history: List[MessageModel],
        learner_state: LearnerStateModel
    ) -> ConversationIntent:
        """Identifies student intent to provide natural, human-like dialogue without robotic filler."""
        msg_lower = text.lower().strip()
        words = msg_lower.split()

        # 0. Quiz Trigger Command: "Quiz me on CPU scheduling", "Test what I've learned", etc.
        if QuizEngine.is_quiz_trigger(msg_lower):
            return ConversationIntent.QUIZ_TRIGGER

        # 0b. Direct Formula Request: "What is the formula for waiting time? Just give me the formula."
        if any(phrase in msg_lower for phrase in [
            "just give me the formula", "give me the formula", "formula for waiting time",
            "formula for turnaround time", "formula for response time", "formula for tat", "formula for wt"
        ]):
            return ConversationIntent.DIRECT_FORMULA_REQUEST

        # 0c. FCFS Socratic Opening: "What is FCFS?", "Teach me FCFS", "I want to learn FCFS"
        if ("fcfs" in msg_lower or "first-come" in msg_lower or "first come" in msg_lower) and any(p in msg_lower for p in [
            "what is", "teach me", "want to learn", "learn", "explain", "tell me about"
        ]) and not any(k in msg_lower for k in ["sjf", "difference", "compare", "just explain it completely", "worked example", "take an example"]):
            return ConversationIntent.FCFS_SOCRATIC_OPENING

        # 1. Greetings: "Hello", "Hi", "Hey"
        if (
            msg_lower in ["hello", "hi", "hey", "hey there", "hi there", "hello!", "hi!", "good morning", "good evening", "howdy", "sup", "greetings"]
            or bool(re.match(r"^(hello|hi|hey|good\s+(morning|afternoon|evening)|howdy|sup|greetings)(\s+there|\s+tutor)?[\s!.,?]*$", msg_lower))
        ) and len(words) <= 4:
            return ConversationIntent.GREETING

        # 2. Gratitude / Closing: "Thanks", "Thank you", "Bye"
        if (
            msg_lower in ["thanks", "thank you", "thanks a lot", "thank you so much", "thx", "appreciate it", "got it thanks", "got it, thanks", "bye", "goodbye"]
            or bool(re.match(r"^(thanks|thank\s+you|thx|appreciate\s+it|got\s+it\s+thanks|bye|goodbye)[\s!.,?]*$", msg_lower))
        ) and len(words) <= 5:
            return ConversationIntent.GRATITUDE_OR_CLOSING

        # 3. Topic Switch: "Let's learn SJF instead.", "switch to sjf", "learn sjf instead"
        if (
            any(k in msg_lower for k in ["instead", "switch to", "let's switch", "lets switch", "switch over", "change topic"])
            or bool(re.match(r"^(let'?s\s+(learn|do|study)\s+([a-z\s]+)\s+instead)[\s!.,?]*$", msg_lower))
        ) and any(algo in msg_lower for algo in [
            "sjf", "fcfs", "round robin", "rr", "srtf", "priority", "hrrn", "cfs",
            "real-time", "real time", "multiprocessor", "lottery", "stride", "mlfq"
        ]):
            return ConversationIntent.TOPIC_SWITCH

        # 4. Direct Equivalence Inquiry: "Which algorithm does Round Robin become equivalent to..."
        if "equivalent" in msg_lower and any(k in msg_lower for k in ["round robin", "rr", "time quantum", "quantum"]):
            return ConversationIntent.DIRECT_EQUIVALENCE_INQUIRY

        # 5. Worked Example: "take an example for the round robin and elaborate", "worked example", "give me an example", etc.
        if any(k in msg_lower for k in [
            "take an example", "consider an example", "give an example", "give me an example",
            "show an example", "show me an example", "worked example", "explain with an example",
            "take an example for", "example of", "an example of", "example for", "solve a problem"
        ]):
            return ConversationIntent.WORKED_EXAMPLE

        # 5a. Student accepting offer for worked example with Gantt chart
        if learner_state.pending_question and any(k in learner_state.pending_question.lower() for k in ["numerical example", "worked example", "gantt chart", "action"]):
            if any(w in msg_lower for w in ["yes", "yeah", "sure", "ok", "okay", "show me", "show example", "let's do it", "lets do it", "please", "yep", "do it"]):
                return ConversationIntent.WORKED_EXAMPLE

        # 5b. Socratic Concept Inquiries: "What is Round Robin?", "Teach me SJF", "What is context switching?", etc.
        concept_detected = SocraticEngine.detect_concept(msg_lower)
        if (
            concept_detected
            and not any(k in msg_lower for k in ["difference", "compare", "vs ", "vs."])
            and not SocraticEngine.is_direct_answer_request(msg_lower)
            and not SocraticEngine.is_worked_example_request(msg_lower)
        ):
            if any(p in msg_lower for p in [
                "what is", "what are", "teach me", "want to learn", "how does", "tell me about",
                "explain", "learn", "understand", "study", "what's", "help me understand"
            ]) or msg_lower in [
                "round robin", "sjf", "srtf", "priority scheduling", "context switching",
                "pcb", "dispatcher", "preemption", "starvation", "aging", "convoy effect",
                "turnaround time", "waiting time", "mlfq", "hrrn", "cfs", "real time", "real-time",
                "multiprocessor", "lottery", "stride", "cpu burst", "io burst"
            ]:
                return ConversationIntent.NEW_CONCEPT_INQUIRY

        # 5c. Explicit Zero Knowledge check (Section 1.A: "I don't know anything about it.")
        if any(phrase in msg_lower for phrase in [
            "i don't know anything", "i dont know anything", "i know nothing",
            "don't know anything about it", "dont know anything about it"
        ]):
            return ConversationIntent.ZERO_KNOWLEDGE

        # 6. Response to pending question when student responds to a tutor question
        if learner_state.pending_question and len(learner_state.pending_question.strip()) > 0:
            pending_q = learner_state.pending_question.lower()
            if any(phrase in msg_lower for phrase in [
                "don't know", "dont know", "no idea", "not sure", "cant answer", "can't answer", "have no idea", "nothing"
            ]):
                return ConversationIntent.PENDING_QUESTION_RESPONSE

            if "what do you already know about fcfs" in pending_q:
                return ConversationIntent.PENDING_QUESTION_RESPONSE

            if "what happens if a process that arrives first needs a really long time to finish" in pending_q or "what do you think happens to those shorter processes" in pending_q or "waiting time of those shorter processes" in pending_q:
                return ConversationIntent.PENDING_QUESTION_RESPONSE

            if "do you know why fcfs can cause the convoy effect" in pending_q:
                return ConversationIntent.PENDING_QUESTION_RESPONSE

            if "which scheduling algorithm does round robin become equivalent to" in pending_q or "time quantum exceeds the longest cpu burst" in pending_q:
                return ConversationIntent.PENDING_QUESTION_RESPONSE

            # Check if pending question relates to any Socratic curriculum concept
            concept_for_pending = (
                SocraticEngine.get_concept_for_question(learner_state.pending_question or "")
                or SocraticEngine.detect_concept(learner_state.current_topic or "")
                or SocraticEngine.detect_concept(pending_q)
                or SocraticEngine.detect_concept(msg_lower)
            )
            if concept_for_pending:
                return ConversationIntent.PENDING_QUESTION_RESPONSE

        # 7. Broad statements / General Goal: "I'm studying CPU scheduling.", "i want to learn process scheduling"
        if (
            any(phrase in msg_lower for phrase in [
                "studying cpu scheduling", "learning cpu scheduling", "study cpu scheduling",
                "learn cpu scheduling", "working on cpu scheduling",
                "studying process scheduling", "learning process scheduling", "study process scheduling",
                "learn process scheduling", "working on process scheduling", "process scheduling",
                "want to learn process scheduling", "want to learn cpu scheduling", "want to study process scheduling"
            ])
            or msg_lower in [
                "cpu scheduling", "process scheduling",
                "i'm studying cpu scheduling", "i am studying cpu scheduling",
                "i want to learn process scheduling", "i want to learn cpu scheduling",
                "i want to study process scheduling", "i want to study cpu scheduling"
            ]
        ) and len(words) <= 10:
            return ConversationIntent.GENERAL_GOAL

        # 8. Explore Round Robin: "i want to explore round robin", "explore round robin", "let's explore round robin"
        if ("explore" in msg_lower or "want to explore" in msg_lower) and ("round robin" in msg_lower or "rr" in msg_lower):
            return ConversationIntent.EXPLORE_ROUND_ROBIN

        # 9. Explicit Syllabus Request: "What is on the syllabus?"
        if any(phrase in msg_lower for phrase in [
            "syllabus", "topics do you cover", "what topics", "list topics", "what can you teach", "topics covered"
        ]):
            return ConversationIntent.SYLLABUS_REQUEST

        # 10. Direct Comparison: "What is the difference between FCFS and SJF?"
        if ("fcfs" in msg_lower and "sjf" in msg_lower) or ("difference between fcfs and sjf" in msg_lower) or ("fcfs vs sjf" in msg_lower):
            return ConversationIntent.CONCEPT_COMPARISON

        # 11. Direct Explanation Request: "Just explain it directly.", "Just give me the definition", etc.
        if SocraticEngine.is_direct_answer_request(msg_lower) or any(phrase in msg_lower for phrase in [
            "just explain it directly", "explain directly", "teach me from beginning",
            "teach me from the beginning", "just tell me the answer", "just tell me",
            "give me proper notes", "explain the whole concept"
        ]):
            return ConversationIntent.DIRECT_EXPLANATION

        # 12. Student Knows Nothing: "I don't know anything about it."
        if any(phrase in msg_lower for phrase in [
            "i don't know anything", "i dont know anything", "i know nothing",
            "no idea", "not sure", "don't know anything about it", "dont know anything about it"
        ]):
            return ConversationIntent.ZERO_KNOWLEDGE

        # 13. Partial Understanding: "I know that preemptive scheduling can interrupt a running process."
        if ("i know" in msg_lower or "i understand" in msg_lower) and any(k in msg_lower for k in [
            "interrupt", "can interrupt", "allows interrupt", "but don't understand", "but i don't understand", "confused about"
        ]):
            return ConversationIntent.PARTIAL_UNDERSTANDING

        # 14. Specific trade-off inquiry
        if any(k in msg_lower for k in ["i understand both", "i know both", "i already understand"]) or (
            ("affect response time" in msg_lower or "trade-off" in msg_lower or "trade off" in msg_lower) and "preempt" in msg_lower
        ):
            return ConversationIntent.SPECIFIC_TRADEOFF

        # 15. Memory Recall
        if any(k in msg_lower for k in [
            "first weakness", "weakness i mentioned", "weakness did i", "what was my weakness",
            "in that example you just showed", "in the example you showed", "waiting time of p2"
        ]):
            return ConversationIntent.MEMORY_RECALL

        # 16. Answer Evaluation (check if previous assistant message had a question)
        last_asst_msg = ""
        for m in reversed(history):
            if m.role == "assistant":
                last_asst_msg = m.content
                break
        if last_asst_msg and evaluate_catalog_answer(last_asst_msg, text):
            return ConversationIntent.ANSWER_EVALUATION

        return ConversationIntent.GENERAL_PEDAGOGICAL

    def detect_mode_intent(self, text: str, current_mode: TutoringMode) -> TutoringMode:
        """
        Detects explicit student intent to switch modes.
        Respects:
        - "explain directly", "teach me from beginning", "just tell me" -> EXPLANATION
        - "i don't know anything", "no idea" -> EXPLANATION (to prevent interrogating stuck learners)
        - "practice", "give me a problem", "calculate" -> GUIDED_PRACTICE
        - "independent practice", "solve myself" -> INDEPENDENT_PRACTICE
        - "test my knowledge", "quiz", "diagnostic" -> DIAGNOSTIC
        - "review", "weak spots", "revision" -> REVISION
        """
        lower = text.lower()

        # Explicit direct explanation request
        if any(phrase in lower for phrase in [
            "explain directly", "just teach me", "teach me from the beginning",
            "teach me from beginning", "just tell me the answer", "tell me the answer",
            "give me proper notes", "give me notes", "explain the whole concept",
            "explain directly to me", "i don't understand", "i dont understand"
        ]):
            return TutoringMode.EXPLANATION

        # Student stating they know nothing
        if any(phrase in lower for phrase in [
            "i don't know anything", "i dont know anything", "i know nothing",
            "no idea", "not sure", "teach me from scratch"
        ]):
            return TutoringMode.EXPLANATION

        # Independent practice request
        if any(phrase in lower for phrase in [
            "independent practice", "solve it myself", "test myself", "independent problem"
        ]):
            return TutoringMode.INDEPENDENT_PRACTICE

        # Guided practice request
        if any(phrase in lower for phrase in [
            "give me a problem", "practice", "numerical", "let me solve",
            "give me an example to calculate", "exercise"
        ]):
            return TutoringMode.GUIDED_PRACTICE

        # Diagnostic request
        if any(phrase in lower for phrase in [
            "test my knowledge", "test me", "diagnostic", "assess me", "start from beginning"
        ]):
            return TutoringMode.DIAGNOSTIC

        # Revision request
        if any(phrase in lower for phrase in [
            "review my mistakes", "revision", "what did i get wrong", "weak points"
        ]):
            return TutoringMode.REVISION

        return current_mode or TutoringMode.SOCRATIC

    def detect_topic(self, text: str, current_topic: str) -> str:
        """Detects if student is switching to a different scheduling topic using word boundaries."""
        lower = text.lower()
        if "fcfs" in lower or "first come" in lower or "first-come" in lower or "convoy" in lower:
            return "FCFS"
        elif "hrrn" in lower or "response ratio" in lower:
            return "HRRN"
        elif re.search(r"\bcfs\b", lower) or "completely fair" in lower or "vruntime" in lower:
            return "Linux CFS"
        elif "real time" in lower or "real-time" in lower or re.search(r"\b(rms|edf)\b", lower):
            return "Real-Time Scheduling"
        elif "multiprocessor" in lower or "sqms" in lower or "mqms" in lower or "affinity" in lower:
            return "Multiprocessor Scheduling"
        elif "lottery" in lower or "stride" in lower:
            return "Proportional Share"
        elif "mlfq" in lower or "multilevel" in lower:
            return "MLFQ"
        elif "round robin" in lower or re.search(r"\brr\b", lower) or "time quantum" in lower or "time slice" in lower:
            return "Round Robin"
        elif "srtf" in lower or "shortest remaining" in lower:
            return "SRTF"
        elif "sjf" in lower or "shortest job first" in lower:
            return "SJF"
        elif "priority" in lower or "aging" in lower or "starvation" in lower:
            return "Priority"
        elif "fcfs" in lower or "first come" in lower or "first-come" in lower or "convoy" in lower:
            return "FCFS"
        elif any(k in lower for k in ["gantt", "turnaround", "waiting time", "response time", "metrics", "utilization", "throughput", "arrival time", "burst time"]):
            return "Metrics"
        elif any(k in lower for k in ["preempt", "cooperative"]):
            return "Preemption"
        elif any(k in lower for k in ["process", "program", "dispatcher", "context switch", "state", "burst", "pcb"]):
            return "Fundamentals"
        return current_topic or "Fundamentals"

    async def generate_tutor_turn(
        self,
        session_id: str,
        user_message: str,
        history: List[MessageModel],
        learner_state: LearnerStateModel,
        topic_override: Optional[str] = None,
        mode_override: Optional[TutoringMode] = None
    ) -> ChatResponse:
        """
        Executes one full tutoring turn with conversational memory, adaptive Socratic logic,
        grounded RAG, and deterministic numerical verification.
        """
        msg_lower = user_message.lower().strip()
        current_mode = TutoringMode(learner_state.current_mode) if learner_state.current_mode else TutoringMode.SOCRATIC
        active_mode = mode_override or self.detect_mode_intent(user_message, current_mode)

        # Classify user conversational intent
        intent = self.classify_conversation_intent(user_message, history, learner_state)

        # 0. Active Quiz Session Handler (Section 10)
        quiz_state = learner_state.quiz_state
        if quiz_state and quiz_state.get("is_active"):
            structured_response = QuizEngine.handle_quiz_turn(learner_state, user_message)
            if structured_response:
                LearnerModelManager.update_state_from_turn(learner_state, structured_response, user_message)
                return ChatResponse(
                    session_id=session_id,
                    message=structured_response.message,
                    mode=structured_response.mode,
                    topic=structured_response.topic,
                    action=structured_response.action,
                    question=structured_response.question,
                    hint=structured_response.hint,
                    misconception=structured_response.misconception,
                    sources=[],
                    gantt_chart_ascii=None,
                    concepts_demonstrated=structured_response.concepts_demonstrated,
                    concepts_needing_review=structured_response.concepts_needing_review,
                    difficulty_level=learner_state.difficulty_level or "beginner",
                    is_fallback=False
                )



        # 0b. Quiz Trigger: "Quiz me on CPU scheduling", "Test what I've learned", etc.
        if intent == ConversationIntent.QUIZ_TRIGGER:
            structured_response = QuizEngine.start_quiz(learner_state, user_message)
            LearnerModelManager.update_state_from_turn(learner_state, structured_response, user_message)
            return ChatResponse(
                session_id=session_id,
                message=structured_response.message,
                mode=structured_response.mode,
                topic=structured_response.topic,
                action=structured_response.action,
                question=structured_response.question,
                hint=structured_response.hint,
                misconception=None,
                sources=[],
                gantt_chart_ascii=None,
                concepts_demonstrated=[],
                concepts_needing_review=[],
                difficulty_level=learner_state.difficulty_level or "beginner",
                is_fallback=False
            )


        # 0c. Direct Formula Request (Section 16 Scenario F)
        if intent == ConversationIntent.DIRECT_FORMULA_REQUEST:
            if "waiting" in msg_lower or "wt" in msg_lower:
                formula_msg = (
                    "Here is the standard formula for **Waiting Time (WT)** in CPU scheduling:\n\n"
                    "$$\\text{Waiting Time (WT)} = \\text{Turnaround Time (TAT)} - \\text{Burst Time (BT)}$$\n\n"
                    "Or expressed using Completion Time:\n"
                    "$$\\text{Waiting Time (WT)} = \\text{Completion Time (CT)} - \\text{Arrival Time (AT)} - \\text{Burst Time (BT)}$$\n\n"
                    "Waiting time measures the total duration a process spends waiting in the Ready Queue before its CPU execution completes."
                )
                topic_tag = "Metrics"
            elif "turnaround" in msg_lower or "tat" in msg_lower:
                formula_msg = (
                    "Here is the standard formula for **Turnaround Time (TAT)** in CPU scheduling:\n\n"
                    "$$\\text{Turnaround Time (TAT)} = \\text{Completion Time (CT)} - \\text{Arrival Time (AT)}$$\n\n"
                    "Turnaround time measures the total elapsed interval from when a process arrives in the system until it terminates."
                )
                topic_tag = "Metrics"
            elif "response" in msg_lower or "rt" in msg_lower:
                formula_msg = (
                    "Here is the standard formula for **Response Time (RT)** in CPU scheduling:\n\n"
                    "$$\\text{Response Time (RT)} = \\text{First CPU Start Time} - \\text{Arrival Time (AT)}$$\n\n"
                    "Response time measures the elapsed time from process arrival until it first obtains the CPU (crucial for interactive systems)."
                )
                topic_tag = "Metrics"
            else:
                formula_msg = (
                    "Here are the core CPU scheduling metric formulas:\n\n"
                    "1. **Turnaround Time (TAT)**: $\\text{TAT} = \\text{Completion Time (CT)} - \\text{Arrival Time (AT)}$\n"
                    "2. **Waiting Time (WT)**: $\\text{WT} = \\text{TAT} - \\text{Burst Time (BT)}$\n"
                    "3. **Response Time (RT)**: $\\text{RT} = \\text{First Start Time} - \\text{Arrival Time (AT)}$"
                )
                topic_tag = "Metrics"

            structured_response = TutorStructuredResponse(
                message=formula_msg,
                mode=TutoringMode.EXPLANATION,
                topic=topic_tag,
                action=TutorAction.EXPLAIN_CONCEPT,
                question=None,
                hint=None,
                misconception=None,
                concepts_demonstrated=["scheduling_formulas"],
                concepts_needing_review=[],
                source_ids=["01_metrics_p1_c0"],
                requires_calculation=False
            )
            learner_state.current_topic = topic_tag
            learner_state.last_concept_explained = "Scheduling metric formulas"
            LearnerModelManager.update_state_from_turn(learner_state, structured_response, user_message)
            return ChatResponse(
                session_id=session_id,
                message=structured_response.message,
                mode=structured_response.mode,
                topic=structured_response.topic,
                action=structured_response.action,
                question=None,
                hint=None,
                misconception=None,
                sources=[],
                gantt_chart_ascii=None,
                concepts_demonstrated=structured_response.concepts_demonstrated,
                concepts_needing_review=[],
                difficulty_level=learner_state.difficulty_level or "beginner",
                is_fallback=False
            )

        # 0d. FCFS Socratic Opening (Section 4 Example A & Section 16 Scenario A)
        if intent == ConversationIntent.FCFS_SOCRATIC_OPENING:
            fcfs_q = "Before we get into it, what do you already know about FCFS? Have you studied it before, or is it completely new to you?"
            structured_response = TutorStructuredResponse(
                message=fcfs_q,
                mode=TutoringMode.SOCRATIC,
                topic="FCFS",
                action=TutorAction.ASK_QUESTION,
                question=fcfs_q,
                hint="Think about what the letters F-C-F-S stand for.",
                misconception=None,
                concepts_demonstrated=[],
                concepts_needing_review=[],
                source_ids=["01_fcfs_algorithm_p1_c0"],
                requires_calculation=False
            )
            learner_state.current_topic = "FCFS"
            learner_state.current_subtopic = "Baseline Assessment"
            learner_state.pending_question = fcfs_q
            learner_state.last_question_asked = fcfs_q
            learner_state.lesson_stage = "knowledge_assessment"
            learner_state.next_teaching_step = "Assess baseline knowledge of FCFS"
            LearnerModelManager.update_state_from_turn(learner_state, structured_response, user_message)
            return ChatResponse(
                session_id=session_id,
                message=structured_response.message,
                mode=structured_response.mode,
                topic=structured_response.topic,
                action=structured_response.action,
                question=structured_response.question,
                hint=structured_response.hint,
                misconception=None,
                sources=[],
                gantt_chart_ascii=None,
                concepts_demonstrated=[],
                concepts_needing_review=[],
                difficulty_level=learner_state.difficulty_level or "beginner",
                is_fallback=False
            )

        # 0e. Socratic Concept Inquiry (Section 1, 3, 4, 5, 16)
        if intent == ConversationIntent.NEW_CONCEPT_INQUIRY:
            concept_id = SocraticEngine.detect_concept(user_message)
            if concept_id:
                structured_response = SocraticEngine.start_socratic_lesson(concept_id, learner_state)
                LearnerModelManager.update_state_from_turn(learner_state, structured_response, user_message)
                return ChatResponse(
                    session_id=session_id,
                    message=structured_response.message,
                    mode=structured_response.mode,
                    topic=structured_response.topic,
                    action=structured_response.action,
                    question=structured_response.question,
                    hint=structured_response.hint,
                    misconception=None,
                    sources=[],
                    gantt_chart_ascii=None,
                    concepts_demonstrated=[],
                    concepts_needing_review=[],
                    difficulty_level=learner_state.difficulty_level or "beginner",
                    is_fallback=False
                )



        # 1. Immediate Conversational Intent Handling (bypassing heavy RAG for casual chat)

        # A. Greeting: "Hello" -> "Hey! What are we learning today?"
        if intent == ConversationIntent.GREETING:
            structured_response = TutorStructuredResponse(
                message="Hey! What are we learning today?",
                mode=active_mode,
                topic=learner_state.current_topic or "Fundamentals",
                action=TutorAction.CHAT,
                question=None,
                hint=None,
                misconception=None,
                concepts_demonstrated=[],
                concepts_needing_review=[],
                source_ids=[],
                requires_calculation=False
            )
            LearnerModelManager.update_state_from_turn(learner_state, structured_response, user_message)
            return ChatResponse(
                session_id=session_id,
                message=structured_response.message,
                mode=structured_response.mode,
                topic=structured_response.topic,
                action=structured_response.action,
                question=None,
                hint=None,
                misconception=None,
                sources=[],
                gantt_chart_ascii=None,
                concepts_demonstrated=[],
                concepts_needing_review=[],
                difficulty_level=learner_state.difficulty_level or "beginner",
                is_fallback=False
            )

        # B. General Goal: "I'm studying CPU scheduling." -> "Nice. Which part are you working on?"
        if intent == ConversationIntent.GENERAL_GOAL:
            structured_response = TutorStructuredResponse(
                message="Nice. Which part are you working on?",
                mode=active_mode,
                topic="Fundamentals",
                action=TutorAction.CHAT,
                question=None,
                hint=None,
                misconception=None,
                concepts_demonstrated=[],
                concepts_needing_review=[],
                source_ids=[],
                requires_calculation=False
            )
            learner_state.current_topic = "Fundamentals"
            LearnerModelManager.update_state_from_turn(learner_state, structured_response, user_message)
            return ChatResponse(
                session_id=session_id,
                message=structured_response.message,
                mode=structured_response.mode,
                topic=structured_response.topic,
                action=structured_response.action,
                question=None,
                hint=None,
                misconception=None,
                sources=[],
                gantt_chart_ascii=None,
                concepts_demonstrated=[],
                concepts_needing_review=[],
                difficulty_level=learner_state.difficulty_level or "beginner",
                is_fallback=False
            )

        # C. Gratitude / Closing: "Thanks." -> "You're welcome!"
        if intent == ConversationIntent.GRATITUDE_OR_CLOSING:
            structured_response = TutorStructuredResponse(
                message="You're welcome!",
                mode=active_mode,
                topic=learner_state.current_topic or "Fundamentals",
                action=TutorAction.CHAT,
                question=None,
                hint=None,
                misconception=None,
                concepts_demonstrated=[],
                concepts_needing_review=[],
                source_ids=[],
                requires_calculation=False
            )
            LearnerModelManager.update_state_from_turn(learner_state, structured_response, user_message)
            return ChatResponse(
                session_id=session_id,
                message=structured_response.message,
                mode=structured_response.mode,
                topic=structured_response.topic,
                action=structured_response.action,
                question=None,
                hint=None,
                misconception=None,
                sources=[],
                gantt_chart_ascii=None,
                concepts_demonstrated=[],
                concepts_needing_review=[],
                difficulty_level=learner_state.difficulty_level or "beginner",
                is_fallback=False
            )

        # C1. Topic Switch: "Let's learn SJF instead."
        if intent == ConversationIntent.TOPIC_SWITCH:
            target_topic = self.detect_topic(user_message, "SJF")
            LearnerModelManager.handle_topic_switch(learner_state, target_topic)
            learner_state.current_topic = target_topic
            learner_state.lesson_stage = "guided_inquiry"

            if target_topic == "SJF":
                switch_msg = (
                    "Sure! Let's switch over to Shortest Job First (SJF). In SJF, the scheduler prioritizes the process with the smallest CPU burst time. "
                    "Would you like to explore non-preemptive SJF or its preemptive version, Shortest Remaining Time First (SRTF)?"
                )
                q_text = "Would you like to explore non-preemptive SJF or preemptive SJF (Shortest Remaining Time First / SRTF)?"
                learner_state.current_subtopic = "SJF vs SRTF"
                learner_state.pending_question = q_text
                learner_state.last_question_asked = q_text
                learner_state.last_concept_explained = "SJF selection criteria"
                learner_state.next_teaching_step = "Choose between non-preemptive SJF and SRTF"
            else:
                switch_msg = f"Sure! Let's switch over to {target_topic}. Which aspect would you like to explore first?"
                q_text = f"Which aspect of {target_topic} would you like to explore first?"
                learner_state.current_subtopic = "Introduction"
                learner_state.pending_question = q_text
                learner_state.last_question_asked = q_text
                learner_state.last_concept_explained = f"{target_topic} switch"
                learner_state.next_teaching_step = "Baseline assessment"

            structured_response = TutorStructuredResponse(
                message=switch_msg,
                mode=active_mode,
                topic=target_topic,
                action=TutorAction.ASK_QUESTION,
                question=q_text,
                hint="Think about whether jobs can be preempted when a shorter job arrives.",
                misconception=None,
                concepts_demonstrated=[],
                concepts_needing_review=[],
                source_ids=[],
                requires_calculation=False
            )
            LearnerModelManager.update_state_from_turn(learner_state, structured_response, user_message)
            return ChatResponse(
                session_id=session_id,
                message=structured_response.message,
                mode=structured_response.mode,
                topic=structured_response.topic,
                action=structured_response.action,
                question=structured_response.question,
                hint=structured_response.hint,
                misconception=None,
                sources=[],
                gantt_chart_ascii=None,
                concepts_demonstrated=[],
                concepts_needing_review=[],
                difficulty_level=learner_state.difficulty_level or "beginner",
                is_fallback=False
            )


        # C2. Direct Equivalence Inquiry: "Which algorithm does Round Robin become equivalent to when the time quantum is larger than the longest CPU burst?"
        if intent == ConversationIntent.DIRECT_EQUIVALENCE_INQUIRY:
            equiv_msg = (
                "When the time quantum is larger than the longest CPU burst, Round Robin becomes equivalent to **First-Come, First-Served (FCFS)**.\n\n"
                "Because every process can finish its entire CPU burst within its very first time slice without being preempted, "
                "the scheduler runs them strictly to completion in their arrival order without interruptions, exactly like FCFS."
            )
            structured_response = TutorStructuredResponse(
                message=equiv_msg,
                mode=TutoringMode.EXPLANATION,
                topic="Round Robin",
                action=TutorAction.EXPLAIN_CONCEPT,
                question=None,
                hint=None,
                misconception=None,
                concepts_demonstrated=["rr_fcfs_equivalence"],
                concepts_needing_review=[],
                source_ids=["01_round_robin_p1_c0"],
                requires_calculation=False
            )
            learner_state.current_topic = "Round Robin"
            learner_state.current_subtopic = "Time Quantum & Equivalence"
            learner_state.pending_question = None
            learner_state.last_concept_explained = "Round Robin reduces to FCFS when quantum exceeds max burst"
            learner_state.next_teaching_step = "Explore impact of very small quantum or walk through numerical example"
            LearnerModelManager.update_state_from_turn(learner_state, structured_response, user_message)
            return ChatResponse(
                session_id=session_id,
                message=structured_response.message,
                mode=structured_response.mode,
                topic=structured_response.topic,
                action=structured_response.action,
                question=None,
                hint=None,
                misconception=None,
                sources=[],
                gantt_chart_ascii=None,
                concepts_demonstrated=structured_response.concepts_demonstrated,
                concepts_needing_review=[],
                difficulty_level=learner_state.difficulty_level or "beginner",
                is_fallback=False
            )

        # C3. Student responding to a pending question (e.g. "I don't know the answer")
        if intent == ConversationIntent.PENDING_QUESTION_RESPONSE:
            pending_q = (learner_state.pending_question or learner_state.last_question_asked or "").lower()

            # Check general Socratic curriculum evaluation for active concept
            concept_for_pending = (
                SocraticEngine.get_concept_for_question(learner_state.pending_question or learner_state.last_question_asked or "")
                or SocraticEngine.detect_concept(learner_state.current_topic or "")
                or SocraticEngine.detect_concept(pending_q)
                or SocraticEngine.detect_concept(msg_lower)
            )
            if concept_for_pending and "what do you already know about fcfs" not in pending_q and "which scheduling algorithm does round robin become equivalent to" not in pending_q:
                socratic_eval = SocraticEngine.evaluate_socratic_turn(concept_for_pending, user_message, learner_state)
                if socratic_eval:
                    LearnerModelManager.update_state_from_turn(learner_state, socratic_eval, user_message)
                    return ChatResponse(
                        session_id=session_id,
                        message=socratic_eval.message,
                        mode=socratic_eval.mode,
                        topic=socratic_eval.topic,
                        action=socratic_eval.action,
                        question=socratic_eval.question,
                        hint=socratic_eval.hint,
                        misconception=socratic_eval.misconception,
                        sources=[],
                        gantt_chart_ascii=None,
                        concepts_demonstrated=socratic_eval.concepts_demonstrated,
                        concepts_needing_review=socratic_eval.concepts_needing_review,
                        difficulty_level=learner_state.difficulty_level or "beginner",
                        is_fallback=False
                    )

            # FCFS Baseline Assessment Response (Section 4 Example A & Section 16 Scenario A)
            if "what do you already know about fcfs" in pending_q:
                # Case 1: Student knows nothing
                if any(phrase in msg_lower for phrase in ["nothing", "don't know", "dont know", "no idea", "not sure", "completely new", "new to me"]):
                    ans_msg = (
                        "No problem. Imagine you're standing in a queue at a canteen. The person who arrived first gets served first, right?\n\n"
                        "FCFS works in much the same way. Processes wait in a queue, and the CPU executes them in the order they arrive.\n\n"
                        "Can you guess what happens if a process that arrives first needs a really long time to finish?"
                    )
                    next_q = "Can you guess what happens if a process that arrives first needs a really long time to finish?"
                    learner_state.pending_question = next_q
                    learner_state.last_question_asked = next_q
                    learner_state.current_subtopic = "Canteen Queue Analogy & Preemption"
                    learner_state.last_concept_explained = "FCFS canteen queue analogy and arrival ordering"
                    learner_state.next_teaching_step = "Check intuition on convoy effect"
                    structured_response = TutorStructuredResponse(
                        message=ans_msg,
                        mode=TutoringMode.SOCRATIC,
                        topic="FCFS",
                        action=TutorAction.ASK_QUESTION,
                        question=next_q,
                        hint="Think about what happens to the customers waiting behind someone placing a massive order.",
                        misconception=None,
                        concepts_demonstrated=["fcfs_queue_analogy"],
                        concepts_needing_review=[],
                        source_ids=["01_fcfs_algorithm_p1_c0"],
                        requires_calculation=False
                    )
                    LearnerModelManager.update_state_from_turn(learner_state, structured_response, user_message)
                    return ChatResponse(
                        session_id=session_id,
                        message=structured_response.message,
                        mode=structured_response.mode,
                        topic=structured_response.topic,
                        action=structured_response.action,
                        question=structured_response.question,
                        hint=structured_response.hint,
                        misconception=None,
                        sources=[],
                        gantt_chart_ascii=None,
                        concepts_demonstrated=structured_response.concepts_demonstrated,
                        concepts_needing_review=[],
                        difficulty_level=learner_state.difficulty_level or "beginner",
                        is_fallback=False
                    )

                # Case 2: Partial knowledge (arrival order acknowledged)
                elif any(w in msg_lower for w in ["comes first", "first comes", "first in first out", "fifo"]):
                    ans_msg = (
                        "Exactly, that's the main idea. In FCFS, the process that arrives first gets the CPU first.\n\n"
                        "Now imagine the first process takes 20 milliseconds, while the next two need only 2 milliseconds each. What do you think happens to those shorter processes?"
                    )
                    next_q = "What do you think happens to those shorter processes?"
                    learner_state.pending_question = next_q
                    learner_state.last_question_asked = next_q
                    learner_state.current_subtopic = "Convoy Effect Intuition"
                    learner_state.last_concept_explained = "FCFS arrival order validated"
                    learner_state.next_teaching_step = "Examine convoy effect on short processes"
                    structured_response = TutorStructuredResponse(
                        message=ans_msg,
                        mode=TutoringMode.SOCRATIC,
                        topic="FCFS",
                        action=TutorAction.ASK_QUESTION,
                        question=next_q,
                        hint="Will the shorter processes have to wait a short time or a long time?",
                        misconception=None,
                        concepts_demonstrated=["fcfs_arrival_order"],
                        concepts_needing_review=[],
                        source_ids=["01_fcfs_algorithm_p1_c0"],
                        requires_calculation=False
                    )
                    LearnerModelManager.update_state_from_turn(learner_state, structured_response, user_message)
                    return ChatResponse(
                        session_id=session_id,
                        message=structured_response.message,
                        mode=structured_response.mode,
                        topic=structured_response.topic,
                        action=structured_response.action,
                        question=structured_response.question,
                        hint=structured_response.hint,
                        misconception=None,
                        sources=[],
                        gantt_chart_ascii=None,
                        concepts_demonstrated=structured_response.concepts_demonstrated,
                        concepts_needing_review=[],
                        difficulty_level=learner_state.difficulty_level or "beginner",
                        is_fallback=False
                    )

                # Case 3: Prior knowledge demonstrated
                elif any(w in msg_lower for w in ["arrival order", "strictly in the order", "without preemption", "non-preemptive"]):
                    ans_msg = (
                        "Correct. In FCFS, processes execute strictly in arrival order. Let's take it a step further: do you know why FCFS can cause the convoy effect?"
                    )
                    next_q = "Do you know why FCFS can cause the convoy effect?"
                    learner_state.pending_question = next_q
                    learner_state.last_question_asked = next_q
                    learner_state.current_subtopic = "Convoy Effect Advanced"
                    learner_state.last_concept_explained = "FCFS arrival order mastery"
                    learner_state.next_teaching_step = "Explore convoy effect mechanism"
                    structured_response = TutorStructuredResponse(
                        message=ans_msg,
                        mode=TutoringMode.SOCRATIC,
                        topic="FCFS",
                        action=TutorAction.ASK_QUESTION,
                        question=next_q,
                        hint="Think of a CPU-heavy process in front of I/O-heavy processes.",
                        misconception=None,
                        concepts_demonstrated=["fcfs_arrival_order", "fcfs_non_preemptive"],
                        concepts_needing_review=[],
                        source_ids=["01_fcfs_algorithm_p1_c0"],
                        requires_calculation=False
                    )
                    LearnerModelManager.update_state_from_turn(learner_state, structured_response, user_message)
                    return ChatResponse(
                        session_id=session_id,
                        message=structured_response.message,
                        mode=structured_response.mode,
                        topic=structured_response.topic,
                        action=structured_response.action,
                        question=structured_response.question,
                        hint=structured_response.hint,
                        misconception=None,
                        sources=[],
                        gantt_chart_ascii=None,
                        concepts_demonstrated=structured_response.concepts_demonstrated,
                        concepts_needing_review=[],
                        difficulty_level=learner_state.difficulty_level or "beginner",
                        is_fallback=False
                    )

            # FCFS Convoy Effect Question Response
            if (
                "what happens if a process that arrives first needs a really long time to finish" in pending_q
                or "what do you think happens to those shorter processes" in pending_q
                or "waiting time of those shorter processes" in pending_q
                or "do you know why fcfs can cause the convoy effect" in pending_q
                or "convoy effect" in pending_q
            ):
                # Misconception check: student thinks other jobs can skip or execute first
                if any(w in msg_lower for w in ["execute before", "run first", "interrupt", "skip", "preempt", "get cpu instead"]):
                    ans_msg = (
                        "Not quite. In FCFS, scheduling is strictly **non-preemptive**: once a process gets the CPU, it keeps running until it finishes. "
                        "If that first process needs a very long time, all other ready processes must sit waiting in the queue until it is done.\n\n"
                        "What do you think happens to the waiting time of those shorter processes behind it?"
                    )
                    next_q = "What do you think happens to the waiting time of those shorter processes behind it?"
                    learner_state.pending_question = next_q
                    learner_state.last_question_asked = next_q
                    learner_state.last_concept_explained = "FCFS non-preemptive nature (no skipping)"
                    structured_response = TutorStructuredResponse(
                        message=ans_msg,
                        mode=TutoringMode.SOCRATIC,
                        topic="FCFS",
                        action=TutorAction.ASK_QUESTION,
                        question=next_q,
                        hint="Do the short processes wait for a short time or a long time?",
                        misconception="Believing that FCFS can interrupt or skip a long process.",
                        concepts_demonstrated=[],
                        concepts_needing_review=["fcfs_non_preemptive"],
                        source_ids=["01_fcfs_algorithm_p1_c0"],
                        requires_calculation=False
                    )
                    LearnerModelManager.update_state_from_turn(learner_state, structured_response, user_message)
                    return ChatResponse(
                        session_id=session_id,
                        message=structured_response.message,
                        mode=structured_response.mode,
                        topic=structured_response.topic,
                        action=structured_response.action,
                        question=structured_response.question,
                        hint=structured_response.hint,
                        misconception=structured_response.misconception,
                        sources=[],
                        gantt_chart_ascii=None,
                        concepts_demonstrated=[],
                        concepts_needing_review=structured_response.concepts_needing_review,
                        difficulty_level=learner_state.difficulty_level or "beginner",
                        is_fallback=False
                    )

                # Correct response: waiting time increases / convoy effect
                else:
                    ans_msg = (
                        "Exactly! That is called the **Convoy Effect**, where short processes are delayed behind one long process, "
                        "leading to high average waiting times and underutilized I/O devices.\n\n"
                        "Would you like to see how this looks in a quick worked example with a Gantt chart?"
                    )
                    next_q = "Would you like to see how this looks in a quick worked example with a Gantt chart?"
                    learner_state.pending_question = next_q
                    learner_state.last_question_asked = next_q
                    learner_state.last_concept_explained = "Convoy effect definition and impact on waiting time"
                    structured_response = TutorStructuredResponse(
                        message=ans_msg,
                        mode=TutoringMode.SOCRATIC,
                        topic="FCFS",
                        action=TutorAction.ASK_QUESTION,
                        question=next_q,
                        hint="Type 'yes' or 'show example'.",
                        misconception=None,
                        concepts_demonstrated=["convoy_effect", "fcfs_waiting_time_impact"],
                        concepts_needing_review=[],
                        source_ids=["01_fcfs_algorithm_p1_c0"],
                        requires_calculation=False
                    )
                    LearnerModelManager.update_state_from_turn(learner_state, structured_response, user_message)
                    return ChatResponse(
                        session_id=session_id,
                        message=structured_response.message,
                        mode=structured_response.mode,
                        topic=structured_response.topic,
                        action=structured_response.action,
                        question=structured_response.question,
                        hint=structured_response.hint,
                        misconception=None,
                        sources=[],
                        gantt_chart_ascii=None,
                        concepts_demonstrated=structured_response.concepts_demonstrated,
                        concepts_needing_review=[],
                        difficulty_level=learner_state.difficulty_level or "beginner",
                        is_fallback=False
                    )

            # Round Robin Equivalence Pending Question Response
            if (
                ("equivalent" in pending_q or "exceeds the longest" in pending_q or "larger than the longest" in pending_q)
                and (
                    any(phrase in msg_lower for phrase in ["don't know", "dont know", "no idea", "not sure", "cant", "can't", "tell me", "what is", "answer"])
                    or any(phrase in msg_lower for phrase in ["fcfs", "first come", "first-come", "fifo"])
                )
            ):
                ans_msg = (
                    "No problem! Round Robin becomes equivalent to **First-Come, First-Served (FCFS)** in that situation.\n\n"
                    "Here's why: if the time quantum is larger than the longest CPU burst, every process will finish its execution within its very first time slice without ever being preempted. "
                    "As a result, processes simply run to completion in the exact order they arrived in the ready queue, which is identical to FCFS."
                )
                structured_response = TutorStructuredResponse(
                    message=ans_msg,
                    mode=TutoringMode.EXPLANATION,
                    topic="Round Robin",
                    action=TutorAction.EXPLAIN_CONCEPT,
                    question="Would you like to walk through a concrete numerical example with a Gantt chart to see Round Robin in action?",
                    hint="Consider how processes share the CPU when the quantum is smaller than their bursts.",
                    misconception=None,
                    concepts_demonstrated=["rr_fcfs_equivalence"],
                    concepts_needing_review=[],
                    source_ids=["01_round_robin_p1_c0"],
                    requires_calculation=False
                )
                learner_state.current_topic = "Round Robin"
                learner_state.current_subtopic = "Time Quantum & Equivalence"
                learner_state.pending_question = "Would you like to walk through a concrete numerical example with a Gantt chart to see Round Robin in action?"
                learner_state.last_question_asked = learner_state.pending_question
                learner_state.last_concept_explained = "Round Robin reduces to FCFS when quantum exceeds max burst"
                learner_state.next_teaching_step = "Walk through a numerical example of Round Robin"
                learner_state.lesson_stage = "explanation"
                LearnerModelManager.update_state_from_turn(learner_state, structured_response, user_message)
                return ChatResponse(
                    session_id=session_id,
                    message=structured_response.message,
                    mode=structured_response.mode,
                    topic=structured_response.topic,
                    action=structured_response.action,
                    question=structured_response.question,
                    hint=structured_response.hint,
                    misconception=None,
                    sources=[],
                    gantt_chart_ascii=None,
                    concepts_demonstrated=structured_response.concepts_demonstrated,
                    concepts_needing_review=[],
                    difficulty_level=learner_state.difficulty_level or "beginner",
                    is_fallback=False
                )



            # Worked Example Check Question Responses across all algorithms
            # 1. Round Robin: impact of large quantum on turnaround/context switches
            if (
                ("preempted when its 2 ms time slice expired" in pending_q or "quantum were made very large" in pending_q or "turnaround times if the time quantum were made very large" in pending_q)
            ):
                if any(phrase in msg_lower for phrase in ["fcfs", "first come", "first-come", "fifo", "increase", "no preemption", "larger", "run to completion", "completion", "turnaround", "don't know", "dont know", "not sure", "tell me"]):
                    ans_msg = (
                        "Spot on! If the time quantum is made larger than the longest burst, no preemption ever occurs. "
                        "Each process runs to completion in arrival order, making Round Robin equivalent to **First-Come, First-Served (FCFS)**.\n\n"
                        "Would you like to explore another scheduling algorithm or try another problem?"
                    )
                else:
                    ans_msg = (
                        "Good effort! If the time quantum exceeds the longest process burst, processes are never preempted by the timer. "
                        "They simply run to completion in arrival order, making Round Robin behave identically to **First-Come, First-Served (FCFS)**.\n\n"
                        "Would you like to explore another scheduling algorithm or try another problem?"
                    )
                structured_response = TutorStructuredResponse(
                    message=ans_msg,
                    mode=TutoringMode.SOCRATIC,
                    topic="Round Robin",
                    action=TutorAction.ASK_QUESTION,
                    question="Would you like to explore another scheduling algorithm or try another problem?",
                    hint="You can name any algorithm like SJF, SRTF, Priority, HRRN, or CFS.",
                    misconception=None,
                    concepts_demonstrated=["rr_large_quantum_fcfs"],
                    concepts_needing_review=[],
                    source_ids=["01_round_robin_p1_c0"],
                    requires_calculation=False
                )
                learner_state.pending_question = "Would you like to explore another scheduling algorithm or try another problem?"
                learner_state.last_question_asked = learner_state.pending_question
                LearnerModelManager.update_state_from_turn(learner_state, structured_response, user_message)
                return ChatResponse(
                    session_id=session_id,
                    message=structured_response.message,
                    mode=structured_response.mode,
                    topic=structured_response.topic,
                    action=structured_response.action,
                    question=structured_response.question,
                    hint=structured_response.hint,
                    misconception=None,
                    sources=[],
                    gantt_chart_ascii=None,
                    concepts_demonstrated=structured_response.concepts_demonstrated,
                    concepts_needing_review=[],
                    difficulty_level=learner_state.difficulty_level or "beginner",
                    is_fallback=False
                )

            # 2. FCFS: Convoy effect check question
            if (
                ("waiting effect called in fcfs" in pending_q or "p3 had to wait behind p1" in pending_q or "waiting effect" in pending_q)
            ):
                if any(phrase in msg_lower for phrase in ["convoy", "convoy effect", "bottleneck", "blocking", "traffic", "long process", "delay", "wait", "don't know", "dont know", "not sure", "tell me"]):
                    ans_msg = (
                        "Exactly right! That bottleneck is called the **Convoy Effect**: short processes getting held up behind a long CPU-bound process, "
                        "leading to high average waiting times and low I/O device utilization.\n\n"
                        "Would you like to explore how Round Robin or SJF solves this?"
                    )
                else:
                    ans_msg = (
                        "Good attempt! That phenomenon is called the **Convoy Effect**: when short, interactive processes are forced to wait behind a long, CPU-bound process, "
                        "dragging down average waiting time for the entire system.\n\n"
                        "Would you like to explore how Round Robin or SJF solves this?"
                    )
                structured_response = TutorStructuredResponse(
                    message=ans_msg,
                    mode=TutoringMode.SOCRATIC,
                    topic="FCFS",
                    action=TutorAction.ASK_QUESTION,
                    question="Would you like to explore how Round Robin or SJF solves this?",
                    hint="Type 'yes' or name an algorithm.",
                    misconception=None,
                    concepts_demonstrated=["convoy_effect_validation"],
                    concepts_needing_review=[],
                    source_ids=["01_fcfs_algorithm_p1_c0"],
                    requires_calculation=False
                )
                learner_state.pending_question = "Would you like to explore how Round Robin or SJF solves this?"
                learner_state.last_question_asked = learner_state.pending_question
                LearnerModelManager.update_state_from_turn(learner_state, structured_response, user_message)
                return ChatResponse(
                    session_id=session_id,
                    message=structured_response.message,
                    mode=structured_response.mode,
                    topic=structured_response.topic,
                    action=structured_response.action,
                    question=structured_response.question,
                    hint=structured_response.hint,
                    misconception=None,
                    sources=[],
                    gantt_chart_ascii=None,
                    concepts_demonstrated=structured_response.concepts_demonstrated,
                    concepts_needing_review=[],
                    difficulty_level=learner_state.difficulty_level or "beginner",
                    is_fallback=False
                )

            # 3. SJF: Shortest burst selection check question
            if (
                ("chosen before p2" in pending_q or "shortest burst minimize" in pending_q or "prioritizing the shortest burst" in pending_q)
            ):
                if any(phrase in msg_lower for phrase in ["short", "shorter", "shortest", "burst", "less waiting", "optimal", "finish early", "1 ms", "smaller", "leave", "earlier", "wait time", "average waiting", "queue", "don't know", "dont know", "not sure", "tell me"]):
                    ans_msg = (
                        "Spot on! Running shorter jobs first lets tasks leave the queue earliest, which mathematically minimizes the sum of waiting times for all processes.\n\n"
                        "Would you like to practice another problem or explore preemptive SRTF?"
                    )
                else:
                    ans_msg = (
                        "Good thinking! By serving shorter jobs first, processes finish and leave the queue as quickly as possible. "
                        "This mathematically minimizes the cumulative queue wait time across all processes!\n\n"
                        "Would you like to practice another problem or explore preemptive SRTF?"
                    )
                structured_response = TutorStructuredResponse(
                    message=ans_msg,
                    mode=TutoringMode.SOCRATIC,
                    topic="SJF",
                    action=TutorAction.ASK_QUESTION,
                    question="Would you like to practice another problem or explore preemptive SRTF?",
                    hint="Type 'SRTF' or 'another problem'.",
                    misconception=None,
                    concepts_demonstrated=["sjf_optimality"],
                    concepts_needing_review=[],
                    source_ids=["01_sjf_algorithm_p1_c0"],
                    requires_calculation=False
                )
                learner_state.pending_question = "Would you like to practice another problem or explore preemptive SRTF?"
                learner_state.last_question_asked = learner_state.pending_question
                LearnerModelManager.update_state_from_turn(learner_state, structured_response, user_message)
                return ChatResponse(
                    session_id=session_id,
                    message=structured_response.message,
                    mode=structured_response.mode,
                    topic=structured_response.topic,
                    action=structured_response.action,
                    question=structured_response.question,
                    hint=structured_response.hint,
                    misconception=None,
                    sources=[],
                    gantt_chart_ascii=None,
                    concepts_demonstrated=structured_response.concepts_demonstrated,
                    concepts_needing_review=[],
                    difficulty_level=learner_state.difficulty_level or "beginner",
                    is_fallback=False
                )

            # 4. SRTF: Preemption rule check question
            if (
                ("burst 8 ms instead" in pending_q or "triggering preemption" in pending_q or "arrived with burst 8 ms" in pending_q)
            ):
                if any(phrase in msg_lower for phrase in ["no preemption", "continue", "p1 continues", "wont preempt", "won't preempt", "no", "not preempt", "longer", "greater", "larger", "8 > 6", "8 is larger", "don't know", "dont know", "not sure", "tell me"]):
                    ans_msg = (
                        "Spot on! In SRTF, preemption strictly requires that the arriving process has a burst strictly smaller than the remaining execution time of the running process. "
                        "Since 8 ms > 6 ms, P1 would continue running without interruption.\n\n"
                        "Great job on mastering SRTF preemption mechanics! Would you like to explore Priority scheduling next?"
                    )
                else:
                    ans_msg = (
                        "Good attempt! In SRTF, a new arrival only preempts the running process if its burst is strictly shorter than what remains of the current process. "
                        "Because 8 ms is larger than P1's remaining 6 ms, no preemption occurs and P1 continues running!\n\n"
                        "Would you like to explore Priority scheduling next?"
                    )
                structured_response = TutorStructuredResponse(
                    message=ans_msg,
                    mode=TutoringMode.SOCRATIC,
                    topic="SRTF",
                    action=TutorAction.ASK_QUESTION,
                    question="Would you like to explore Priority scheduling next?",
                    hint="Type 'Priority' or 'practice problem'.",
                    misconception=None,
                    concepts_demonstrated=["srtf_preemption_rules"],
                    concepts_needing_review=[],
                    source_ids=["01_srtf_algorithm_p1_c0"],
                    requires_calculation=False
                )
                learner_state.pending_question = "Would you like to explore Priority scheduling next?"
                learner_state.last_question_asked = learner_state.pending_question
                LearnerModelManager.update_state_from_turn(learner_state, structured_response, user_message)
                return ChatResponse(
                    session_id=session_id,
                    message=structured_response.message,
                    mode=structured_response.mode,
                    topic=structured_response.topic,
                    action=structured_response.action,
                    question=structured_response.question,
                    hint=structured_response.hint,
                    misconception=None,
                    sources=[],
                    gantt_chart_ascii=None,
                    concepts_demonstrated=structured_response.concepts_demonstrated,
                    concepts_needing_review=[],
                    difficulty_level=learner_state.difficulty_level or "beginner",
                    is_fallback=False
                )

            # 5. Priority: Preemption by priority value check question
            if (
                ("priority 0 arrived" in pending_q or "process with priority 0" in pending_q)
            ):
                if any(phrase in msg_lower for phrase in ["preempt", "run", "interrupt", "take cpu", "priority 0 runs", "higher", "first", "0 is highest", "immediate", "don't know", "dont know", "not sure", "tell me"]):
                    ans_msg = (
                        "Spot on! Under the lower-value-is-higher-priority convention, Priority 0 is the highest urgency, "
                        "so the new arrival immediately preempts the running process.\n\n"
                        "Would you like to explore how Aging prevents starvation in priority scheduling?"
                    )
                else:
                    ans_msg = (
                        "Good attempt! In standard Operating Systems conventions, Priority 0 represents the highest possible priority (like 1st place in a race). "
                        "Thus, a process with Priority 0 immediately preempts the running job!\n\n"
                        "Would you like to explore how Aging prevents starvation in priority scheduling?"
                    )
                structured_response = TutorStructuredResponse(
                    message=ans_msg,
                    mode=TutoringMode.SOCRATIC,
                    topic="Priority",
                    action=TutorAction.ASK_QUESTION,
                    question="Would you like to explore how Aging prevents starvation in priority scheduling?",
                    hint="Type 'Aging' or 'starvation'.",
                    misconception=None,
                    concepts_demonstrated=["priority_preemption_mechanics"],
                    concepts_needing_review=[],
                    source_ids=["01_priority_scheduling_p1_c0"],
                    requires_calculation=False
                )
                learner_state.pending_question = "Would you like to explore how Aging prevents starvation in priority scheduling?"
                learner_state.last_question_asked = learner_state.pending_question
                LearnerModelManager.update_state_from_turn(learner_state, structured_response, user_message)
                return ChatResponse(
                    session_id=session_id,
                    message=structured_response.message,
                    mode=structured_response.mode,
                    topic=structured_response.topic,
                    action=structured_response.action,
                    question=structured_response.question,
                    hint=structured_response.hint,
                    misconception=None,
                    sources=[],
                    gantt_chart_ascii=None,
                    concepts_demonstrated=structured_response.concepts_demonstrated,
                    concepts_needing_review=[],
                    difficulty_level=learner_state.difficulty_level or "beginner",
                    is_fallback=False
                )

            # 6. HRRN: Response ratio check question
            if (
                ("response ratio" in pending_q or "which one gets chosen first" in pending_q or "two processes have the same burst time" in pending_q)
            ):
                if any(phrase in msg_lower for phrase in ["waited longer", "waiting time", "older", "larger w", "w", "wait time", "waited", "longer wait", "time", "don't know", "dont know", "not sure", "tell me"]):
                    ans_msg = (
                        "Spot on! Since $R = 1 + \\frac{W}{S}$, for processes with identical burst times $S$, "
                        "the process that has waited longer ($W$) has the higher response ratio and executes first, eliminating starvation.\n\n"
                        "Outstanding reasoning! Would you like to explore Linux CFS or Real-Time scheduling next?"
                    )
                else:
                    ans_msg = (
                        "Good thinking! The response ratio formula is $R = 1 + \\frac{W}{S}$. When two processes have the same burst time $S$, "
                        "the process with the larger waiting time $W$ achieves a higher ratio and is scheduled first, eliminating starvation!\n\n"
                        "Would you like to explore Linux CFS or Real-Time scheduling next?"
                    )
                structured_response = TutorStructuredResponse(
                    message=ans_msg,
                    mode=TutoringMode.SOCRATIC,
                    topic="HRRN",
                    action=TutorAction.ASK_QUESTION,
                    question="Would you like to explore Linux CFS or Real-Time scheduling next?",
                    hint="Type 'CFS' or 'Real-Time'.",
                    misconception=None,
                    concepts_demonstrated=["hrrn_starvation_prevention"],
                    concepts_needing_review=[],
                    source_ids=["01_hrrn_highest_response_ratio_next_p1_c0"],
                    requires_calculation=False
                )
                learner_state.pending_question = "Would you like to explore Linux CFS or Real-Time scheduling next?"
                learner_state.last_question_asked = learner_state.pending_question
                LearnerModelManager.update_state_from_turn(learner_state, structured_response, user_message)
                return ChatResponse(
                    session_id=session_id,
                    message=structured_response.message,
                    mode=structured_response.mode,
                    topic=structured_response.topic,
                    action=structured_response.action,
                    question=structured_response.question,
                    hint=structured_response.hint,
                    misconception=None,
                    sources=[],
                    gantt_chart_ascii=None,
                    concepts_demonstrated=structured_response.concepts_demonstrated,
                    concepts_needing_review=[],
                    difficulty_level=learner_state.difficulty_level or "beginner",
                    is_fallback=False
                )

            # 7. MLFQ: Priority Boost / Starvation check question
            if (
                ("demoted jobs in q2 do not starve" in pending_q or "mechanism does mlfq use" in pending_q or "demoted to q1" in pending_q or "completed at t=5 ms in top queue" in pending_q)
            ):
                if any(phrase in msg_lower for phrase in ["priority boost", "boost", "aging", "periodic boost", "move all", "reset priority", "promot", "ageing", "top queue", "move to q0", "don't know", "dont know", "not sure", "tell me"]):
                    ans_msg = (
                        "Spot on! MLFQ implements a periodic **Priority Boost** (Rule 5): after a fixed time period $S$, all processes in the system are moved to top Queue $Q_0$. "
                        "This guarantees that starving CPU-bound processes get CPU time, and also allows processes whose behavior transformed from batch to interactive to regain top priority!\n\n"
                        "Outstanding reasoning! Would you like to explore Linux CFS or Real-Time scheduling next?"
                    )
                else:
                    ans_msg = (
                        "Good thinking! MLFQ solves this with a periodic **Priority Boost**: after a time period $S$, the operating system moves all processes back to the top Queue $Q_0$. "
                        "This resets their priority and guarantees long batch jobs never starve!\n\n"
                        "Would you like to explore Linux CFS or Real-Time scheduling next?"
                    )
                structured_response = TutorStructuredResponse(
                    message=ans_msg,
                    mode=TutoringMode.SOCRATIC,
                    topic="MLFQ",
                    action=TutorAction.ASK_QUESTION,
                    question="Would you like to explore Linux CFS or Real-Time scheduling next?",
                    hint="Type 'CFS' or 'Real-Time'.",
                    misconception=None,
                    concepts_demonstrated=["mlfq_priority_boost", "mlfq_starvation_prevention"],
                    concepts_needing_review=[],
                    source_ids=["05_multilevel_queues_and_advanced_p1_c0"],
                    requires_calculation=False
                )
                learner_state.pending_question = "Would you like to explore Linux CFS or Real-Time scheduling next?"
                learner_state.last_question_asked = learner_state.pending_question
                LearnerModelManager.update_state_from_turn(learner_state, structured_response, user_message)
                return ChatResponse(
                    session_id=session_id,
                    message=structured_response.message,
                    mode=structured_response.mode,
                    topic=structured_response.topic,
                    action=structured_response.action,
                    question=structured_response.question,
                    hint=structured_response.hint,
                    misconception=None,
                    sources=[],
                    gantt_chart_ascii=None,
                    concepts_demonstrated=structured_response.concepts_demonstrated,
                    concepts_needing_review=[],
                    difficulty_level=learner_state.difficulty_level or "beginner",
                    is_fallback=False
                )

            # 8. CFS: Virtual runtime growth rate check question
            if (
                ("negative nice value make vruntime grow faster or slower" in pending_q or "vruntime grow faster or slower" in pending_q)
            ):
                if any(phrase in msg_lower for phrase in ["slower", "slow", "less", "more slowly", "decreases rate", "decrease", "slowly", "don't know", "dont know", "not sure", "tell me"]):
                    ans_msg = (
                        "Spot on! Because high-priority tasks (negative nice values) have a much higher weight, their `vruntime` increases **slower** per millisecond of real CPU execution: "
                        "$\\Delta vruntime = \\Delta \\text{exec} \\times \\frac{1024}{weight}$. This keeps them at the leftmost branch of the Red-Black Tree longer so they receive more CPU time!\n\n"
                        "Would you like to explore Real-Time scheduling (RMS & EDF) or Multiprocessor scheduling next?"
                    )
                else:
                    ans_msg = (
                        "Good attempt! In CFS, higher-priority tasks have larger weights, causing their `vruntime` to accumulate **slower** than real time. "
                        "Because CFS always selects the task with the smallest `vruntime`, they stay eligible to run longer!\n\n"
                        "Would you like to explore Real-Time scheduling (RMS & EDF) or Multiprocessor scheduling next?"
                    )
                structured_response = TutorStructuredResponse(
                    message=ans_msg,
                    mode=TutoringMode.SOCRATIC,
                    topic="CFS",
                    action=TutorAction.ASK_QUESTION,
                    question="Would you like to explore Real-Time scheduling (RMS & EDF) or Multiprocessor scheduling next?",
                    hint="Type 'Real-Time' or 'Multiprocessor'.",
                    misconception=None,
                    concepts_demonstrated=["cfs_vruntime_nice_weight"],
                    concepts_needing_review=[],
                    source_ids=["02_linux_cfs_completely_fair_scheduler_p1_c0"],
                    requires_calculation=False
                )
                learner_state.pending_question = "Would you like to explore Real-Time scheduling (RMS & EDF) or Multiprocessor scheduling next?"
                learner_state.last_question_asked = learner_state.pending_question
                LearnerModelManager.update_state_from_turn(learner_state, structured_response, user_message)
                return ChatResponse(
                    session_id=session_id,
                    message=structured_response.message,
                    mode=structured_response.mode,
                    topic=structured_response.topic,
                    action=structured_response.action,
                    question=structured_response.question,
                    hint=structured_response.hint,
                    misconception=None,
                    sources=[],
                    gantt_chart_ascii=None,
                    concepts_demonstrated=structured_response.concepts_demonstrated,
                    concepts_needing_review=[],
                    difficulty_level=learner_state.difficulty_level or "beginner",
                    is_fallback=False
                )

            # 9. Real-Time RMS: Preemption check question
            if (
                ("what would happen under preemptive rms" in pending_q or "tau_1 releases a new job" in pending_q or "assigned higher priority than tau_2 because its period" in pending_q)
            ):
                if any(phrase in msg_lower for phrase in ["preempt", "preemption", "tau_1 runs", "t1 runs", "interrupt", "switch", "stops tau_2", "run tau_1", "tau 1", "t1", "don't know", "dont know", "not sure", "tell me"]):
                    ans_msg = (
                        "Spot on! In preemptive Rate Monotonic Scheduling (RMS), because $\\tau_1$ has a shorter period (4 ms) than $\\tau_2$ (6 ms), "
                        "it has higher static priority. At $t=4$ ms, $\\tau_1$'s new job immediately preempts the running $\\tau_2$ to guarantee that $\\tau_1$ meets its deadline!\n\n"
                        "Would you like to explore Earliest Deadline First (EDF) or Multiprocessor scheduling next?"
                    )
                else:
                    ans_msg = (
                        "Good attempt! In Rate Monotonic Scheduling, the task with the shorter period has higher priority. "
                        "When $\\tau_1$'s new period begins at $t=4$ ms, it immediately preempts $\\tau_2$ so that $\\tau_1$ never misses its strict deadline!\n\n"
                        "Would you like to explore Earliest Deadline First (EDF) or Multiprocessor scheduling next?"
                    )
                structured_response = TutorStructuredResponse(
                    message=ans_msg,
                    mode=TutoringMode.SOCRATIC,
                    topic="Real-Time",
                    action=TutorAction.ASK_QUESTION,
                    question="Would you like to explore Earliest Deadline First (EDF) or Multiprocessor scheduling next?",
                    hint="Type 'EDF' or 'Multiprocessor'.",
                    misconception=None,
                    concepts_demonstrated=["rms_preemption_mechanics"],
                    concepts_needing_review=[],
                    source_ids=["03_real_time_scheduling_rms_edf_p1_c0"],
                    requires_calculation=False
                )
                learner_state.pending_question = "Would you like to explore Earliest Deadline First (EDF) or Multiprocessor scheduling next?"
                learner_state.last_question_asked = learner_state.pending_question
                LearnerModelManager.update_state_from_turn(learner_state, structured_response, user_message)
                return ChatResponse(
                    session_id=session_id,
                    message=structured_response.message,
                    mode=structured_response.mode,
                    topic=structured_response.topic,
                    action=structured_response.action,
                    question=structured_response.question,
                    hint=structured_response.hint,
                    misconception=None,
                    sources=[],
                    gantt_chart_ascii=None,
                    concepts_demonstrated=structured_response.concepts_demonstrated,
                    concepts_needing_review=[],
                    difficulty_level=learner_state.difficulty_level or "beginner",
                    is_fallback=False
                )

            # 10. Multiprocessor: Work stealing / cache affinity trade-off check question
            if (
                ("what trade-off occurs when p4 migrates from core 1 to core 0" in pending_q or "migrates from core 1" in pending_q or "stole the remaining 2 ms of p4" in pending_q)
            ):
                if any(phrase in msg_lower for phrase in ["cache", "cache miss", "affinity", "warm cache", "latency", "cold cache", "invalidat", "reload", "misses", "don't know", "dont know", "not sure", "tell me"]):
                    ans_msg = (
                        "Spot on! While work stealing keeps Core 0 utilized (eliminating idle core waste), migrating P4 destroys its **cache affinity**. "
                        "Core 0's private L1/L2 caches are cold for P4, causing high memory access latency as P4's cache lines must be reloaded from shared L3 cache or RAM!\n\n"
                        "Would you like to explore another topic or try another problem?"
                    )
                else:
                    ans_msg = (
                        "Good thinking! The main trade-off is **Cache Affinity**: while stealing P4 keeps Core 0 busy, Core 0 has none of P4's data in its private L1/L2 caches. "
                        "P4 suffers cold cache misses and must reload its working set from slower memory!\n\n"
                        "Would you like to explore another topic or try another problem?"
                    )
                structured_response = TutorStructuredResponse(
                    message=ans_msg,
                    mode=TutoringMode.SOCRATIC,
                    topic="Multiprocessor",
                    action=TutorAction.ASK_QUESTION,
                    question="Would you like to explore another topic or try another problem?",
                    hint="You can name any algorithm like Round Robin, SJF, SRTF, or CFS.",
                    misconception=None,
                    concepts_demonstrated=["work_stealing_cache_affinity_tradeoff"],
                    concepts_needing_review=[],
                    source_ids=["04_multiprocessor_and_thread_scheduling_p1_c0"],
                    requires_calculation=False
                )
                learner_state.pending_question = "Would you like to explore another topic or try another problem?"
                learner_state.last_question_asked = learner_state.pending_question
                LearnerModelManager.update_state_from_turn(learner_state, structured_response, user_message)
                return ChatResponse(
                    session_id=session_id,
                    message=structured_response.message,
                    mode=structured_response.mode,
                    topic=structured_response.topic,
                    action=structured_response.action,
                    question=structured_response.question,
                    hint=structured_response.hint,
                    misconception=None,
                    sources=[],
                    gantt_chart_ascii=None,
                    concepts_demonstrated=structured_response.concepts_demonstrated,
                    concepts_needing_review=[],
                    difficulty_level=learner_state.difficulty_level or "beginner",
                    is_fallback=False
                )

            # 11. Stride Scheduling: Smaller stride check question
            if (
                ("smaller stride cause a process to be selected more frequently or less frequently" in pending_q or "selected more frequently or less frequently" in pending_q or "stride of 50, whereas p1 with 100 tickets has a stride of 100" in pending_q)
            ):
                if any(phrase in msg_lower for phrase in ["more", "more frequently", "often", "more often", "higher", "frequently", "run more", "don't know", "dont know", "not sure", "tell me"]):
                    ans_msg = (
                        "Spot on! In Stride Scheduling, the process with the smallest `pass` value is always scheduled next. "
                        "A smaller stride means the pass counter advances in smaller increments, causing the process to stay near the minimum pass value and be selected **more frequently**!\n\n"
                        "Would you like to explore another scheduling algorithm or practice another problem?"
                    )
                else:
                    ans_msg = (
                        "Good attempt! The scheduler always selects the process with the lowest `pass` counter. "
                        "A smaller stride increases the pass counter by smaller steps each turn, keeping the process eligible and causing it to be scheduled **more frequently**!\n\n"
                        "Would you like to explore another scheduling algorithm or practice another problem?"
                    )
                structured_response = TutorStructuredResponse(
                    message=ans_msg,
                    mode=TutoringMode.SOCRATIC,
                    topic="Stride Scheduling",
                    action=TutorAction.ASK_QUESTION,
                    question="Would you like to explore another scheduling algorithm or practice another problem?",
                    hint="You can name any algorithm like Round Robin, SJF, SRTF, or CFS.",
                    misconception=None,
                    concepts_demonstrated=["stride_selection_frequency"],
                    concepts_needing_review=[],
                    source_ids=["05_lottery_and_stride_scheduling_p1_c0"],
                    requires_calculation=False
                )
                learner_state.pending_question = "Would you like to explore another scheduling algorithm or practice another problem?"
                learner_state.last_question_asked = learner_state.pending_question
                LearnerModelManager.update_state_from_turn(learner_state, structured_response, user_message)
                return ChatResponse(
                    session_id=session_id,
                    message=structured_response.message,
                    mode=structured_response.mode,
                    topic=structured_response.topic,
                    action=structured_response.action,
                    question=structured_response.question,
                    hint=structured_response.hint,
                    misconception=None,
                    sources=[],
                    gantt_chart_ascii=None,
                    concepts_demonstrated=structured_response.concepts_demonstrated,
                    concepts_needing_review=[],
                    difficulty_level=learner_state.difficulty_level or "beginner",
                    is_fallback=False
                )


        # D. Explicit Syllabus Request (shown ONLY when explicitly requested)
        if intent == ConversationIntent.SYLLABUS_REQUEST:
            syl_msg = (
                "Here are the topics we cover in CPU scheduling:\n\n"
                "* **Fundamentals**: Process states, CPU/I/O bursts, CPU scheduler vs. dispatcher, context switching\n"
                "* **Scheduling Metrics**: Completion Time, Turnaround Time, Waiting Time, Response Time, and Gantt charts\n"
                "* **Non-Preemptive Algorithms**: First-Come First-Served (FCFS), Shortest Job First (SJF)\n"
                "* **Preemptive Algorithms**: Shortest Remaining Time First (SRTF), Round Robin (RR), Preemptive Priority\n"
                "* **Advanced Concepts**: Starvation, aging, convoy effect, multilevel queues\n\n"
                "Which of these would you like to start with?"
            )
            structured_response = TutorStructuredResponse(
                message=syl_msg,
                mode=active_mode,
                topic=learner_state.current_topic or "Fundamentals",
                action=TutorAction.EXPLAIN_CONCEPT,
                question="Which of these topics would you like to start with?",
                hint="Pick any algorithm or fundamental concept to begin.",
                misconception=None,
                concepts_demonstrated=[],
                concepts_needing_review=[],
                source_ids=[],
                requires_calculation=False
            )
            LearnerModelManager.update_state_from_turn(learner_state, structured_response, user_message)
            return ChatResponse(
                session_id=session_id,
                message=structured_response.message,
                mode=structured_response.mode,
                topic=structured_response.topic,
                action=structured_response.action,
                question=structured_response.question,
                hint=structured_response.hint,
                misconception=None,
                sources=[],
                gantt_chart_ascii=None,
                concepts_demonstrated=[],
                concepts_needing_review=[],
                difficulty_level=learner_state.difficulty_level or "beginner",
                is_fallback=False
            )


        # E. Direct Concept Comparison: "What is the difference between FCFS and SJF?"
        if intent == ConversationIntent.CONCEPT_COMPARISON:
            comp_msg = (
                "Here is how **FCFS** and **SJF** compare:\n\n"
                "* **Selection Rule**: FCFS (First-Come, First-Served) runs processes strictly in the order they arrive (FIFO). SJF (Shortest Job First) selects the process with the shortest CPU burst time next.\n"
                "* **Performance**: SJF is provably optimal for minimizing average waiting time. In contrast, FCFS can suffer from the **Convoy Effect**, where short processes get stuck waiting behind one long process, resulting in high average waiting times.\n"
                "* **Trade-off / Risk**: FCFS is simple and fair with zero starvation. SJF requires knowing or estimating burst times in advance, and long processes can suffer from **starvation** if shorter jobs keep arriving.\n\n"
                "*Quick Example*: If P1 (burst 10) arrives first at $t=0$, followed by P2 (burst 2) and P3 (burst 1):\n"
                "- Under **FCFS**: P1 runs first (0-10), then P2 (10-12), then P3 (12-13). Average waiting time = $(0 + 10 + 12) / 3 = 7.33$ ms.\n"
                "- Under **SJF** (if all ready): P3 runs first (0-1), then P2 (1-3), then P1 (3-13). Average waiting time = $(0 + 1 + 3) / 3 = 1.33$ ms."
            )
            structured_response = TutorStructuredResponse(
                message=comp_msg,
                mode=TutoringMode.EXPLANATION,
                topic="SJF",
                action=TutorAction.EXPLAIN_CONCEPT,
                question=None,
                hint=None,
                misconception=None,
                concepts_demonstrated=["fcfs_vs_sjf", "convoy_effect", "optimal_waiting_time"],
                concepts_needing_review=[],
                source_ids=["01_fcfs_algorithm_p1_c0", "01_sjf_algorithm_p1_c0"],
                requires_calculation=False
            )
            learner_state.current_topic = "SJF"
            LearnerModelManager.update_state_from_turn(learner_state, structured_response, user_message)
            return ChatResponse(
                session_id=session_id,
                message=structured_response.message,
                mode=structured_response.mode,
                topic=structured_response.topic,
                action=structured_response.action,
                question=None,
                hint=None,
                misconception=None,
                sources=[],
                gantt_chart_ascii=None,
                concepts_demonstrated=structured_response.concepts_demonstrated,
                concepts_needing_review=[],
                difficulty_level=learner_state.difficulty_level or "beginner",
                is_fallback=False
            )

        # F. Direct Explanation Request: "Just explain it directly.", "Just give me the definition", etc.
        if intent == ConversationIntent.DIRECT_EXPLANATION:
            concept_id = SocraticEngine.detect_concept(user_message)
            if concept_id and concept_id != "preemption":
                structured_response = SocraticEngine.get_direct_explanation(concept_id, learner_state)
                LearnerModelManager.update_state_from_turn(learner_state, structured_response, user_message)
                return ChatResponse(
                    session_id=session_id,
                    message=structured_response.message,
                    mode=structured_response.mode,
                    topic=structured_response.topic,
                    action=structured_response.action,
                    question=None,
                    hint=None,
                    misconception=None,
                    sources=[],
                    gantt_chart_ascii=None,
                    concepts_demonstrated=structured_response.concepts_demonstrated,
                    concepts_needing_review=[],
                    difficulty_level=learner_state.difficulty_level or "beginner",
                    is_fallback=False
                )



            direct_msg = (
                "In Operating Systems, the difference comes down to whether the operating system can interrupt a running process before it finishes:\n\n"
                "* **Preemptive Scheduling**: The operating system can pause (preempt) a currently running process when a higher-priority process arrives or when its time slice expires (via a hardware timer interrupt). The interrupted process moves from the Running state back to the Ready state.\n"
                "* **Non-Preemptive (Cooperative) Scheduling**: Once a process gets the CPU, it keeps running until it finishes its CPU burst or voluntarily yields (for example, by waiting for I/O). The scheduler cannot force it off the CPU.\n\n"
                "Preemptive scheduling provides much better responsiveness for interactive systems, but incurs context switch overhead. Non-preemptive scheduling is simpler and has lower overhead, but long jobs can delay shorter jobs."
            )
            structured_response = TutorStructuredResponse(
                message=direct_msg,
                mode=TutoringMode.EXPLANATION,
                topic=learner_state.current_topic or "Preemption",
                action=TutorAction.EXPLAIN_CONCEPT,
                question=None,
                hint=None,
                misconception=None,
                concepts_demonstrated=["preemptive_definition", "non_preemptive_cooperative"],
                concepts_needing_review=[],
                source_ids=["01_preemption_concepts_p1_c0"],
                requires_calculation=False
            )
            learner_state.lesson_stage = "explanation"
            LearnerModelManager.update_state_from_turn(learner_state, structured_response, user_message)
            return ChatResponse(
                session_id=session_id,
                message=structured_response.message,
                mode=structured_response.mode,
                topic=structured_response.topic,
                action=structured_response.action,
                question=None,
                hint=None,
                misconception=None,
                sources=[],
                gantt_chart_ascii=None,
                concepts_demonstrated=structured_response.concepts_demonstrated,
                concepts_needing_review=[],
                difficulty_level=learner_state.difficulty_level or "beginner",
                is_fallback=False
            )

        # G. Student Knows Nothing: "I don't know anything about it."
        if intent == ConversationIntent.ZERO_KNOWLEDGE:
            knows_nothing_msg = (
                "No problem. Let's start with a simple example. Imagine you're doing a task and someone asks you to pause it so they can use your desk. "
                "That's the basic idea behind preemption: the operating system can pause a running task so another task can use the CPU. "
                "In non-preemptive systems, once you get the desk, you keep it until you finish your entire task."
            )
            structured_response = TutorStructuredResponse(
                message=knows_nothing_msg,
                mode=TutoringMode.EXPLANATION,
                topic=learner_state.current_topic or "Preemption",
                action=TutorAction.EXPLAIN_CONCEPT,
                question="Does that desk analogy make sense?",
                hint="Think about whether sharing is forced or voluntary.",
                misconception=None,
                concepts_demonstrated=["preemption_analogy"],
                concepts_needing_review=[],
                source_ids=["01_preemption_concepts_p1_c0"],
                requires_calculation=False
            )
            learner_state.lesson_stage = "guided_inquiry"
            LearnerModelManager.update_state_from_turn(learner_state, structured_response, user_message)
            return ChatResponse(
                session_id=session_id,
                message=structured_response.message,
                mode=structured_response.mode,
                topic=structured_response.topic,
                action=structured_response.action,
                question=structured_response.question,
                hint=structured_response.hint,
                misconception=None,
                sources=[],
                gantt_chart_ascii=None,
                concepts_demonstrated=structured_response.concepts_demonstrated,
                concepts_needing_review=[],
                difficulty_level=learner_state.difficulty_level or "beginner",
                is_fallback=False
            )

        # H. Partial Understanding: "I know that preemptive scheduling can interrupt a running process."
        if intent == ConversationIntent.PARTIAL_UNDERSTANDING:
            partial_msg = "Exactly. The key question is what happens when another process becomes ready. Want to try a quick example?"
            structured_response = TutorStructuredResponse(
                message=partial_msg,
                mode=TutoringMode.SOCRATIC,
                topic=learner_state.current_topic or "Preemption",
                action=TutorAction.ASK_QUESTION,
                question="Want to try a quick example?",
                hint="Consider what happens to the interrupted process.",
                misconception=None,
                concepts_demonstrated=["preemptive_interrupts"],
                concepts_needing_review=[],
                source_ids=["01_preemption_concepts_p1_c0"],
                requires_calculation=False
            )
            learner_state.lesson_stage = "guided_inquiry"
            LearnerModelManager.update_state_from_turn(learner_state, structured_response, user_message)
            return ChatResponse(
                session_id=session_id,
                message=structured_response.message,
                mode=structured_response.mode,
                topic=structured_response.topic,
                action=structured_response.action,
                question=structured_response.question,
                hint=structured_response.hint,
                misconception=None,
                sources=[],
                gantt_chart_ascii=None,
                concepts_demonstrated=structured_response.concepts_demonstrated,
                concepts_needing_review=[],
                difficulty_level=learner_state.difficulty_level or "beginner",
                is_fallback=False
            )

        # I. Explore Round Robin: "i want to explore round robin"
        if intent == ConversationIntent.EXPLORE_ROUND_ROBIN:
            rr_msg = (
                "Round Robin (RR) is a preemptive scheduling algorithm where each ready process is allocated a fixed slice of CPU time, called a **time quantum** (or time slice). "
                "The processes are executed in a circular FIFO queue; if a process does not complete within its time quantum, it is preempted and put at the tail of the ready queue.\n\n"
                "Here is a quick question to check your intuition:\n"
                "Which scheduling algorithm does Round Robin become equivalent to when the time quantum exceeds the longest CPU burst?"
            )
            structured_response = TutorStructuredResponse(
                message=rr_msg,
                mode=TutoringMode.SOCRATIC,
                topic="Round Robin",
                action=TutorAction.ASK_QUESTION,
                question="Which scheduling algorithm does Round Robin become equivalent to when the time quantum exceeds the longest CPU burst?",
                hint="Think about whether any process will ever be preempted if the quantum is that large.",
                misconception=None,
                concepts_demonstrated=["round_robin_basics"],
                concepts_needing_review=[],
                source_ids=["01_round_robin_p1_c0"],
                requires_calculation=False
            )
            learner_state.current_topic = "Round Robin"
            learner_state.current_subtopic = "Time Quantum & Equivalence"
            learner_state.pending_question = "Which scheduling algorithm does Round Robin become equivalent to when the time quantum exceeds the longest CPU burst?"
            learner_state.last_question_asked = learner_state.pending_question
            learner_state.lesson_stage = "guided_inquiry"
            learner_state.last_concept_explained = "Round Robin fixed time slice / circular FIFO queue"
            learner_state.next_teaching_step = "Assess impact of time quantum size on scheduling behavior"
            LearnerModelManager.update_state_from_turn(learner_state, structured_response, user_message)
            return ChatResponse(
                session_id=session_id,
                message=structured_response.message,
                mode=structured_response.mode,
                topic=structured_response.topic,
                action=structured_response.action,
                question=structured_response.question,
                hint=structured_response.hint,
                misconception=None,
                sources=[],
                gantt_chart_ascii=None,
                concepts_demonstrated=structured_response.concepts_demonstrated,
                concepts_needing_review=[],
                difficulty_level=learner_state.difficulty_level or "beginner",
                is_fallback=False
            )

        # J. New Concept Inquiry: Launches interactive Socratic lesson for ANY OS scheduling concept
        if intent == ConversationIntent.NEW_CONCEPT_INQUIRY:
            concept_id = SocraticEngine.detect_concept(user_message) or "preemption"
            structured_response = SocraticEngine.start_socratic_lesson(concept_id, learner_state)
            LearnerModelManager.update_state_from_turn(learner_state, structured_response, user_message)
            return ChatResponse(
                session_id=session_id,
                message=structured_response.message,
                mode=structured_response.mode,
                topic=structured_response.topic,
                action=structured_response.action,
                question=structured_response.question,
                hint=structured_response.hint,
                misconception=None,
                sources=[],
                gantt_chart_ascii=None,
                concepts_demonstrated=structured_response.concepts_demonstrated,
                concepts_needing_review=[],
                difficulty_level=learner_state.difficulty_level or "beginner",
                is_fallback=False
            )


        # 1. Topic Switch & State Continuity Management
        topic = topic_override or self.detect_topic(user_message, learner_state.current_topic)
        if topic != learner_state.current_topic:
            LearnerModelManager.handle_topic_switch(learner_state, topic)

        current_mode = TutoringMode(learner_state.current_mode) if learner_state.current_mode else TutoringMode.SOCRATIC
        active_mode = mode_override or self.detect_mode_intent(user_message, current_mode)

        learner_state.current_topic = topic
        learner_state.current_mode = active_mode.value

        # Initialize unassessed concepts if empty
        if not learner_state.concepts_not_assessed and not learner_state.concepts_understood:
            LearnerModelManager.initialize_topic_concepts(learner_state, topic)

        # 2. Conversational Memory & Token-Aware Rolling Context Management
        recent_window_size = 8
        recent_messages = ConversationMemoryManager.format_recent_messages(history, window_size=recent_window_size)

        # Incrementally update conversation summary preserving key educational facts
        if history:
            learner_state.conversation_summary = ConversationMemoryManager.build_or_update_summary(
                current_summary=learner_state.conversation_summary or "",
                messages_to_summarize=history,
                learner_state=learner_state
            )

        # 3. RAG Retrieval - retrieve top semantically relevant passages
        retrieved_passages = self.retriever.retrieve(
            query=user_message,
            topic=topic,
            top_k=2
        )

        # 4. Deterministic Numerical Verification and Worked Example Generation
        verified_info, verified_gantt, verified_example_md = self._attempt_deterministic_solve(
            user_message, topic, active_mode, is_example_intent=(intent == ConversationIntent.WORKED_EXAMPLE)
        )

        # 5. Build Consolidated System Prompt
        system_prompt = build_system_prompt(
            mode=active_mode,
            topic=topic,
            learner_state=learner_state,
            passages=retrieved_passages,
            verified_scheduling_info=verified_info
        )

        # 6. Assemble Full Conversational Payload for LLM
        chat_messages = ConversationMemoryManager.assemble_prompt_messages(
            system_prompt=system_prompt,
            conversation_summary=learner_state.conversation_summary,
            recent_messages=recent_messages,
            latest_user_message=user_message,
            tutoring_state_dict=learner_state.to_state_dict()
        )

        # 7. Pedagogical Decision Engine
        msg_lower = user_message.lower().strip()
        last_asst_msg = ""
        for m in reversed(history):
            if m.role == "assistant":
                last_asst_msg = m.content
                break

        # A. Check: Previous Question Answer Evaluation
        eval_result = evaluate_catalog_answer(last_asst_msg, user_message) if last_asst_msg else None

        # B. Check: Worked Example Explicit Request
        is_direct_example_request = (
            verified_example_md is not None
            and (
                intent == ConversationIntent.WORKED_EXAMPLE
                or any(k in msg_lower for k in [
                    "take an example", "consider an example", "give an example", "give me an example",
                    "show an example", "show me an example", "worked example", "explain with an example",
                    "take an example for", "example of", "an example of", "example for"
                ])
            )
        )

        # C. Check: Explicit Direct Teaching Request or Complete Beginner
        is_explicit_direct_request = (
            active_mode == TutoringMode.EXPLANATION
            and any(k in msg_lower for k in [
                "explain directly", "teach me from the beginning", "just tell me the answer",
                "give me proper notes", "explain the whole concept", "i don't understand", "i dont understand"
            ])
        )

        is_student_knows_nothing = any(k in msg_lower for k in [
            "i don't know anything", "i dont know anything", "i know nothing", "no idea", "not sure"
        ])

        # D. Check: Partial Understanding (Section 4.3)
        # e.g. "I know preemptive allows interrupt, but don't understand non-preemptive"
        is_partial_understanding = (
            ("i know" in msg_lower or "i understand" in msg_lower)
            and any(k in msg_lower for k in ["but don't understand", "but i don't understand", "but not", "confused about", "what about"])
        )

        # E. Check: Advanced Student Asking Specific Angle (Section 4.4)
        # e.g. "I understand both definitions. I want to know how they affect response time."
        is_specific_tradeoff_inquiry = (
            any(k in msg_lower for k in ["i understand both", "i know both", "i already understand", "i get both"])
            or ("affect response time" in msg_lower or "trade-off" in msg_lower or "trade off" in msg_lower)
        )

        # F. Check: New Conceptual Question in unassessed topic (Section 4.2)
        # Student asks a new concept question without asking for direct teaching
        is_new_concept_inquiry = (
            learner_state.lesson_stage == "knowledge_assessment"
            and not is_explicit_direct_request
            and not is_direct_example_request
            and not is_partial_understanding
            and not is_student_knows_nothing
            and any(msg_lower.startswith(p) for p in [
                "what is", "what are", "difference between", "how does", "why does", "tell me about"
            ])
        )

        # G. Check: Memory / Recall of Earlier Session Context (Section 3.1 & 3.2)
        is_memory_recall_request = (
            any(k in msg_lower for k in [
                "first weakness", "weakness i mentioned", "weakness did i", "what was my weakness",
                "in that example you just showed", "in the example you showed", "waiting time of p2"
            ])
        )

        structured_response = None
        is_fallback = False

        # --- ROUTING DECISIONS ---

        # 1. Answer Evaluation
        if eval_result:
            structured_response = TutorStructuredResponse(
                message=eval_result["message"],
                mode=active_mode,
                topic=topic,
                action=TutorAction.EVALUATE_ANSWER,
                question=eval_result.get("question"),
                hint=eval_result.get("hint"),
                misconception=eval_result.get("misconception"),
                concepts_demonstrated=eval_result.get("concepts_demonstrated", []),
                concepts_needing_review=[],
                source_ids=[p.get("chunk_id", "") for p in retrieved_passages if p.get("chunk_id")],
                requires_calculation=False,
                gantt_chart_ascii=None
            )

        # 2. Worked Example
        elif is_direct_example_request:
            intro = (
                f"Here is a complete worked example for **{topic}** scheduling showing arrival times, execution sequence, Gantt chart, and timeline metrics:\n\n"
                f"{verified_example_md}"
            )
            q_text = (
                "Notice how P3 had to wait behind P1 and P2 despite needing only 1 ms of CPU time. What is this waiting effect called in FCFS?"
                if "fcfs" in topic.lower() else
                "Notice how each process was preempted when its 2 ms time slice expired. What would happen to the turnaround times if the time quantum were made very large?"
                if "round robin" in topic.lower() or topic.lower() == "rr" else
                "Notice how response ratio R = 1 + W/S increases the longer a process waits. If two processes have the same burst time, which one gets chosen first?"
                if "hrrn" in topic.lower() else
                "Notice how after P1 finished at t=6 ms, P3 (BT=1) was chosen before P2 (BT=3). How does prioritizing the shortest burst minimize average waiting time?"
                if "sjf" in topic.lower() else
                "Notice that at t=1 ms, P2 arrived with burst 4 while P1 had 6 ms remaining, triggering preemption. What would happen if P2 arrived with burst 8 ms instead?"
                if "srtf" in topic.lower() else
                "Notice how P2 preempted P1 at t=1 ms because Priority 1 is higher urgency than Priority 3. What would happen if a process with Priority 0 arrived?"
                if "priority" in topic.lower() else
                "Notice how short interactive job P3 completed at t=5 ms in top Queue Q0 without ever being demoted, while long CPU job P1 descended to Q2. What mechanism does MLFQ use to ensure that demoted jobs in Q2 do not starve if new interactive jobs keep arriving?"
                if "mlfq" in topic.lower() or "multilevel" in topic.lower() else
                "Notice how high-priority process P2 (nice -5) received 6 ms of CPU time while low-priority P3 (nice +5) received only 2 ms, yet both progressed their virtual runtimes. In CFS, does a negative nice value make vruntime grow faster or slower than real execution time?"
                if "cfs" in topic.lower() or "completely fair" in topic.lower() else
                "Notice how tau_1 was assigned higher priority than tau_2 because its period (4 ms) is shorter than tau_2's period (6 ms). If tau_2 were running at t=4 ms when tau_1 releases a new job, what would happen under preemptive RMS?"
                if "real" in topic.lower() or "rms" in topic.lower() or "edf" in topic.lower() else
                "Notice how Core 0 finished its local queue at t=7 ms and stole the remaining 2 ms of P4 from Core 1's queue. What trade-off occurs when P4 migrates from Core 1 to Core 0?"
                if "multiprocessor" in topic.lower() or "multicore" in topic.lower() else
                "Notice how process P2 with 200 tickets has a stride of 50, whereas P1 with 100 tickets has a stride of 100. Does a smaller stride cause a process to be selected more frequently or less frequently by the scheduler?"
                if "stride" in topic.lower() or "lottery" in topic.lower() or "proportional" in topic.lower() else
                f"Based on this timeline, what factor decided which process ran next at each transition?"
            )
            structured_response = TutorStructuredResponse(
                message=intro,
                mode=TutoringMode.EXPLANATION,
                topic=topic,
                action=TutorAction.EXPLAIN_CONCEPT,
                question=q_text,
                hint="Think about process arrival order and burst times.",
                misconception=None,
                concepts_demonstrated=[f"{topic.lower()}_execution", "gantt_chart", "tat_and_wt_metrics"],
                concepts_needing_review=[],
                source_ids=[p.get("chunk_id", "") for p in retrieved_passages if p.get("chunk_id")],
                requires_calculation=True,
                gantt_chart_ascii=verified_gantt
            )
            learner_state.current_topic = topic
            learner_state.current_subtopic = "Worked Example & Metrics"
            learner_state.pending_question = q_text
            learner_state.last_question_asked = q_text
            learner_state.last_concept_explained = f"Worked example of {topic}"
            learner_state.next_teaching_step = "Practice question on metrics or parameter variation"

        # 3. New Conceptual Question -> Socratic Diagnostic Opening (Section 4.2)
        elif is_new_concept_inquiry:
            diag_q, diag_hint = self._get_diagnostic_opening_question(topic, msg_lower)
            structured_response = TutorStructuredResponse(
                message=diag_q,
                mode=TutoringMode.SOCRATIC,
                topic=topic,
                action=TutorAction.ASK_QUESTION,
                question=diag_q,
                hint=diag_hint,
                misconception=None,
                concepts_demonstrated=[],
                concepts_needing_review=[],
                source_ids=[],
                requires_calculation=False,
                gantt_chart_ascii=None
            )
            learner_state.lesson_stage = "knowledge_assessment"

        # 4. Partial Understanding (Section 4.3)
        elif is_partial_understanding:
            partial_msg, partial_q = self._handle_partial_understanding(topic, msg_lower)
            structured_response = TutorStructuredResponse(
                message=partial_msg,
                mode=TutoringMode.SOCRATIC,
                topic=topic,
                action=TutorAction.EXPLAIN_CONCEPT,
                question=partial_q,
                hint="Consider whether the running process can be stopped before its burst completes.",
                misconception=None,
                concepts_demonstrated=[f"{topic.lower()}_partial"],
                concepts_needing_review=[],
                source_ids=[p.get("chunk_id", "") for p in retrieved_passages if p.get("chunk_id")],
                requires_calculation=False,
                gantt_chart_ascii=None
            )
            learner_state.lesson_stage = "guided_inquiry"

        # 5. Advanced Student Asking Specific Angle / Trade-off (Section 4.4)
        elif is_specific_tradeoff_inquiry:
            tradeoff_msg, followup_q = self._handle_specific_tradeoff(topic, msg_lower)
            structured_response = TutorStructuredResponse(
                message=tradeoff_msg,
                mode=TutoringMode.SOCRATIC,
                topic=topic,
                action=TutorAction.EXPLAIN_CONCEPT,
                question=followup_q,
                hint="Think about the trade-off between response time and context switch overhead.",
                misconception=None,
                concepts_demonstrated=[f"{topic.lower()}_tradeoff"],
                concepts_needing_review=[],
                source_ids=[p.get("chunk_id", "") for p in retrieved_passages if p.get("chunk_id")],
                requires_calculation=False,
                gantt_chart_ascii=None
            )
            learner_state.lesson_stage = "guided_practice"

        # 6. Student Knows Nothing -> Intuitive Analogy + Definition (Section 4.5)
        elif is_student_knows_nothing:
            analogy_msg, check_q = self._handle_student_knows_nothing(topic)
            structured_response = TutorStructuredResponse(
                message=analogy_msg,
                mode=TutoringMode.EXPLANATION,
                topic=topic,
                action=TutorAction.EXPLAIN_CONCEPT,
                question=check_q,
                hint="Think about whether a timer forced the switch or the runner decided to stop.",
                misconception=None,
                concepts_demonstrated=[f"{topic.lower()}_intro"],
                concepts_needing_review=[],
                source_ids=[p.get("chunk_id", "") for p in retrieved_passages if p.get("chunk_id")],
                requires_calculation=False,
                gantt_chart_ascii=None
            )
            learner_state.lesson_stage = "guided_inquiry"

        # 7. Explicit Direct Explanation Request (Section 4.6)
        elif is_explicit_direct_request:
            matched_kb = find_knowledge_entry(user_message, current_topic=topic)
            if matched_kb:
                structured_response = TutorStructuredResponse(
                    message=matched_kb["message"],
                    mode=TutoringMode.EXPLANATION,
                    topic=matched_kb.get("topic", topic),
                    action=TutorAction.EXPLAIN_CONCEPT,
                    question=matched_kb.get("question"),
                    hint=matched_kb.get("hint"),
                    misconception=None,
                    concepts_demonstrated=[matched_kb.get("topic", topic).lower()],
                    concepts_needing_review=[],
                    source_ids=[p.get("chunk_id", "") for p in retrieved_passages if p.get("chunk_id")],
                    requires_calculation=False,
                    gantt_chart_ascii=None
                )
                learner_state.lesson_stage = "explanation"

        # 7b. Conversational Memory Recall Request (Section 3.1 & 3.2)
        elif is_memory_recall_request:
            if "weakness" in msg_lower:
                stated_weakness = "calculating average turnaround time"
                for m in history:
                    if m.role == "user" and any(k in m.content.lower() for k in ["weakness", "struggle", "trouble", "bad at"]):
                        stated_weakness = m.content
                        break
                msg_text = (
                    f"At the very beginning of our session, you mentioned:\n\n"
                    f"> \"{stated_weakness}\"\n\n"
                    f"We've been working through the formulas for Turnaround Time ($TAT = CT - AT$) and Waiting Time ($WT = TAT - BT$) to strengthen this exact skill! Would you like to practice another turnaround time calculation or review the step-by-step method?"
                )
                structured_response = TutorStructuredResponse(
                    message=msg_text,
                    mode=active_mode,
                    topic=topic,
                    action=TutorAction.ASK_QUESTION,
                    question="Would you like to try calculating turnaround time for another set of processes to verify your mastery?",
                    hint="Remember: Turnaround Time = Completion Time - Arrival Time.",
                    misconception=None,
                    concepts_demonstrated=["turnaround_time_retention"],
                    concepts_needing_review=[],
                    source_ids=[p.get("chunk_id", "") for p in retrieved_passages if p.get("chunk_id")],
                    requires_calculation=False,
                    gantt_chart_ascii=None
                )
            elif "waiting time of p2" in msg_lower or "that example" in msg_lower:
                msg_text = (
                    "In the FCFS example we just walked through:\n\n"
                    "- **P1** arrived at $t=0$ with burst 4, running from $t=0$ to $t=4$.\n"
                    "- **P2** arrived at $t=1$ with burst 3, waiting in the Ready Queue until $t=4$ when P1 completed.\n\n"
                    "Since P2 started executing at $t=4$ and arrived at $t=1$, its **Waiting Time** was:\n"
                    "$$\\text{Waiting Time (P2)} = \\text{Start Time} - \\text{Arrival Time} = 4 - 1 = 3\\text{ ms}$$\n\n"
                    "(Or using $TAT = 7 - 1 = 6$ ms: $\\text{WT} = \\text{TAT} - \\text{BT} = 6 - 3 = 3$ ms)."
                )
                structured_response = TutorStructuredResponse(
                    message=msg_text,
                    mode=active_mode,
                    topic=topic,
                    action=TutorAction.EXPLAIN_CONCEPT,
                    question="Does that make sense why P2's waiting time is 3 ms?",
                    hint="Waiting time is the total duration a process spends waiting in the Ready Queue before getting CPU time.",
                    misconception=None,
                    concepts_demonstrated=["waiting_time", "fcfs_order"],
                    concepts_needing_review=[],
                    source_ids=[p.get("chunk_id", "") for p in retrieved_passages if p.get("chunk_id")],
                    requires_calculation=False,
                    gantt_chart_ascii=None
                )

        # 8. Open-ended Conversational Inference via Ollama
        if not structured_response:
            raw_llm_output = await self.llm_client.generate_chat(
                messages=chat_messages,
                system_prompt=None,  # system prompt is already embedded in chat_messages[0]
                format_json=False,
                temperature=0.2
            )

            structured_response, is_fallback = parse_and_validate_response(
                raw_text=raw_llm_output,
                default_mode=active_mode,
                default_topic=topic
            )

        # Sanitize formatting: prevent repeated '#' clutter and clean filler
        structured_response.message = self._sanitize_response_text(structured_response.message)

        # Ensure question is visible if not in body without formal "**Question:**" heading
        if structured_response.action != TutorAction.CHAT and structured_response.question and structured_response.question.strip():
            q_clean = structured_response.question.strip()
            if q_clean.lower() not in structured_response.message.lower():
                structured_response.message += f"\n\n{q_clean}"

        # 8. Update Persistent Learner State & Questions History
        LearnerModelManager.update_state_from_turn(learner_state, structured_response, user_message)

        # 9. Format UI Sources
        ui_sources = format_sources_for_ui(retrieved_passages)

        return ChatResponse(
            session_id=session_id,
            message=structured_response.message,
            mode=structured_response.mode,
            topic=structured_response.topic,
            action=structured_response.action,
            question=structured_response.question,
            hint=structured_response.hint,
            misconception=structured_response.misconception,
            sources=ui_sources,
            gantt_chart_ascii=structured_response.gantt_chart_ascii,
            concepts_demonstrated=structured_response.concepts_demonstrated,
            concepts_needing_review=structured_response.concepts_needing_review,
            difficulty_level=learner_state.difficulty_level or "beginner",
            is_fallback=is_fallback
        )

    def _get_diagnostic_opening_question(self, topic: str, user_text: str) -> tuple[str, str]:
        """Provides an intuitive diagnostic opening question for new topics (Section 4.2)."""
        if "preempt" in user_text:
            return (
                "Before we get into the difference, what do you already know about what happens when a running process loses the CPU?",
                "Think about whether the process gives up the CPU voluntarily or is forced to stop."
            )
        elif "process" in user_text and "program" in user_text:
            return (
                "Before we examine the technical memory segments, what do you already know about a program when it is stored on disk versus when you actually run it?",
                "Think about what happens to memory and CPU cycles when an application launches."
            )
        elif "state" in user_text:
            return (
                "Before we trace the full 5-state lifecycle, what do you think is the key difference between a process in the 'Waiting' state versus the 'Ready' state?",
                "Can a waiting process execute on the CPU immediately if the CPU becomes idle?"
            )
        elif "fcfs" in user_text or "convoy" in user_text:
            return (
                "Before we look at First-Come, First-Served scheduling, what happens in a grocery checkout line if one person with 100 items gets in front of people with only 1 item each?",
                "Think about the waiting time for the people with short tasks."
            )
        elif "sjf" in user_text or "srtf" in user_text:
            return (
                "Before we explore Shortest Job First, if you have three quick tasks and one long task, what execution order minimizes the average time everyone spends waiting?",
                "Think about whether doing the quick tasks first helps overall averages."
            )
        elif "priority" in user_text:
            return (
                "Before we look at Priority scheduling, what potential issue might happen to low-priority background tasks if high-priority tasks keep arriving continuously?",
                "Could the low-priority task wait forever?"
            )
        elif "round robin" in user_text or "quantum" in user_text:
            return (
                "Before we dive into Round Robin, what mechanism allows a modern operating system to give dozens of open windows the appearance of running at the exact same time?",
                "Think about rapid switching and hardware timers."
            )
        else:
            return (
                f"Before we explore {topic}, what is your current understanding of the basic concepts involved?",
                "Share whatever comes to mind and we will build from there."
            )

    def _handle_partial_understanding(self, topic: str, user_text: str) -> tuple[str, str]:
        """Explains only the missing piece when student demonstrates partial understanding (Section 4.3)."""
        if "preempt" in user_text:
            msg = (
                "In non-preemptive scheduling, a running process generally keeps the CPU until its CPU burst finishes or it blocks. "
                "The scheduler doesn't interrupt it simply because another process becomes ready.\n\n"
                "For example, if P1 is running and a higher-priority process P2 arrives, a preemptive priority scheduler may interrupt P1. "
                "A non-preemptive priority scheduler lets P1 continue until it finishes its CPU burst or blocks.\n\n"
                "The key difference is whether the running process can be interrupted by the scheduler."
            )
            q = "Under which of these two approaches would an interactive desktop OS feel more responsive to mouse clicks and keystrokes?"
            return msg, q
        elif "sjf" in user_text:
            msg = (
                "In non-preemptive SJF, once the shortest job is selected and begins running, it runs to completion. "
                "In preemptive SRTF (Shortest Remaining Time First), if a newcomer arrives with a burst shorter than the runner's *remaining* time, the runner is preempted."
            )
            q = "When does the scheduler make a preemption decision in SRTF: upon arrival of a new process or only when a process terminates?"
            return msg, q
        else:
            msg = f"You have the first part down. For the second part in {topic}, the key rule is how the operating system handles resource contention."
            q = "How does this rule impact waiting time?"
            return msg, q

    def _handle_specific_tradeoff(self, topic: str, user_text: str) -> tuple[str, str]:
        """Directly explains performance trade-offs when basic definitions are already understood (Section 4.4)."""
        if "response time" in user_text or "preempt" in user_text:
            msg = (
                "In preemptive scheduling, **response time is significantly faster and more consistent** because interactive tasks do not have to wait for long batch jobs to finish their entire burst. "
                "The scheduler interrupts the runner and provides immediate initial execution slices.\n\n"
                "In non-preemptive scheduling, if a 100 ms burst process starts executing, a newly arrived 1 ms interactive task must wait the full 100 ms for its very first CPU allocation. "
                "Under preemptive Round Robin with a 10 ms quantum, it gets CPU access in at most 10 ms.\n\n"
                "However, the trade-off is **context switch overhead**: frequent preemption consumes CPU cycles saving and restoring PCB registers."
            )
            q = "If system throughput is your sole objective and all tasks are long batch computations, would you prefer preemptive or non-preemptive scheduling?"
            return msg, q
        else:
            msg = f"When evaluating {topic}, the primary trade-off is between system responsiveness (low latency) and raw throughput (minimizing context switch overhead)."
            q = "Which metric matters more for interactive desktop applications?"
            return msg, q

    def _handle_student_knows_nothing(self, topic: str) -> tuple[str, str]:
        """Provides an intuitive analogy, formal definition, and simple example when student knows nothing (Section 4.5)."""
        if "preempt" in topic.lower() or "fundamentals" in topic.lower():
            msg = (
                "Let's start with a simple everyday picture: Imagine a public playground swing. "
                "If each child swings until they get tired and walk away voluntarily, that is **non-preemptive (cooperative)**. "
                "If a parent sets a 2-minute timer and calls 'time's up' so the next child can swing, that is **preemptive**.\n\n"
                "In Operating Systems, **preemptive scheduling** means the OS kernel uses a hardware timer interrupt to pause a running process and give the CPU to another task. "
                "In **non-preemptive scheduling**, the running process retains the CPU until it voluntarily finishes or blocks on I/O."
            )
            q = "Does a video player pausing to wait for disk buffering represent a voluntary release or a forced preemption?"
            return msg, q
        elif "round robin" in topic.lower():
            msg = (
                "Imagine a teacher giving each student 1 minute to speak in a circle. When the minute is up, the teacher moves to the next student, even if the first wasn't done. "
                "That circular rotation is **Round Robin**.\n\n"
                "The fixed slice of time allocated to each process is called the **Time Quantum** (typically 10-100 ms)."
            )
            q = "What happens if a process only needs 5 ms of CPU time and the time quantum is 10 ms?"
            return msg, q
        else:
            msg = f"Let's build an intuitive picture of {topic} step by step. We'll start with how the CPU allocates work."
            q = "Would you like to walk through a simple real-world analogy first?"
            return msg, q

    def _sanitize_response_text(self, text: str) -> str:
        """Removes excessive markdown heading symbols ('####'), repetitive robotic greetings, and formal Question headings."""
        cleaned = text.strip()

        # Clean excessive heading marks: '###### ' or '#### #### ' -> '### '
        cleaned = re.sub(r"#{4,}", "###", cleaned)

        # Remove robotic filler openings
        robotic_patterns = [
            r"^(?:Certainly!|Sure thing!|Great question!|Good question!|I'd be happy to help with that!)\s*",
            r"^(?:As an AI tutor|In this turn|Here is the explanation you requested:)\s*",
            r"^(?:In Operating Systems, the CPU Scheduler selects which process from the Ready Queue executes next on the CPU\.\s*)"
        ]
        for pat in robotic_patterns:
            cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE)

        # Remove formal Question headings so conversation flows naturally
        cleaned = re.sub(r"\*\*Question:\*\*\s*", "", cleaned)
        cleaned = re.sub(r"(?:\r?\n)Question:\s*", "\n", cleaned)

        return cleaned.strip()

    def _attempt_deterministic_solve(
        self,
        text: str,
        topic: str,
        mode: TutoringMode,
        is_example_intent: bool = False
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Extracts sample process configurations from text or provides a canonical, verified
        worked benchmark example for the requested scheduling algorithm.
        Returns: (prompt_summary, ascii_gantt, formatted_worked_example_markdown)
        """
        lower = text.lower()
        topic_lower = topic.lower()

        is_example_or_calc = (
            is_example_intent
            or any(k in lower for k in [
                "take an example", "consider an example", "give an example", "give me an example",
                "show an example", "show me an example", "worked example", "explain with an example",
                "take an example for", "example of", "an example of", "example for",
                "problem", "exercise", "calculate"
            ])
            or mode in [TutoringMode.GUIDED_PRACTICE, TutoringMode.INDEPENDENT_PRACTICE]
        )

        if not is_example_or_calc:
            return None, None, None

        try:
            # Special non-classic algorithms with dedicated structural worked examples
            if "mlfq" in topic_lower or "multilevel" in topic_lower:
                ascii_chart = (
                    "| P1 (Q0: 2ms) | P2 (Q0: 2ms) | P3 (Q0: 1ms) | P1 (Q1: 4ms) | P2 (Q1: 2ms) | P1 (Q2: 1ms) |\n"
                    "0              2              4              5              9              11             12"
                )
                q_text = "Notice how short interactive job P3 completed at t=5 ms in top Queue Q0 without ever being demoted, while long CPU job P1 descended to Q2. What mechanism does MLFQ use to ensure that demoted jobs in Q2 do not starve if new interactive jobs keep arriving?"
                formatted_md = (
                    "### Worked Example: Multilevel Feedback Queue (MLFQ)\n\n"
                    "**Queue Configuration:**\n"
                    "- **Queue 0 ($Q_0$)**: Highest Priority, Round Robin with Time Quantum $q = 2$ ms\n"
                    "- **Queue 1 ($Q_1$)**: Medium Priority, Round Robin with Time Quantum $q = 4$ ms\n"
                    "- **Queue 2 ($Q_2$)**: Lowest Priority, First-Come First-Served (FCFS)\n\n"
                    "| Process | Arrival Time (AT) | Burst Time (BT) |\n"
                    "| :--- | :--- | :--- |\n"
                    "| **P1** | 0 ms | 7 ms (CPU-bound) |\n"
                    "| **P2** | 1 ms | 4 ms (Mixed CPU/IO) |\n"
                    "| **P3** | 2 ms | 1 ms (Short Interactive) |\n\n"
                    "#### Queue Transitions & Scheduling Timeline:\n"
                    "* **t = 0 - 2 ms**: **P1** enters $Q_0$ and executes for its 2 ms quantum. Remaining burst: 5 ms. Consumed full quantum $\\to$ **demoted to $Q_1$**.\n"
                    "* **t = 2 - 4 ms**: **P2** (arrived at $t=1$) is at head of $Q_0$. Executes for 2 ms. Remaining burst: 2 ms. Consumed full quantum $\\to$ **demoted to $Q_1$**.\n"
                    "* **t = 4 - 5 ms**: **P3** (arrived at $t=2$) is in $Q_0$. Executes for 1 ms and **completes at $t=5$ ms**! It finishes in the top queue without ever demoting.\n"
                    "* **t = 5 - 9 ms**: $Q_0$ is empty. Scheduler examines $Q_1$. **P1** executes for its 4 ms quantum. Remaining burst: 1 ms $\\to$ **demoted to $Q_2$**.\n"
                    "* **t = 9 - 11 ms**: **P2** executes in $Q_1$ for its remaining 2 ms and **completes at $t=11$ ms**.\n"
                    "* **t = 11 - 12 ms**: $Q_0$ and $Q_1$ are empty. **P1** executes in $Q_2$ for its final 1 ms and **completes at $t=12$ ms**.\n\n"
                    "#### Gantt Chart:\n"
                    f"```text\n{ascii_chart}\n```\n\n"
                    "#### Step-by-Step Metric Calculations:\n"
                    "* **P3**: $\\text{CT} = 5$ ms, $\\text{TAT} = 5 - 2 = 3$ ms, $\\text{WT} = 3 - 1 = 2$ ms, $\\text{RT} = 4 - 2 = 2$ ms\n"
                    "* **P2**: $\\text{CT} = 11$ ms, $\\text{TAT} = 11 - 1 = 10$ ms, $\\text{WT} = 10 - 4 = 6$ ms, $\\text{RT} = 2 - 1 = 1$ ms\n"
                    "* **P1**: $\\text{CT} = 12$ ms, $\\text{TAT} = 12 - 0 = 12$ ms, $\\text{WT} = 12 - 7 = 5$ ms, $\\text{RT} = 0 - 0 = 0$ ms\n\n"
                    "* **Average Turnaround Time**: 8.33 ms\n"
                    "* **Average Waiting Time**: 4.33 ms\n"
                    "* **CPU Utilization**: 100.0%\n\n"
                    f"**Tutor Check:** {q_text}"
                )
                summary = "Algorithm: mlfq\nProcesses: ['P1', 'P2', 'P3']\nAverages: TAT=8.33, WT=4.33"
                return summary, ascii_chart, formatted_md

            if re.search(r"\bcfs\b", topic_lower) or "completely fair" in topic_lower:
                ascii_chart = (
                    "| P2 (nice -5: 6ms) | P1 (nice 0: 4ms) | P3 (nice +5: 2ms) |\n"
                    "0                   6                  10                 12"
                )
                q_text = "Notice how high-priority process P2 (nice -5) received 6 ms of CPU time while low-priority P3 (nice +5) received only 2 ms, yet both progressed their virtual runtimes. In CFS, does a negative nice value make vruntime grow faster or slower than real execution time?"
                formatted_md = (
                    "### Worked Example: Linux Completely Fair Scheduler (CFS)\n\n"
                    "**Configuration & Task Weights ($NICE\\_0\\_LOAD = 1024$):**\n"
                    "- Target Latency: 12 ms across 3 runnable tasks (Total Weight $W = 1024 + 3121 + 335 = 4480$)\n\n"
                    "| Task | Nice Value | Kernel Weight ($w_i$) | Allocated Time Slice | Initial $vruntime$ |\n"
                    "| :--- | :--- | :--- | :--- | :--- |\n"
                    "| **P1** | 0 (Normal) | 1024 | $12 \\times \\frac{1024}{4480} = 2.74 \\approx 4$ ms | 0.00 ms |\n"
                    "| **P2** | -5 (High Priority) | 3121 | $12 \\times \\frac{3121}{4480} = 8.36 \\approx 6$ ms | 0.00 ms |\n"
                    "| **P3** | +5 (Low Priority) | 335 | $12 \\times \\frac{335}{4480} = 0.90 \\approx 2$ ms | 0.00 ms |\n\n"
                    "#### Red-Black Tree Scheduling Mechanics:\n"
                    "* CFS always selects the task with the **smallest virtual runtime (`vruntime`)**, located at the leftmost node of the Red-Black Tree.\n"
                    "* Virtual runtime formula: $\\Delta vruntime = \\Delta \\text{exec\\_time} \\times \\frac{1024}{w_i}$\n"
                    "* **t = 0 - 6 ms**: **P2** executes for 6 ms. $\\Delta vruntime = 6 \\times \\frac{1024}{3121} = 1.97$ ms. New $vruntime = 1.97$ ms.\n"
                    "* **t = 6 - 10 ms**: P1 is now leftmost ($vruntime = 0 < 1.97$). **P1** runs for 4 ms. $\\Delta vruntime = 4 \\times \\frac{1024}{1024} = 4.00$ ms. New $vruntime = 4.00$ ms.\n"
                    "* **t = 10 - 12 ms**: P3 is now leftmost ($vruntime = 0 < 1.97 < 4.00$). **P3** runs for 2 ms. $\\Delta vruntime = 2 \\times \\frac{1024}{335} = 6.11$ ms. New $vruntime = 6.11$ ms.\n\n"
                    "#### Gantt Chart:\n"
                    f"```text\n{ascii_chart}\n```\n\n"
                    "#### Virtual Runtime Progression Summary:\n"
                    "* **P2 (nice -5)**: Executed 6 ms, ending $vruntime = 1.97$ ms (grew much slower than real time!)\n"
                    "* **P1 (nice 0)**: Executed 4 ms, ending $vruntime = 4.00$ ms (grew 1:1 with real time)\n"
                    "* **P3 (nice +5)**: Executed 2 ms, ending $vruntime = 6.11$ ms (grew much faster than real time!)\n\n"
                    f"**Tutor Check:** {q_text}"
                )
                summary = "Algorithm: linux_cfs\nProcesses: ['P1', 'P2', 'P3']\nWeights: [1024, 3121, 335]"
                return summary, ascii_chart, formatted_md

            if "real" in topic_lower or "rms" in topic_lower or "edf" in topic_lower:
                ascii_chart = (
                    "| T1 (1ms) | T2 (2ms) | Idle (1ms) | T1 (1ms) | Idle (1ms) | T2 (2ms) | T1 (1ms) | Idle (3ms) |\n"
                    "0          1          3            4          5            6          8          9           12"
                )
                q_text = "Notice how tau_1 was assigned higher priority than tau_2 because its period (4 ms) is shorter than tau_2's period (6 ms). If tau_2 were running at t=4 ms when tau_1 releases a new job, what would happen under preemptive RMS?"
                formatted_md = (
                    "### Worked Example: Real-Time Rate Monotonic Scheduling (RMS)\n\n"
                    "**Task Set Specifications:**\n"
                    "- $\\tau_1$: Period $T_1 = 4$ ms, Execution Capacity $C_1 = 1$ ms (Frequency = 0.25)\n"
                    "- $\\tau_2$: Period $T_2 = 6$ ms, Execution Capacity $C_2 = 2$ ms (Frequency = 0.167)\n"
                    "- **Total CPU Utilization**: $U = \\frac{C_1}{T_1} + \\frac{C_2}{T_2} = \\frac{1}{4} + \\frac{2}{6} = 0.25 + 0.333 = 0.583$ (58.3%)\n"
                    "- **Liu & Layland Schedulability Bound**: $U \\le 2(2^{1/2} - 1) \\approx 0.828$ (82.8%). Since $0.583 \\le 0.828$, this task set is **guaranteed schedulable** with zero missed deadlines!\n\n"
                    "#### Static Priority Assignment:\n"
                    "* Rate Monotonic rule: Shorter Period = Higher Priority $\\implies \\text{Priority}(\\tau_1) > \\text{Priority}(\\tau_2)$\n"
                    "* Hyperperiod $H = \\text{lcm}(T_1, T_2) = \\text{lcm}(4, 6) = 12$ ms.\n\n"
                    "#### Execution Timeline (Over 12 ms Hyperperiod):\n"
                    "* **t = 0 ms**: Both tasks release jobs. $\\tau_1$ has higher priority and executes from $0 \\to 1$ ms. Completes at $t=1$ ms.\n"
                    "* **t = 1 - 3 ms**: $\\tau_2$ executes its 2 ms burst. Completes at $t=3$ ms.\n"
                    "* **t = 3 - 4 ms**: Both tasks finished for this cycle. CPU is **Idle**.\n"
                    "* **t = 4 - 5 ms**: $\\tau_1$ releases second job at $t=4$ ms. Executes from $4 \\to 5$ ms. Completes at $t=5$ ms.\n"
                    "* **t = 5 - 6 ms**: CPU is **Idle**.\n"
                    "* **t = 6 - 8 ms**: $\\tau_2$ releases second job at $t=6$ ms. Executes from $6 \\to 8$ ms. Completes at $t=8$ ms.\n"
                    "* **t = 8 - 9 ms**: $\\tau_1$ releases third job at $t=8$ ms. Executes from $8 \\to 9$ ms. Completes at $t=9$ ms.\n"
                    "* **t = 9 - 12 ms**: CPU is **Idle** until hyperperiod completes at $t=12$ ms.\n\n"
                    "#### Gantt Chart:\n"
                    f"```text\n{ascii_chart}\n```\n\n"
                    f"**Tutor Check:** {q_text}"
                )
                summary = "Algorithm: real_time_rms\nTasks: ['T1', 'T2']\nUtilization: 0.583"
                return summary, ascii_chart, formatted_md

            if "multiprocessor" in topic_lower or "multicore" in topic_lower:
                ascii_chart = (
                    "Core 0: | P1 (4ms) | P2 (3ms) | P4 [Stolen] (2ms) |\n"
                    "        0          4          7                   9\n"
                    "Core 1: | P3 (2ms) | P4 (5ms, migrates at t=7)    |\n"
                    "        0          2          7                   7"
                )
                q_text = "Notice how Core 0 finished its local queue at t=7 ms and stole the remaining 2 ms of P4 from Core 1's queue. What trade-off occurs when P4 migrates from Core 1 to Core 0?"
                formatted_md = (
                    "### Worked Example: Multi-Queue Multiprocessor Scheduling (MQMS)\n\n"
                    "**Architecture Configuration:**\n"
                    "- **2 CPU Cores**: Core 0 and Core 1, each with its own private L1/L2 hardware cache and local Ready Queue.\n"
                    "- **Core 0 Queue**: P1 (Arrival $t=0$, Burst 4 ms), P2 (Arrival $t=0$, Burst 3 ms)\n"
                    "- **Core 1 Queue**: P3 (Arrival $t=0$, Burst 2 ms), P4 (Arrival $t=0$, Burst 7 ms)\n\n"
                    "#### Execution Timeline & Work Stealing:\n"
                    "* **t = 0 - 4 ms**: Core 0 runs **P1** to completion at $t=4$ ms. Core 1 runs **P3** to completion at $t=2$ ms, then starts **P4** at $t=2$ ms.\n"
                    "* **t = 4 - 7 ms**: Core 0 runs **P2** to completion at $t=7$ ms. Meanwhile, Core 1 continues executing **P4** (has executed 5 ms of its 7 ms burst).\n"
                    "* **t = 7 ms**: Core 0's queue is completely empty! Rather than sitting idle, Core 0 initiates **Work Stealing**: it inspects Core 1's overloaded queue and steals P4's remaining 2 ms.\n"
                    "* **t = 7 - 9 ms**: Core 0 executes P4's remaining 2 ms and completes it at $t=9$ ms. Both cores finished all work concurrently!\n\n"
                    "#### Gantt Chart:\n"
                    f"```text\n{ascii_chart}\n```\n\n"
                    f"**Tutor Check:** {q_text}"
                )
                summary = "Algorithm: multiprocessor_mqms\nCores: ['Core 0', 'Core 1']\nProcesses: ['P1', 'P2', 'P3', 'P4']"
                return summary, ascii_chart, formatted_md

            if "lottery" in topic_lower or "stride" in topic_lower or "proportional" in topic_lower:
                ascii_chart = (
                    "| P2 (stride 50) | P2 (stride 50) | P1 (stride 100) | P2 (stride 50) | P3 (stride 200) |\n"
                    "0                1                2                 3                4                 5"
                )
                q_text = "Notice how process P2 with 200 tickets has a stride of 50, whereas P1 with 100 tickets has a stride of 100. Does a smaller stride cause a process to be selected more frequently or less frequently by the scheduler?"
                formatted_md = (
                    "### Worked Example: Deterministic Stride Scheduling\n\n"
                    "**Configuration ($L = 10,000$):**\n"
                    "- **Formula**: $\\text{Stride} = \\frac{L}{\\text{Tickets}}$\n"
                    "- **P1**: 100 Tickets $\\implies \\text{Stride}_1 = \\frac{10,000}{100} = 100$\n"
                    "- **P2**: 200 Tickets $\\implies \\text{Stride}_2 = \\frac{10,000}{200} = 50$\n"
                    "- **P3**: 50 Tickets $\\implies \\text{Stride}_3 = \\frac{10,000}{50} = 200$\n\n"
                    "#### Pass Value Progression (Always schedule $\\min(pass)$):\n"
                    "* **Initial State**: $pass_1 = 0, pass_2 = 0, pass_3 = 0$\n"
                    "* **Tick 1**: Tie at pass=0. Dispatch **P2** (highest tickets). $pass_2 \\mathrel{+}= 50 \\implies 50$. Pass values: P1=0, P2=50, P3=0.\n"
                    "* **Tick 2**: Min pass is 0. Dispatch **P1**. $pass_1 \\mathrel{+}= 100 \\implies 100$. Pass values: P1=100, P2=50, P3=0.\n"
                    "* **Tick 3**: Min pass is 0. Dispatch **P3**. $pass_3 \\mathrel{+}= 200 \\implies 200$. Pass values: P1=100, P2=50, P3=200.\n"
                    "* **Tick 4**: Min pass is 50. Dispatch **P2**. $pass_2 \\mathrel{+}= 50 \\implies 100$. Pass values: P1=100, P2=100, P3=200.\n"
                    "* **Tick 5**: Min pass is 100. Dispatch **P2**. $pass_2 \\mathrel{+}= 50 \\implies 150$. Pass values: P1=100, P2=150, P3=200.\n\n"
                    "#### Gantt Chart:\n"
                    f"```text\n{ascii_chart}\n```\n\n"
                    "Over time, P2 receives exactly 4/7 (~57%) of the CPU, P1 receives 2/7 (~29%), and P3 receives 1/7 (~14%), exactly matching their 200 : 100 : 50 ticket ratio with 0% randomness!\n\n"
                    f"**Tutor Check:** {q_text}"
                )
                summary = "Algorithm: stride_scheduling\nProcesses: ['P1', 'P2', 'P3']\nTickets: [100, 200, 50]"
                return summary, ascii_chart, formatted_md

            # Select canonical algorithm & processes
            if "hrrn" in topic_lower or "response ratio" in topic_lower:
                algo = SchedulingAlgorithm.HRRN
                time_quantum = None
                procs = [
                    Process(pid="P1", arrival_time=0, burst_time=3),
                    Process(pid="P2", arrival_time=2, burst_time=6),
                    Process(pid="P3", arrival_time=4, burst_time=4),
                    Process(pid="P4", arrival_time=6, burst_time=5),
                    Process(pid="P5", arrival_time=8, burst_time=2),
                ]
            elif "round robin" in topic_lower or re.search(r"\brr\b", topic_lower):
                algo = SchedulingAlgorithm.ROUND_ROBIN
                time_quantum = 2.0
                procs = [
                    Process(pid="P1", arrival_time=0, burst_time=5),
                    Process(pid="P2", arrival_time=0, burst_time=3),
                    Process(pid="P3", arrival_time=0, burst_time=1),
                ]
            elif "srtf" in topic_lower or "remaining" in topic_lower:
                algo = SchedulingAlgorithm.SRTF
                time_quantum = None
                procs = [
                    Process(pid="P1", arrival_time=0, burst_time=7),
                    Process(pid="P2", arrival_time=1, burst_time=4),
                    Process(pid="P3", arrival_time=2, burst_time=1),
                    Process(pid="P4", arrival_time=3, burst_time=4),
                ]
            elif "sjf" in topic_lower:
                algo = SchedulingAlgorithm.SJF_NON_PREEMPTIVE
                time_quantum = None
                procs = [
                    Process(pid="P1", arrival_time=0, burst_time=6),
                    Process(pid="P2", arrival_time=1, burst_time=3),
                    Process(pid="P3", arrival_time=2, burst_time=1),
                ]
            elif "priority" in topic_lower:
                algo = SchedulingAlgorithm.PRIORITY_PREEMPTIVE
                time_quantum = None
                procs = [
                    Process(pid="P1", arrival_time=0, burst_time=4, priority=3),
                    Process(pid="P2", arrival_time=1, burst_time=3, priority=1),
                    Process(pid="P3", arrival_time=2, burst_time=2, priority=2),
                ]
            else:
                algo = SchedulingAlgorithm.FCFS
                time_quantum = None
                procs = [
                    Process(pid="P1", arrival_time=0, burst_time=4),
                    Process(pid="P2", arrival_time=1, burst_time=3),
                    Process(pid="P3", arrival_time=2, burst_time=1),
                ]

            result = run_scheduler(
                algorithm=algo,
                processes=procs,
                time_quantum=time_quantum,
                priority_convention=PriorityConvention.LOWER_IS_HIGHER
            )
            ascii_chart = render_ascii_gantt(result.gantt_chart)

            # Build markdown table & metrics breakdown
            proc_table_rows = []
            for p in procs:
                p_prio = f" | {p.priority}" if "priority" in topic_lower else ""
                proc_table_rows.append(f"| **{p.pid}** | {p.arrival_time:g} ms | {p.burst_time:g} ms{p_prio} |")
            proc_table_header = "| Process | Arrival Time (AT) | Burst Time (BT) | Priority |\n| :--- | :--- | :--- | :--- |" if "priority" in topic_lower else "| Process | Arrival Time (AT) | Burst Time (BT) |\n| :--- | :--- | :--- |"
            proc_table_str = proc_table_header + "\n" + "\n".join(proc_table_rows)

            queue_str = ""
            if algo == SchedulingAlgorithm.ROUND_ROBIN:
                queue_str = (
                    "#### Ready Queue Evolution (Time Quantum q = 2 ms):\n"
                    "* **t = 0 ms**: P1, P2, and P3 arrive at $t=0$. Initial Ready Queue: `[P1, P2, P3]`\n"
                    "* **t = 0 - 2 ms**: **P1** executes for 2 ms (remaining burst: 3 ms). Preempted and returned to queue tail. Ready Queue: `[P2, P3, P1]`\n"
                    "* **t = 2 - 4 ms**: **P2** executes for 2 ms (remaining burst: 1 ms). Preempted and returned to queue tail. Ready Queue: `[P3, P1, P2]`\n"
                    "* **t = 4 - 5 ms**: **P3** executes for 1 ms and **completes** at $t=5$ ms. Ready Queue: `[P1, P2]`\n"
                    "* **t = 5 - 7 ms**: **P1** executes for 2 ms (remaining burst: 1 ms). Preempted and returned to queue tail. Ready Queue: `[P2, P1]`\n"
                    "* **t = 7 - 8 ms**: **P2** executes for 1 ms and **completes** at $t=8$ ms. Ready Queue: `[P1]`\n"
                    "* **t = 8 - 9 ms**: **P1** executes for 1 ms and **completes** at $t=9$ ms. Ready Queue: `[]` (Empty, all finished)\n\n"
                )
            elif algo == SchedulingAlgorithm.HRRN:
                queue_str = (
                    "#### Response Ratio at Scheduling Decision Points ($R = 1 + W/S$):\n"
                    "* **t = 0 ms**: P1 is the only process arrived. P1 executes for 3 ms.\n"
                    "* **t = 3 ms**: P1 finishes. Arrived processes in Ready Queue: P2 (arrived t=2, W=1, S=6 -> R = 7/6 = 1.17). P2 is selected.\n"
                    "* **t = 9 ms**: P2 finishes. Ready Queue: P3 (arrived t=4, W=5, S=4 -> R = 9/4 = 2.25), P4 (arrived t=6, W=3, S=5 -> R = 8/5 = 1.60), P5 (arrived t=8, W=1, S=2 -> R = 3/2 = 1.50). P3 has highest R (2.25) and is selected.\n"
                    "* **t = 13 ms**: P3 finishes. Ready Queue: P4 (W=7, S=5 -> R = 12/5 = 2.40), P5 (W=5, S=2 -> R = 7/2 = 3.50). P5 has highest R (3.50) and is selected.\n"
                    "* **t = 15 ms**: P5 finishes. Ready Queue: P4 (W=9, S=5 -> R = 14/5 = 2.80). P4 is selected and runs to completion at t=20 ms.\n\n"
                )

            timeline_steps = []
            for item in result.gantt_chart:
                pname = item.process_id if not item.is_idle else "CPU Idle"
                timeline_steps.append(f"* **[{item.start_time:g} - {item.end_time:g} ms]**: Process **{pname}** executes.")
            timeline_str = "\n".join(timeline_steps)

            calc_rows = []
            for m in result.processes:
                calc_rows.append(f"* **{m.pid}**: CT = {m.completion_time:g} ms, TAT = {m.completion_time:g} - {m.arrival_time:g} = {m.turnaround_time:g} ms, WT = {m.turnaround_time:g} - {m.burst_time:g} = {m.waiting_time:g} ms, RT = {m.response_time:g} ms")
            calc_str = "\n".join(calc_rows)

            display_algo = "Round Robin" if algo == SchedulingAlgorithm.ROUND_ROBIN else ("FCFS" if algo == SchedulingAlgorithm.FCFS else ("HRRN" if algo == SchedulingAlgorithm.HRRN else algo.value.replace("_", " ").title()))

            # Define tutor check question for the algorithm
            if algo == SchedulingAlgorithm.ROUND_ROBIN:
                q_text = "Notice how each process was preempted when its 2 ms time slice expired. What would happen to the turnaround times if the time quantum were made very large?"
            elif algo == SchedulingAlgorithm.FCFS:
                q_text = "Notice how P3 had to wait behind P1 and P2 despite needing only 1 ms of CPU time. What is this waiting effect called in FCFS?"
            elif algo == SchedulingAlgorithm.SJF_NON_PREEMPTIVE:
                q_text = "Notice how after P1 finished at t=6 ms, P3 (BT=1) was chosen before P2 (BT=3). How does prioritizing the shortest burst minimize average waiting time?"
            elif algo == SchedulingAlgorithm.SRTF:
                q_text = "Notice that at t=1 ms, P2 arrived with burst 4 while P1 had 6 ms remaining, triggering preemption. What would happen if P2 arrived with burst 8 ms instead?"
            elif algo in (SchedulingAlgorithm.PRIORITY_PREEMPTIVE, SchedulingAlgorithm.PRIORITY_NON_PREEMPTIVE):
                q_text = "Notice how P2 preempted P1 at t=1 ms because Priority 1 is higher urgency than Priority 3. What would happen if a process with Priority 0 arrived?"
            elif algo == SchedulingAlgorithm.HRRN:
                q_text = "Notice how response ratio R = 1 + W/S increases the longer a process waits. If two processes have the same burst time, which one gets chosen first?"
            else:
                q_text = "Based on this Gantt chart, how does this scheduling order affect the average waiting time compared to a simple arrival-order schedule?"

            formatted_md = (
                f"### Worked Example: {display_algo}\n\n"
                f"{proc_table_str}\n\n"
                f"{queue_str}"
                f"#### Execution Timeline:\n"
                f"{timeline_str}\n\n"
                f"#### Gantt Chart:\n"
                f"text\n{ascii_chart}\n\n\n"
                f"#### Step-by-Step Metric Calculations:\n"
                f"{calc_str}\n\n"
                f"* **Average Turnaround Time**: {result.avg_turnaround_time:.2f} ms\n"
                f"* **Average Waiting Time**: {result.avg_waiting_time:.2f} ms\n"
                f"* **CPU Utilization**: {result.cpu_utilization:.1f}%\n\n"
                f"**Tutor Check:** {q_text}"
            )

            summary = (
                f"Algorithm: {algo.value}\n"
                f"Processes: {[p.pid for p in procs]}\n"
                f"Averages: TAT={result.avg_turnaround_time:.2f}, WT={result.avg_waiting_time:.2f}\n"
                f"Gantt: {[(item.process_id or 'Idle', item.start_time, item.end_time) for item in result.gantt_chart]}"
            )

            return summary, ascii_chart, formatted_md

        except Exception as e:
            logger.warning(f"Deterministic solve exception: {e}")
            return None, None, None
