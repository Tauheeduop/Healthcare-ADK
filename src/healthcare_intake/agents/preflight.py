"""Non-generative checks run concurrently before the RootAgent can call a model."""

from __future__ import annotations

from typing import AsyncGenerator

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events.event import Event
from google.adk.events.event_actions import EventActions

from healthcare_intake.agents.guardrail_agent import classify_healthcare_scope
from healthcare_intake.services.input_validation import validate_user_text


def _message(ctx: InvocationContext) -> str:
    parts = getattr(ctx.user_content, "parts", None) or []
    return " ".join(part.text for part in parts if getattr(part, "text", None)).strip()


class ScopeGuardrailAgent(BaseAgent):
    """Classify the new user turn without invoking a language model."""

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        state = ctx.session.state if ctx.session else {}
        pending = state.get("intake_pending_topic")
        scope = classify_healthcare_scope(_message(ctx), pending_topic=pending)
        yield Event(
            invocation_id=ctx.invocation_id,
            author=self.name,
            actions=EventActions(state_delta={"input_scope": scope.value}),
        )


class InputValidationAgent(BaseAgent):
    """Validate message size/shape concurrently with scope classification."""

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        error = validate_user_text(_message(ctx))
        yield Event(
            invocation_id=ctx.invocation_id,
            author=self.name,
            actions=EventActions(state_delta={"input_validation_error": error}),
        )
