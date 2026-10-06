"""Arrange-Act-Assert scaffolds for the Patient Intake Assistant spec.

These tests use deterministic local boundaries. A live Vertex AI corpus/model is
not required for the acceptance contracts to be checked.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from google.adk.agents import ParallelAgent, SequentialAgent

from healthcare_intake.agents.intake_agent import create_intake_workflow
from healthcare_intake.agents.preflight import InputValidationAgent, ScopeGuardrailAgent
from healthcare_intake.agents.rag_agent import create_rag_workflow
from healthcare_intake.agents.root_agent import create_root_agent
from healthcare_intake.callbacks.input_guardrail import before_model_callback
from healthcare_intake.tools.intake_tools import (
    get_next_intake_question,
    save_patient_info,
)
from healthcare_intake.tools.rag_tools import (
    NO_VERIFIED_INFORMATION,
    answer_for_retrieval_result,
    create_rag_retrieval_tool,
)


REFUSAL = "I am a healthcare intake assistant. I can only help with patient intake questions."


def test_weather_query_is_refused_before_model_invocation():
    # Arrange
    context = SimpleNamespace(state={})
    # The request callback uses the latest user message from LlmRequest; construct
    # the real request type here so this test covers the production boundary.
    from google.adk.models.llm_request import LlmRequest
    from google.genai import types

    request = LlmRequest(
        model="mock",
        contents=[types.Content(role="user", parts=[types.Part(text="What is the weather?")])],
    )

    # Act
    response = before_model_callback(context, request)

    # Assert
    assert response is not None
    assert response.content.parts[0].text == REFUSAL


@pytest.mark.parametrize(
    ("field", "answer", "following_field"),
    [
        ("allergies", "Penicillin", "medications"),
        ("medications", "Metformin", "medical_history"),
    ],
)
def test_answered_allergy_or_medication_is_not_asked_again(field, answer, following_field):
    # Arrange
    context = SimpleNamespace(
        state={"intake_data": {}, "intake_status": "in_progress"},
        invocation_id="same-session-turn",
    )
    save_patient_info("symptoms", "Headache", context)

    # Act
    save_patient_info(field, answer, context)
    next_question = get_next_intake_question(context)

    # Assert
    assert context.state["intake_data"][field]["value"] == answer
    assert next_question["field"] == following_field
    assert next_question["field"] != field


def test_rag_uses_vertex_retrieval_and_returns_specified_empty_result_response():
    # Arrange
    retrieval_tool = create_rag_retrieval_tool("projects/test/locations/us/corpora/1")
    empty_retrieval_result = []

    # Act
    response = answer_for_retrieval_result(empty_retrieval_result)

    # Assert
    assert retrieval_tool is not None
    assert retrieval_tool.__class__.__name__ == "VertexAiRagRetrieval"
    assert response == "I don't have verified information on that"
    assert response == NO_VERIFIED_INFORMATION


def test_root_pipeline_wires_preflight_before_intake_and_rag_workflows():
    # Arrange
    root = create_root_agent()

    # Act
    preflight = root.sub_agents[0]
    router = root.sub_agents[1]

    # Assert
    assert isinstance(root, SequentialAgent)
    assert isinstance(preflight, ParallelAgent)
    assert {agent.name for agent in preflight.sub_agents} == {
        "GuardrailAgent",
        "InputValidationAgent",
    }
    assert {agent.name for agent in router.sub_agents} == {
        "IntakeWorkflow",
        "RAGWorkflow",
    }
    assert isinstance(create_intake_workflow(), SequentialAgent)
    assert isinstance(create_rag_workflow(), SequentialAgent)
    assert any(isinstance(agent, ScopeGuardrailAgent) for agent in preflight.sub_agents)
    assert any(isinstance(agent, InputValidationAgent) for agent in preflight.sub_agents)
    assert router.sub_agents[0].sub_agents[0].name == "IntakeAgent"
    assert router.sub_agents[1].sub_agents[0].name == "RAGAgent"
