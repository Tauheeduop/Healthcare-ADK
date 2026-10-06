from google.adk.models.llm_request import LlmRequest
from google.genai import types

from healthcare_intake.services.context_manager import manage_request_context


def test_context_management_preserves_intake_state_and_recent_turns():
    request = LlmRequest(
        model="mock",
        contents=[
            types.Content(role="user", parts=[types.Part(text="old intake information " * 40)]),
            types.Content(role="model", parts=[types.Part(text="old response " * 40)]),
            types.Content(role="user", parts=[types.Part(text="current allergy answer")]),
            types.Content(role="model", parts=[types.Part(text="current response")]),
        ],
    )
    state = {"intake_data": {"allergies": {"value": "peanuts"}}}
    manage_request_context(request, state, last_n_turns=1, token_threshold=10)
    assert "old intake information" in state["conversation_summary"]
    assert state["intake_data"]["allergies"]["value"] == "peanuts"
    assert len(request.contents) == 3
