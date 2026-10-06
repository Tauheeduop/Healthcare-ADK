"""Patient intake fields and validation."""

from __future__ import annotations

from enum import StrEnum


class IntakeField(StrEnum):
    SYMPTOMS = "symptoms"
    ALLERGIES = "allergies"
    MEDICATIONS = "medications"
    MEDICAL_HISTORY = "medical_history"


FIELD_ORDER = tuple(IntakeField)
FIELD_QUESTIONS = {
    IntakeField.SYMPTOMS: "What symptoms or concerns would you like the care team to know about?",
    IntakeField.ALLERGIES: "Do you have any allergies? You can say none or list them.",
    IntakeField.MEDICATIONS: "What medications do you currently take? You can say none or list them.",
    IntakeField.MEDICAL_HISTORY: "Is there any medical history you would like the care team to know about?",
}
MAX_ANSWER_LENGTH = 4000


def normalize_field(field: str) -> IntakeField:
    try:
        return IntakeField(field.strip().casefold())
    except (ValueError, AttributeError) as exc:
        allowed = ", ".join(item.value for item in IntakeField)
        raise ValueError(f"field must be one of: {allowed}") from exc


def validate_answer(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("patient answer must be text")
    clean = " ".join(value.split())
    if not clean:
        raise ValueError("patient answer cannot be empty")
    if len(clean) > MAX_ANSWER_LENGTH:
        raise ValueError(f"patient answer cannot exceed {MAX_ANSWER_LENGTH} characters")
    return clean
