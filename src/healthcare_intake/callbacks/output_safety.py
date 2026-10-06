"""Output guards for empty, ungrounded, and malformed medical responses."""

from __future__ import annotations

import re

from google.adk.agents.context import Context
from google.adk.models.llm_response import LlmResponse
from google.genai import types

from healthcare_intake.tools.rag_tools import NO_VERIFIED_INFORMATION
from healthcare_intake.services.rag_service import normalize_grounding_sources

_UNSAFE_MEDICAL_ADVICE = re.compile(
    r"\b(you should (take|stop|start|increase|decrease)|take (this|that|\d+)|"
    r"stop taking|increase your dose|decrease your dose|your diagnosis is|"
    r"you have (cancer|diabetes|a heart attack|an infection))\b",
    re.IGNORECASE,
)
_MEDICAL_SAFETY_FALLBACK = (
    "I can't provide a diagnosis or treatment recommendation. Please discuss this with your care team."
)


def _text(response: LlmResponse) -> str:
    content = response.content
    if content is None:
        return ""
    return " ".join(part.text for part in (content.parts or []) if part.text).strip()


def validate_patient_output(_context: Context, response: LlmResponse) -> LlmResponse | None:
    """Reject empty completions; grounding is enforced by the RAG-specific callback."""
    content = response.content
    has_tool_call = bool(
        content
        and any(
            getattr(part, "function_call", None)
            or getattr(part, "code_execution_call", None)
            for part in (content.parts or [])
        )
    )
    response_text = _text(response)
    if has_tool_call or response.turn_complete is False:
        return None
    if _UNSAFE_MEDICAL_ADVICE.search(response_text):
        return LlmResponse(
            content=types.Content(
                role="model", parts=[types.Part(text=_MEDICAL_SAFETY_FALLBACK)]
            ),
            turn_complete=True,
        )
    if response_text:
        return None
    return LlmResponse(
        content=types.Content(
            role="model",
            parts=[types.Part(text="I couldn't safely prepare a response. Please try again.")],
        ),
        turn_complete=True,
    )


def validate_rag_output(_context: Context, response: LlmResponse) -> LlmResponse | None:
    """Require Vertex grounding metadata for final RAG answers."""
    content = response.content
    has_tool_call = bool(
        content
        and any(
            getattr(part, "function_call", None)
            or getattr(part, "code_execution_call", None)
            for part in (content.parts or [])
        )
    )
    if has_tool_call or response.turn_complete is False:
        return None
    metadata = response.grounding_metadata
    chunks = getattr(metadata, "grounding_chunks", None) if metadata else None
    rag_chunks = [
        chunk for chunk in (chunks or []) if getattr(chunk, "retrieved_context", None)
    ]
    if rag_chunks:
        sources = normalize_grounding_sources(metadata)
        if sources:
            _context.state["rag_sources"] = sources
        return None
    return LlmResponse(
        content=types.Content(
            role="model", parts=[types.Part(text=NO_VERIFIED_INFORMATION)]
        ),
        turn_complete=True,
    )
