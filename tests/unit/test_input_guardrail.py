from __future__ import annotations

from types import SimpleNamespace

from google.adk.models.llm_request import LlmRequest
from google.genai import types

from healthcare_intake.agents.guardrail_agent import REFUSAL, Scope, classify_healthcare_scope
from healthcare_intake.callbacks.input_guardrail import before_model_callback


def request(text: str) -> LlmRequest:
    return LlmRequest(
        model="mock",
        contents=[types.Content(role="user", parts=[types.Part(text=text)])],
    )


def test_healthcare_input_passes_the_gate():
    context = SimpleNamespace(state={})
    assert before_model_callback(context, request("I have a headache")) is None
    assert classify_healthcare_scope("I have a headache") is Scope.HEALTHCARE


def test_off_topic_input_returns_exact_refusal_before_model_call():
    context = SimpleNamespace(state={})
    response = before_model_callback(context, request("What is the weather?"))
    assert response is not None
    assert response.content.parts[0].text == REFUSAL
    assert classify_healthcare_scope("What is the weather?") is Scope.OFF_TOPIC


def test_short_answer_is_allowed_only_when_intake_topic_is_pending():
    assert classify_healthcare_scope("None", pending_topic="allergies") is Scope.HEALTHCARE
    assert classify_healthcare_scope("None") is Scope.OFF_TOPIC
    assert classify_healthcare_scope("Can you help with taxes?", pending_topic="allergies") is Scope.OFF_TOPIC
