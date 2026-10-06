from __future__ import annotations

from types import SimpleNamespace

from healthcare_intake.tools.intake_tools import (
    confirm_intake,
    get_next_intake_question,
    save_patient_info,
)


def test_one_question_at_a_time_then_confirm_with_correction():
    tool_context = SimpleNamespace(state={"intake_data": {}, "intake_status": "in_progress"})
    seen = []
    for answer in ("Headache", "None", "None", "No relevant history"):
        question = get_next_intake_question(tool_context)
        assert question is not None
        seen.append(question["field"])
        save_patient_info(question["field"], answer, tool_context)
    assert seen == ["symptoms", "allergies", "medications", "medical_history"]
    assert get_next_intake_question(tool_context) is None
    save_patient_info("allergies", "Peanuts", tool_context)
    assert confirm_intake(True, tool_context) == {"confirmed": True}
