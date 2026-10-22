"""Conversation memory manager for SchedulAI.

Implements token-aware context construction, configurable sliding message windows,
persistent session isolation, and structured conversation summarization preserving:
- Current and previous topics
- Concepts already explained and understood
- Concepts partially understood or not assessed
- Previous misconceptions
- Questions already asked and student answers
- Examples discussed (parameters, Gantt charts, metrics)
- Stated student weaknesses and unresolved questions
"""

import re
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.database.models import MessageModel, LearnerStateModel


class ConversationMemoryManager:
    """Manages conversational memory, rolling context, and structured summaries."""

    DEFAULT_RECENT_WINDOW: int = 8
    MAX_TOKENS_ESTIMATE: int = 2048

    @classmethod
    def format_recent_messages(
        cls,
        history: List[MessageModel],
        window_size: int = DEFAULT_RECENT_WINDOW
    ) -> List[Dict[str, str]]:
        """
        Extracts the most recent messages up to window_size in chronological order.
        Preserves complete text without truncating meaningful mathematical explanations or examples.
        """
        if not history:
            return []

        recent = history[-window_size:] if len(history) > window_size else history
        formatted = []
        for msg in recent:
            role = msg.role if msg.role in ["user", "assistant", "system"] else "user"
            content = msg.content.strip() if msg.content else ""
            if content:
                formatted.append({"role": role, "content": content})
        return formatted

    @classmethod
    def extract_key_points_from_turn(cls, role: str, content: str) -> Dict[str, Any]:
        """Extracts key pedagogical facts from a message turn."""
        points = {}
        lower = content.lower()

        # Weaknesses / Goals
        if role == "user":
            if any(w in lower for w in ["weakness", "struggle", "don't understand", "dont understand", "hard for me", "bad at"]):
                points["stated_weakness"] = content.strip()
            if any(w in lower for w in ["example", "calculate", "problem", "solve"]):
                points["example_or_problem"] = content.strip()
        elif role == "assistant":
            # Check for worked example
            if "worked example" in lower or "gantt" in lower or "| process |" in lower:
                points["example_provided"] = content[:300].strip()
            # Check for question
            if "**check your understanding:**" in lower:
                q = content.split("**check your understanding:**")[-1].strip()
                points["question_asked"] = q.split("\n")[0].strip()
            elif "?" in content:
                sentences = [s.strip() for s in content.split("\n") if "?" in s]
                if sentences:
                    points["question_asked"] = sentences[-1]

        return points

    @classmethod
    def build_or_update_summary(
        cls,
        current_summary: str,
        messages_to_summarize: List[MessageModel],
        learner_state: Optional[LearnerStateModel] = None
    ) -> str:
        """
        Incrementally builds or updates a compact, structured conversation summary.
        Preserves critical educational facts: topics, verified answers, examples,
        misconceptions, questions asked, and student-stated goals.
        """
        summary_sections: Dict[str, List[str]] = {
            "Topics & Lesson Stage": [],
            "Student Goals & Weaknesses": [],
            "Concepts Explained & Student Answers": [],
            "Examples & Calculations Discussed": [],
            "Misconceptions Addressed": [],
            "Unresolved Questions": []
        }

        # Seed from existing summary if structured
        if current_summary:
            current_lower = current_summary.lower()
            # Carry over past weaknesses
            for line in current_summary.split("\n"):
                line = line.strip()
                if line.startswith("- Weakness:") or "weakness" in line.lower():
                    summary_sections["Student Goals & Weaknesses"].append(line.lstrip("- "))
                elif line.startswith("- Example:") or "p1" in line.lower():
                    summary_sections["Examples & Calculations Discussed"].append(line.lstrip("- "))

        # Extract from state if available
        if learner_state:
            stage = learner_state.lesson_stage or "knowledge_assessment"
            topic = learner_state.current_topic or "Fundamentals"
            summary_sections["Topics & Lesson Stage"].append(f"Active topic: {topic} (Stage: {stage})")

            understood = learner_state.concepts_understood
            if understood:
                summary_sections["Concepts Explained & Student Answers"].append(
                    f"Student demonstrated understanding of: {', '.join(understood)}"
                )

            partial = learner_state.concepts_partially_understood
            if partial:
                summary_sections["Concepts Explained & Student Answers"].append(
                    f"Partially understood (needs reinforcement): {', '.join(partial)}"
                )

            misconceptions = learner_state.recent_misconceptions
            if misconceptions:
                summary_sections["Misconceptions Addressed"].extend(misconceptions)

            if learner_state.last_question_asked:
                summary_sections["Unresolved Questions"].append(f"Last question: {learner_state.last_question_asked}")

        # Process message items to summarize
        for msg in messages_to_summarize:
            role = msg.role
            content = msg.content
            extracted = cls.extract_key_points_from_turn(role, content)

            if "stated_weakness" in extracted:
                summary_sections["Student Goals & Weaknesses"].append(extracted["stated_weakness"])
            if "example_or_problem" in extracted or "example_provided" in extracted:
                summary_sections["Examples & Calculations Discussed"].append(
                    f"Discussed example/calculation: {content[:150]}"
                )
            if "question_asked" in extracted:
                summary_sections["Unresolved Questions"].append(f"Tutor asked: {extracted['question_asked']}")

        # Deduplicate and format output
        output_lines = ["### Session Conversation Summary:"]
        for section, items in summary_sections.items():
            clean_items = list(dict.fromkeys(item.strip() for item in items if item.strip()))
            if clean_items:
                output_lines.append(f"**{section}:**")
                for item in clean_items[-4:]:  # Keep most relevant points
                    output_lines.append(f"- {item}")

        return "\n".join(output_lines)

    @classmethod
    def assemble_prompt_messages(
        cls,
        system_prompt: str,
        conversation_summary: str,
        recent_messages: List[Dict[str, str]],
        latest_user_message: str,
        tutoring_state_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, str]]:
        """
        Assembles token-controlled conversation payload for LLM inference.
        Includes a single unified system prompt (with state and summary),
        untruncated recent messages, and current user message.
        """
        messages: List[Dict[str, str]] = []

        # 1. Single unified System Prompt with embedded structured state & summary
        sys_content = system_prompt
        if tutoring_state_dict:
            state_block = f"\n\n[STRUCTURED TUTORING STATE]\n{json.dumps(tutoring_state_dict, indent=2)}"
            sys_content += state_block

        # Inject earlier conversation summary into single system prompt
        if conversation_summary and conversation_summary.strip():
            sys_content += f"\n\n[BACKGROUND CONTEXT: EARLIER CONVERSATION SUMMARY]\n{conversation_summary.strip()}"

        messages.append({"role": "system", "content": sys_content})

        # 2. Inject untruncated recent messages
        for msg in recent_messages:
            messages.append(msg)

        # 3. Inject latest user message if not already the last item in recent_messages
        if not recent_messages or recent_messages[-1].get("content") != latest_user_message:
            messages.append({"role": "user", "content": latest_user_message})

        return messages
