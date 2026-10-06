"""Grounded medical Q&A agent and workflow."""

from __future__ import annotations

from google.adk.agents import LlmAgent, SequentialAgent

from healthcare_intake.callbacks.input_guardrail import rag_before_model_callback
from healthcare_intake.callbacks.output_safety import validate_rag_output
from healthcare_intake.config import settings
from healthcare_intake.tools.rag_tools import (
    NO_VERIFIED_INFORMATION,
    create_rag_retrieval_tool,
)


def create_rag_workflow() -> SequentialAgent:
    rag_tool = create_rag_retrieval_tool(settings.rag_corpus)
    tools = [rag_tool] if rag_tool is not None else []
    agent = LlmAgent(
        name="RAGAgent",
        model=settings.model,
        description="Answer healthcare knowledge questions from verified retrieved sources.",
        instruction=(
            "Answer only from verified healthcare retrieval results. Always use the retrieval "
            "tool before answering. Keep claims within the retrieved evidence and include the "
            "returned source title or citation when available. If retrieval returns no matching "
            f"result, or the corpus is unavailable, respond exactly: {NO_VERIFIED_INFORMATION}. "
            "Do not diagnose, prescribe, or invent citations."
        ),
        tools=tools,
        before_model_callback=rag_before_model_callback,
        after_model_callback=validate_rag_output,
    )
    return SequentialAgent(
        name="RAGWorkflow",
        description="Retrieve evidence and generate a grounded answer in sequence.",
        sub_agents=[agent],
    )
