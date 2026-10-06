"""Intake conversation agent and its ordered workflow."""

from __future__ import annotations

from google.adk.agents import LlmAgent, SequentialAgent

from healthcare_intake.callbacks.input_guardrail import before_model_callback
from healthcare_intake.callbacks.output_safety import validate_patient_output
from healthcare_intake.config import settings
from healthcare_intake.tools.intake_tools import (
    check_if_answered,
    confirm_intake,
    get_intake_summary,
    get_next_intake_question,
    get_patient_info,
    save_patient_info,
)


def create_intake_workflow() -> SequentialAgent:
    agent = LlmAgent(
        name="IntakeAgent",
        model=settings.model,
        description="Collect and confirm one patient's intake answers.",
        instruction=(
            "You are a patient intake assistant. Collect symptoms, allergies, medications, "
            "and medical history. Use the current session tools as the source of truth. "
            "At the start of each turn, check the current pending topic and saved answers. "
            "When the patient answers, save that answer before choosing the next topic. "
            "Never ask again for an answered allergy or medication field. Ask at most one "
            "question per response. Once all fields are collected, present the saved summary "
            "and ask the patient to confirm or correct it. Mark it confirmed only after an "
            "explicit confirmation. Do not diagnose or prescribe."
        ),
        tools=[
            save_patient_info,
            get_patient_info,
            check_if_answered,
            get_next_intake_question,
            get_intake_summary,
            confirm_intake,
        ],
        before_model_callback=before_model_callback,
        after_model_callback=validate_patient_output,
    )
    return SequentialAgent(
        name="IntakeWorkflow",
        description="Run the ordered intake conversation workflow.",
        sub_agents=[agent],
    )
