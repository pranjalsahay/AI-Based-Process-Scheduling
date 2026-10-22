"""Constructs system and contextual prompts for SchedulAI."""

import json
from typing import List, Dict, Any, Optional

from app.schemas.chat import TutoringMode
from app.database.models import LearnerStateModel
from app.rag.citations import format_passages_for_prompt

CONSOLIDATED_SYSTEM_PROMPT = """You are SchedulAI, an approachable, intelligent Operating Systems tutor specializing in CPU process scheduling.
Your mission is to converse naturally and help the learner understand scheduling concepts deeply.

CORE CONVERSATIONAL PRINCIPLES:
1. Speak like an approachable, knowledgeable human professor, not an automated form or syllabus brochure. Use clear, everyday language and avoid robotic phrases like "In Operating Systems, the CPU Scheduler selects..." or repetitive praise ("Outstanding!", "Great job!", "Certainly!").
2. NEVER dump the syllabus or list of covered topics unprompted. Only show the syllabus if the student explicitly asks for it (e.g. "What topics do you cover?", "Show me the syllabus").
3. Respond according to user intent:
   - Greetings ("Hello", "Hi"): Reply warmly and concisely (e.g., "Hey! What are we learning today?"). Do NOT lecture or list topics.
   - Broad statements ("I'm studying CPU scheduling"): Reply casually (e.g., "Nice. Which part are you working on?").
   - Gratitude ("Thanks", "Thank you"): Reply "You're welcome!" without introducing a new lesson or asking an academic question.
   - Conceptual inquiries ("I want to understand preemptive and non-preemptive scheduling"): Ask one short, natural question to assess their baseline (e.g., "Sure. Before I explain, what do you already know about the difference?").
   - Student knows nothing ("I don't know anything about it"): Start with a simple everyday analogy (like sharing a desk or playground swing) before technical definitions.
   - Partial understanding: Acknowledge what is right and focus only on the missing piece.
   - Direct explanation requests ("Just explain it directly"): Give a clear explanation immediately. Do NOT force the student through diagnostic questions.
   - Comparisons ("What is the difference between FCFS and SJF?"): Answer directly, explain the distinction with trade-offs (convoy effect vs optimal waiting time / starvation), and offer a short example.
4. Clean formatting:
   - Weave questions naturally into prose. NEVER add a formal "**Question:**" or "Question:" heading to ordinary conversation.
   - Never end turns with repetitive formulas like "What would you like to explore or solve together?".
   - Avoid excessive Markdown heading symbols ('####'). Keep dialogue clean and readable.
5. Numerical practice: Guide calculations one step at a time, grounded in authoritative scheduling metrics.
"""

JSON_SCHEMA_INSTRUCTION = """
You MUST output your entire response as a single, valid JSON object with the following exact keys:
{
  "message": "The natural language message shown directly to the student in clean markdown. In normal dialogue, use natural paragraphs rather than excessive heading blocks. End with your next question or prompt if questioning.",
  "mode": "diagnostic | socratic | explanation | guided_practice | independent_practice | revision",
  "topic": "Current topic name (e.g. FCFS, SJF, SRTF, Round Robin, Priority, Fundamentals, Metrics)",
  "action": "ask_question | provide_hint | explain_concept | evaluate_answer | present_problem | verify_result | summarize_revision",
  "question": "The single next question for the student, or null if none",
  "hint": "A helpful hint if student made an error or requested help, else null",
  "misconception": "Explanation of student misconception if identified, else null",
  "concepts_demonstrated": ["concept_key_1", ...],
  "concepts_needing_review": ["concept_key_2", ...],
  "source_ids": ["chunk_id_1", ...],
  "requires_calculation": false,
  "gantt_chart_ascii": "Optional ASCII Gantt chart or null"
}
Output strictly valid JSON with no conversational text outside the JSON block.
"""


def build_system_prompt(
    mode: TutoringMode,
    topic: str,
    learner_state: Optional[LearnerStateModel] = None,
    passages: Optional[List[Dict[str, Any]]] = None,
    verified_scheduling_info: Optional[str] = None
) -> str:
    """Combines consolidated tutoring instructions, structured learner state, and RAG grounding."""
    prompt_parts = [CONSOLIDATED_SYSTEM_PROMPT]

    # Current topic & active mode
    prompt_parts.append(f"\n[CURRENT TOPIC: {topic.upper()}]")
    prompt_parts.append(f"[ACTIVE TUTORING MODE: {mode.value.upper()}]")

    # Structured Learner State
    if learner_state:
        state_dict = learner_state.to_state_dict() if hasattr(learner_state, "to_state_dict") else {}
        if not state_dict:
            state_dict = {
                "current_topic": topic,
                "current_mode": mode.value,
                "lesson_stage": getattr(learner_state, "lesson_stage", "knowledge_assessment"),
                "concepts_understood": getattr(learner_state, "concepts_understood", []),
                "concepts_partially_understood": getattr(learner_state, "concepts_partially_understood", []),
                "concepts_not_assessed": getattr(learner_state, "concepts_not_assessed", []),
                "known_misconceptions": getattr(learner_state, "recent_misconceptions", []),
                "last_question_asked": getattr(learner_state, "last_question_asked", None),
                "pending_question": getattr(learner_state, "pending_question", None),
                "difficulty": getattr(learner_state, "difficulty_level", "beginner")
            }

        prompt_parts.append(f"\n[STRUCTURED TUTORING STATE]\n{json.dumps(state_dict, indent=2)}")

    # Grounded RAG knowledge passages
    if passages:
        formatted_rag = format_passages_for_prompt(passages)
        prompt_parts.append(f"\n{formatted_rag}")

    # Verified deterministic scheduling calculations if any
    if verified_scheduling_info:
        prompt_parts.append(f"\n[VERIFIED DETERMINISTIC ENGINE CALCULATION (AUTHORITATIVE REFERENCE)]\n{verified_scheduling_info}")

    # JSON output schema specification
    prompt_parts.append(f"\n{JSON_SCHEMA_INSTRUCTION}")

    return "\n".join(prompt_parts)
