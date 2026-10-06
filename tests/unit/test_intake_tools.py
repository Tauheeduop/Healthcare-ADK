from __future__ import annotations

from types import SimpleNamespace

import pytest

from healthcare_intake.tools.intake_tools import (
    check_if_answered,
    confirm_intake,
    get_intake_summary,
    get_next_intake_question,
    get_patient_info,
    save_patient_info,
)


def context():
    return SimpleNamespace(state={"intake_data": {}, "intake_status": "in_progress"})


def test_intake_questions_are_ordered_and_answered_fields_are_skipped():
    tool_context = context()
    first = get_next_intake_question(tool_context)
    assert first["field"] == "symptoms"
    save_patient_info("symptoms", "Headache", tool_context)
    allergy = get_next_intake_question(tool_context)
    assert allergy["field"] == "allergies"
    save_patient_info("allergies", "None", tool_context)
    assert check_if_answered("allergies", tool_context)
    assert get_patient_info("allergies", tool_context)["value"] == "None"
    assert get_next_intake_question(tool_context)["field"] == "medications"


def test_answers_can_be_corrected_and_summary_requires_all_topics():
    tool_context = context()
    for field in ("symptoms", "allergies", "medications", "medical_history"):
        save_patient_info(field, "None", tool_context)
    save_patient_info("allergies", "Peanuts", tool_context)
    assert get_patient_info("allergies", tool_context)["status"] == "corrected"
    assert get_intake_summary(tool_context)["missing_fields"] == []
    assert confirm_intake(True, tool_context) == {"confirmed": True}
    assert tool_context.state["intake_status"] == "confirmed"


@pytest.mark.parametrize("field", ["", "weight", "dob"])
def test_invalid_intake_fields_are_rejected(field):
    with pytest.raises(ValueError):
        save_patient_info(field, "value", context())


def test_empty_answer_is_rejected():
    with pytest.raises(ValueError):
        save_patient_info("allergies", "  ", context())
