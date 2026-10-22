"""Learner modeling, mastery heuristics, and adaptive tutoring state management."""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.database.models import LearnerStateModel
from app.schemas.chat import TutoringMode, TutorStructuredResponse, TutorAction

TOPIC_CONCEPTS: Dict[str, List[str]] = {
    "Fundamentals": [
        "process_vs_program",
        "process_states",
        "state_transitions",
        "pcb_structure",
        "dispatcher_vs_scheduler",
        "context_switching",
        "cpu_io_burst",
        "schedulers_types"
    ],
    "Preemption": [
        "preemption_definition",
        "non_preemptive_cooperative",
        "hardware_timer_interrupt",
        "silberschatz_circumstances",
        "kernel_preemption"
    ],
    "FCFS": [
        "fcfs_fifo_order",
        "non_preemptive_nature",
        "convoy_effect",
        "waiting_time_impact"
    ],
    "SJF": [
        "shortest_burst_selection",
        "optimal_waiting_time",
        "burst_prediction_exponential_smoothing",
        "starvation_vulnerability"
    ],
    "SRTF": [
        "remaining_burst_comparison",
        "preemptive_interrupts",
        "context_switch_overhead",
        "starvation_of_long_jobs"
    ],
    "Priority": [
        "priority_number_convention",
        "preemptive_vs_non_preemptive_priority",
        "starvation_indefinite_blocking",
        "aging_solution"
    ],
    "Round Robin": [
        "circular_queue_mechanism",
        "time_quantum_selection",
        "timer_preemption",
        "80_percent_rule_tradeoff"
    ],
    "Metrics": [
        "completion_time",
        "turnaround_time_formula",
        "waiting_time_formula",
        "response_time_formula",
        "cpu_utilization_throughput",
        "gantt_chart_construction"
    ]
}


class LearnerModelManager:
    """Manages student proficiency tracking, lesson stages, and adaptive state updates."""

    @staticmethod
    def initialize_topic_concepts(state: LearnerStateModel, topic: str):
        """Initializes unassessed concepts when entering or switching topics."""
        topic_key = "Preemption" if "preempt" in topic.lower() else topic
        cur_not_assessed = state.concepts_not_assessed
        all_topic_concepts = TOPIC_CONCEPTS.get(topic_key, TOPIC_CONCEPTS.get("Fundamentals", []))

        # Filter out already understood concepts
        understood = set(state.concepts_understood)
        partial = set(state.concepts_partially_understood)
        needed = [c for c in all_topic_concepts if c not in understood and c not in partial]
        state.concepts_not_assessed = needed

    @staticmethod
    def handle_topic_switch(state: LearnerStateModel, new_topic: str):
        """Preserves learning progress of the old topic and restores progress of new topic if present."""
        old_topic = state.current_topic
        if old_topic and old_topic != new_topic:
            progress = state.topic_progress
            progress[old_topic] = {
                "lesson_stage": state.lesson_stage or "knowledge_assessment",
                "concepts_understood": state.concepts_understood,
                "concepts_partially_understood": state.concepts_partially_understood,
                "concepts_not_assessed": state.concepts_not_assessed,
                "recent_misconceptions": state.recent_misconceptions,
                "difficulty_level": state.difficulty_level or "beginner",
                "current_subtopic": state.current_subtopic,
                "last_concept_explained": state.last_concept_explained,
                "next_teaching_step": state.next_teaching_step
            }
            state.topic_progress = progress

            # Restore previous progress if user already visited new_topic
            if new_topic in progress:
                saved = progress[new_topic]
                state.lesson_stage = saved.get("lesson_stage", "knowledge_assessment")
                state.concepts_understood = saved.get("concepts_understood", [])
                state.concepts_partially_understood = saved.get("concepts_partially_understood", [])
                state.concepts_not_assessed = saved.get("concepts_not_assessed", [])
                state.recent_misconceptions = saved.get("recent_misconceptions", [])
                state.difficulty_level = saved.get("difficulty_level", "beginner")
                state.current_subtopic = saved.get("current_subtopic")
                state.last_concept_explained = saved.get("last_concept_explained")
                state.next_teaching_step = saved.get("next_teaching_step")
            else:
                state.lesson_stage = "knowledge_assessment"
                state.current_subtopic = None
                state.last_concept_explained = None
                state.next_teaching_step = None
                LearnerModelManager.initialize_topic_concepts(state, new_topic)

            state.current_topic = new_topic

    @staticmethod
    def update_state_from_turn(
        state: LearnerStateModel,
        structured_response: TutorStructuredResponse,
        user_input: str
    ) -> LearnerStateModel:
        """
        Updates the persistent learner state based on validated tutoring decisions,
        distinguishing between unassessed, partial, mastered, and misconceptions.
        """
        if structured_response.action != TutorAction.CHAT:
            state.questions_attempted = (state.questions_attempted or 0) + 1
        state.correct_answers = state.correct_answers or 0
        state.partial_answers = state.partial_answers or 0
        state.incorrect_answers = state.incorrect_answers or 0
        state.hints_used = state.hints_used or 0
        state.difficulty_level = state.difficulty_level or "beginner"
        state.concepts_understood = state.concepts_understood or []
        state.concepts_partially_understood = state.concepts_partially_understood or []
        state.concepts_not_assessed = state.concepts_not_assessed or []
        state.concepts_needing_review = state.concepts_needing_review or []
        state.recent_misconceptions = state.recent_misconceptions or []

        # Track question asked
        if structured_response.action != TutorAction.CHAT and structured_response.question and structured_response.question.strip():
            state.last_question_asked = structured_response.question.strip()
            state.pending_question = structured_response.question.strip()
        else:
            state.pending_question = None

        # 1. Update concepts demonstrated
        new_mastered = structured_response.concepts_demonstrated or []
        current_understood = set(state.concepts_understood)
        current_partial = set(state.concepts_partially_understood)
        current_not_assessed = set(state.concepts_not_assessed)

        for c in new_mastered:
            # Rule: require multiple demonstrations or explicit progression before full mastery
            if c in current_partial or c in current_understood:
                current_understood.add(c)
                current_partial.discard(c)
            else:
                # First time demonstrating: mark as partially understood
                current_partial.add(c)
            current_not_assessed.discard(c)

        # 2. Update concepts needing review
        new_review = structured_response.concepts_needing_review or []
        current_review = set(state.concepts_needing_review)
        for r in new_review:
            if r in current_understood:
                current_understood.discard(r)
                current_partial.add(r)
            current_review.add(r)
            current_not_assessed.discard(r)

        state.concepts_understood = list(current_understood)
        state.concepts_partially_understood = list(current_partial)
        state.concepts_not_assessed = list(current_not_assessed)
        state.concepts_needing_review = list(current_review)

        # 3. Track misconceptions
        if structured_response.misconception:
            misconceptions = state.recent_misconceptions
            misconceptions.append(structured_response.misconception)
            state.recent_misconceptions = misconceptions[-5:]
            state.incorrect_answers += 1
            state.lesson_stage = "guided_inquiry"
        elif structured_response.hint:
            state.hints_used += 1
            state.partial_answers += 1
        else:
            if new_mastered:
                state.correct_answers += 1

        # 4. Advance lesson stage appropriately
        mode_val = structured_response.mode.value if hasattr(structured_response.mode, "value") else str(structured_response.mode)
        if mode_val == "guided_practice":
            state.lesson_stage = "guided_practice"
        elif mode_val == "independent_practice":
            state.lesson_stage = "independent_practice"
        elif mode_val == "explanation":
            state.lesson_stage = "explanation"
        elif mode_val == "revision":
            state.lesson_stage = "review"
        elif state.concepts_understood and len(state.concepts_understood) >= 2:
            state.lesson_stage = "guided_practice"
        elif state.concepts_partially_understood:
            state.lesson_stage = "guided_inquiry"

        # 5. Adaptive difficulty adjustment
        LearnerModelManager.adjust_difficulty(state)
        state.last_reviewed = datetime.utcnow()
        return state

    @staticmethod
    def adjust_difficulty(state: LearnerStateModel) -> None:
        """Adapts difficulty based on verified correct answers, misconceptions, and accuracy."""
        total = state.questions_attempted or 0
        if total < 2:
            return

        correct = state.correct_answers or 0
        incorrect = state.incorrect_answers or 0
        mastered_count = len(state.concepts_understood or [])
        accuracy = (correct / total) if total > 0 else 0.0

        current = (state.difficulty_level or "beginner").lower()

        # Promotion logic
        if current == "beginner":
            if correct >= 3 and incorrect <= 1 and mastered_count >= 2:
                state.difficulty_level = "intermediate"
        elif current == "intermediate":
            if correct >= 6 and mastered_count >= 4 and accuracy >= 0.70:
                state.difficulty_level = "advanced"

        # Demotion logic
        if current == "advanced" and incorrect >= 3:
            state.difficulty_level = "intermediate"
        elif current == "intermediate" and (incorrect >= 4 or (incorrect >= 3 and accuracy <= 0.50)):
            state.difficulty_level = "beginner"

    @staticmethod
    def calculate_metrics(state: LearnerStateModel) -> Dict[str, float]:
        """Calculates accuracy percentage and composite mastery score (0-100%)."""
        total = state.questions_attempted or 0
        accuracy = (state.correct_answers / total * 100.0) if total > 0 else 0.0
        mastery = min(100.0, (len(state.concepts_understood or []) * 15.0) + (accuracy * 0.5))
        return {
            "accuracy_percentage": round(accuracy, 1),
            "accuracy_percent": round(accuracy, 1),
            "mastery_score": round(mastery, 1)
        }
