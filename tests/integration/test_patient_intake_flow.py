from __future__ import annotations

from types import SimpleNamespace

import pytest

from healthcare_intake.callbacks.input_guardrail import before_model_callback
from healthcare_intake.models.intake import FIELD_ORDER
from healthcare_intake.services.session_repository import get_or_create_session
from healthcare_intake.services.session_service import create_session_service
from healthcare_intake.tools.intake_tools import get_next_intake_question, save_patient_info
from healthcare_intake.tools.intake_tools import confirm_intake
from healthcare_intake.tools.rag_tools import NO_VERIFIED_INFORMATION, answer_for_retrieval_result
from google.adk.models.llm_request import LlmRequest
from google.genai import types


@pytest.mark.asyncio
async def test_intake_capture_persists_state_and_blocks_off_topic(tmp_path):
    service = create_session_service(tmp_path / "flow.db")
    session = await get_or_create_session(service, app_name="flow", session_id="flow-123")
    tool_context = SimpleNamespace(state=dict(session.state), invocation_id="test-invocation")
    for field in FIELD_ORDER:
        prompt = get_next_intake_question(tool_context)
        assert prompt and prompt["field"] == field.value
        save_patient_info(field.value, "Patient-provided answer", tool_context)
    event = __import__("google.adk.events", fromlist=["Event"]).Event(
        invocation_id="flow-event",
        author="intake-test",
        actions=__import__("google.adk.events.event_actions", fromlist=["EventActions"]).EventActions(
            state_delta={"intake_data": tool_context.state["intake_data"]}
        ),
    )
    await service.append_event(session, event)
    restored = await service.get_session(
        app_name="flow", user_id="patient:flow-123", session_id="flow-123"
    )
    assert set(restored.state["intake_data"]) == {field.value for field in FIELD_ORDER}
    for field in FIELD_ORDER:
        save_patient_info(field.value, "Updated patient answer", tool_context)
    assert confirm_intake(True, tool_context) == {"confirmed": True}
    assert answer_for_retrieval_result([]) == NO_VERIFIED_INFORMATION

    callback_context = SimpleNamespace(state={})
    request = LlmRequest(
        model="mock",
        contents=[types.Content(role="user", parts=[types.Part(text="What is the weather?")])],
    )
    refusal = before_model_callback(callback_context, request)
    assert refusal.content.parts[0].text == (
        "I am a healthcare intake assistant. I can only help with patient intake questions."
    )
