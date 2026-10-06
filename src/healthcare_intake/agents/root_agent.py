"""Root intent router with concurrent deterministic preflight and a hard model gate."""

from __future__ import annotations

from google.adk.agents import LlmAgent, ParallelAgent, SequentialAgent

from healthcare_intake.agents.intake_agent import create_intake_workflow
from healthcare_intake.agents.preflight import InputValidationAgent, ScopeGuardrailAgent
from healthcare_intake.agents.rag_agent import create_rag_workflow
from healthcare_intake.callbacks.input_guardrail import before_model_callback
from healthcare_intake.callbacks.output_safety import validate_patient_output
from healthcare_intake.config import settings


def create_root_agent() -> SequentialAgent:
    preflight = ParallelAgent(
        name="DeterministicPreflight",
        description="Classify scope and validate message before any language model call.",
        sub_agents=[
            ScopeGuardrailAgent(
                name="GuardrailAgent",
                description="Deterministically classify healthcare intake scope.",
            ),
            InputValidationAgent(
                name="InputValidationAgent",
                description="Validate message size and shape without model calls.",
            ),
        ],
    )
    router = LlmAgent(
        name="RootAgent",
        model=settings.model,
        description="Route a healthcare intake turn to intake collection or verified Q&A.",
        instruction=(
            "Route patient intake answers and intake progress to IntakeWorkflow. Route "
            "standalone healthcare knowledge questions to RAGWorkflow. Do not answer medical "
            "knowledge questions yourself. Preserve session continuity and use one workflow "
            "per user turn."
        ),
        sub_agents=[create_intake_workflow(), create_rag_workflow()],
        before_model_callback=before_model_callback,
        after_model_callback=validate_patient_output,
    )
    return SequentialAgent(
        name="HealthcareIntakePipeline",
        description="Run deterministic preflight before RootAgent intent routing.",
        sub_agents=[preflight, router],
    )


root_agent = create_root_agent()
