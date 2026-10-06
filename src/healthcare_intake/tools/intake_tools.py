"""Session-scoped tools for collecting and reviewing intake answers."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from google.adk.tools import ToolContext

from healthcare_intake.models.intake import (
    FIELD_ORDER,
    FIELD_QUESTIONS,
    normalize_field,
    validate_answer,
)


def _answers(tool_context: ToolContext) -> dict[str, Any]:
    current = tool_context.state.get("intake_data", {})
    return dict(current) if isinstance(current, dict) else {}


def save_patient_info(field: str, value: str, tool_context: ToolContext) -> dict[str, Any]:
    """Save or correct one patient-provided intake answer in this session."""
    topic = normalize_field(field)
    answer = validate_answer(value)
    answers = _answers(tool_context)
    prior = answers.get(topic.value, {})
    answers[topic.value] = {
        "value": answer,
        "status": "corrected" if prior else "answered",
        "updated_at": datetime.now(UTC).isoformat(),
        "source_event_id": getattr(tool_context, "invocation_id", None),
    }
    tool_context.state["intake_data"] = answers
    tool_context.state["intake_pending_topic"] = None
    tool_context.state["intake_status"] = "in_progress"
    return {"saved": True, "field": topic.value}


def get_patient_info(field: str, tool_context: ToolContext) -> dict[str, Any] | None:
    """Return one answer from the current session, if present."""
    topic = normalize_field(field)
    item = _answers(tool_context).get(topic.value)
    return item if isinstance(item, dict) else None


def check_if_answered(field: str, tool_context: ToolContext) -> bool:
    """Check whether a topic has an answer before asking the patient again."""
    item = get_patient_info(field, tool_context)
    return bool(item and item.get("status") in {"answered", "corrected"})


def get_next_intake_question(tool_context: ToolContext) -> dict[str, str] | None:
    """Select and persist the next unanswered topic in the defined intake order."""
    for field in FIELD_ORDER:
        if not check_if_answered(field.value, tool_context):
            tool_context.state["intake_pending_topic"] = field.value
            return {"field": field.value, "question": FIELD_QUESTIONS[field]}
    tool_context.state["intake_pending_topic"] = None
    tool_context.state["intake_status"] = "awaiting_confirmation"
    return None


def get_intake_summary(tool_context: ToolContext) -> dict[str, Any]:
    """Return collected fields for the patient review step."""
    answers = _answers(tool_context)
    return {
        "answers": answers,
        "missing_fields": [
            field.value for field in FIELD_ORDER if field.value not in answers
        ],
        "status": tool_context.state.get("intake_status", "in_progress"),
    }


def confirm_intake(confirmed: bool, tool_context: ToolContext) -> dict[str, Any]:
    """Record explicit patient confirmation after reviewing the collected answers."""
    if not confirmed:
        tool_context.state["intake_status"] = "in_progress"
        return {"confirmed": False, "message": "Please tell me what you would like to correct."}
    if get_next_intake_question(tool_context) is not None:
        return {"confirmed": False, "message": "The intake still has unanswered topics."}
    tool_context.state["intake_status"] = "confirmed"
    return {"confirmed": True}
