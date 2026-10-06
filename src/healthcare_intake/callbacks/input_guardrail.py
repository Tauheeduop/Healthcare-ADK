"""ADK before-model callback enforcing the non-generative scope gate."""

from __future__ import annotations

from google.adk.agents.context import Context
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types

from healthcare_intake.agents.guardrail_agent import REFUSAL, Scope, classify_healthcare_scope
from healthcare_intake.services.context_manager import manage_request_context
from healthcare_intake.services.input_validation import validate_user_text
from healthcare_intake.config import settings
from healthcare_intake.tools.rag_tools import NO_VERIFIED_INFORMATION


def _latest_user_text(request: LlmRequest) -> str:
    for content in reversed(request.contents or []):
        if content.role != "user":
            continue
        return " ".join(
            part.text for part in (content.parts or []) if part.text
        ).strip()
    return ""


def before_model_callback(
    callback_context: Context, llm_request: LlmRequest
) -> LlmResponse | None:
    text = _latest_user_text(llm_request)
    validation_error = callback_context.state.get("input_validation_error")
    if not validation_error:
        validation_error = validate_user_text(text)
    if validation_error:
        return LlmResponse(
            content=types.Content(
                role="model", parts=[types.Part(text=str(validation_error))]
            ),
            turn_complete=True,
        )
    intake_data = callback_context.state.get("intake_data", {})
    pending_topic = callback_context.state.get("intake_pending_topic")
    if not pending_topic and isinstance(intake_data, dict):
        pending_topic = callback_context.state.get("intake_pending_topic")
    preflight_scope = callback_context.state.get("input_scope")
    scope = (
        Scope(preflight_scope)
        if preflight_scope in {item.value for item in Scope}
        else classify_healthcare_scope(text, pending_topic=pending_topic)
    )
    if scope is Scope.HEALTHCARE:
        manage_request_context(
            llm_request,
            callback_context.state,
            last_n_turns=settings.recent_turns,
            token_threshold=settings.summary_token_threshold,
        )
        return None
    return LlmResponse(
        content=types.Content(role="model", parts=[types.Part(text=REFUSAL)]),
        turn_complete=True,
    )


def rag_before_model_callback(
    callback_context: Context, llm_request: LlmRequest
) -> LlmResponse | None:
    """Apply the scope gate, then fail closed before model use if no verified corpus exists."""
    response = before_model_callback(callback_context, llm_request)
    if response is not None:
        return response
    if not settings.rag_corpus:
        return LlmResponse(
            content=types.Content(
                role="model", parts=[types.Part(text=NO_VERIFIED_INFORMATION)]
            ),
            turn_complete=True,
        )
    return None
