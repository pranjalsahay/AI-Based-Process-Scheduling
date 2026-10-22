"""Parses, sanitizes, and validates structured LLM JSON responses."""

import re
import json
import logging
from typing import Dict, Any, Optional, Tuple

from pydantic import ValidationError
from app.schemas.chat import TutorStructuredResponse, TutoringMode, TutorAction

logger = logging.getLogger(__name__)


def extract_json_substring(raw_text: str) -> Optional[str]:
    """Finds the outermost matching JSON object in a string."""
    if not raw_text:
        return None

    # Strip code block fences if present
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    start_idx = cleaned.find("{")
    end_idx = cleaned.rfind("}")

    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        return cleaned[start_idx:end_idx + 1]

    return None


def repair_common_json_flaws(json_str: str) -> str:
    """Repairs common LLM formatting flaws like trailing commas before closing braces."""
    # Remove trailing commas in lists and objects: , ] -> ] and , } -> }
    repaired = re.sub(r",\s*([\]}])", r"\1", json_str)
    return repaired


def parse_and_validate_response(
    raw_text: str,
    default_mode: TutoringMode = TutoringMode.SOCRATIC,
    default_topic: str = "Fundamentals"
) -> Tuple[Optional[TutorStructuredResponse], bool]:
    """
    Parses raw LLM text into a validated TutorStructuredResponse.
    
    Returns:
        (TutorStructuredResponse, is_fallback: bool)
    """
    json_candidate = extract_json_substring(raw_text)

    if json_candidate:
        try:
            # First attempt standard parse
            data = json.loads(json_candidate)

            # Normalization: If the model put the educational content/table in 'question'
            # or if 'message' is an incomplete sentence or preamble:
            q_val = (data.get("question") or "").strip()
            m_val = (data.get("message") or "").strip()
            if q_val and ("|" in q_val or "\n" in q_val or len(m_val) < 80):
                if q_val.lower() not in m_val.lower():
                    data["message"] = f"{m_val}\n\n{q_val}".strip()

            # Ensure any follow-up question is included at the end of message if not already present
            if data.get("question") and data["question"].strip():
                q_text = data["question"].strip()
                if q_text.lower() not in data.get("message", "").lower():
                    # Weave question in naturally without a formal "**Question:**" heading
                    data["message"] = f"{data.get('message', '')}\n\n{q_text}".strip()

            validated = TutorStructuredResponse.model_validate(data)
            return validated, False
        except Exception:
            # Second attempt with trailing-comma repair
            try:
                repaired = repair_common_json_flaws(json_candidate)
                data = json.loads(repaired)

                q_val = (data.get("question") or "").strip()
                m_val = (data.get("message") or "").strip()
                if q_val and ("|" in q_val or "\n" in q_val or len(m_val) < 80):
                    if q_val.lower() not in m_val.lower():
                        data["message"] = f"{m_val}\n\n{q_val}".strip()

                if data.get("question") and data["question"].strip():
                    q_text = data["question"].strip()
                    if q_text.lower() not in data.get("message", "").lower():
                        # Weave question in naturally without a formal "**Question:**" heading
                        data["message"] = f"{data.get('message', '')}\n\n{q_text}".strip()

                validated = TutorStructuredResponse.model_validate(data)
                return validated, False
            except Exception as e:
                logger.warning(f"JSON validation failed on candidate: {e}")

    # Fallback response if JSON extraction or validation failed completely
    fallback_message = raw_text.strip() if raw_text and raw_text.strip() else (
        "Let's review this concept together. Can you describe what rule or metric we should examine first?"
    )

    # Clean out any stray backticks from fallback display
    fallback_message = re.sub(r"^```(?:json)?", "", fallback_message).rstrip("`").strip()

    fallback_obj = TutorStructuredResponse(
        message=fallback_message,
        mode=default_mode,
        topic=default_topic,
        action=TutorAction.ASK_QUESTION if default_mode != TutoringMode.EXPLANATION else TutorAction.EXPLAIN_CONCEPT,
        question=None,
        hint=None,
        misconception=None,
        concepts_demonstrated=[],
        concepts_needing_review=[],
        source_ids=[],
        requires_calculation=False
    )
    return fallback_obj, True
