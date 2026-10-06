from __future__ import annotations

from types import SimpleNamespace

from google.adk.models.llm_request import LlmRequest
from google.genai import types

from healthcare_intake.services.context_manager import manage_request_context


def test_context_manager_summarizes_old_turns_and_keeps_recent_window():
    request = LlmRequest(
        model="mock",
        contents=[
            types.Content(role=role, parts=[types.Part(text=text)])
            for role, text in (
                ("user", "old symptoms " * 30),
                ("model", "old follow-up " * 30),
                ("user", "current allergies question"),
                ("model", "current answer"),
            )
        ],
    )
    state = {}
    manage_request_context(request, state, last_n_turns=1, token_threshold=10)
    assert "old symptoms" in state["conversation_summary"]
    assert len(request.contents) == 3  # summary plus the most recent user/model turn
    assert "current allergies question" in request.contents[-2].parts[0].text
