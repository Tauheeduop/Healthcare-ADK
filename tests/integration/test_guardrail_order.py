from __future__ import annotations

from typing import AsyncGenerator

import pytest
from google.adk.agents import LlmAgent
from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from healthcare_intake.callbacks.input_guardrail import before_model_callback


class CountingModel(BaseLlm):
    model: str = "counting-test-model"
    calls: int = 0

    async def generate_content_async(
        self, llm_request: LlmRequest, stream: bool = False
    ) -> AsyncGenerator[LlmResponse, None]:
        self.calls += 1
        yield LlmResponse(
            content=types.Content(role="model", parts=[types.Part(text="safe test response")]),
            turn_complete=True,
        )


async def run_turn(text: str):
    model = CountingModel()
    agent = LlmAgent(
        name="GuardedTestAgent",
        model=model,
        instruction="Respond briefly.",
        before_model_callback=before_model_callback,
    )
    service = InMemorySessionService()
    runner = Runner(app_name="guardrail-test", agent=agent, session_service=service)
    session = await service.create_session(app_name="guardrail-test", user_id="user-1")
    events = [
        event
        async for event in runner.run_async(
            user_id="user-1",
            session_id=session.id,
            new_message=types.Content(role="user", parts=[types.Part(text=text)]),
        )
    ]
    return model.calls, events


@pytest.mark.asyncio
async def test_off_topic_is_refused_without_invoking_model():
    calls, events = await run_turn("What is the weather?")
    assert calls == 0
    assert any(
        event.content
        and any(part.text == "I am a healthcare intake assistant. I can only help with patient intake questions." for part in (event.content.parts or []))
        for event in events
    )


@pytest.mark.asyncio
async def test_healthcare_input_reaches_model():
    calls, _ = await run_turn("I have a headache")
    assert calls == 1
