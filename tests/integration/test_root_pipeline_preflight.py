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

from healthcare_intake.agents.root_agent import create_root_agent


class CountingModel(BaseLlm):
    model: str = "counting-root-test"
    calls: int = 0

    async def generate_content_async(
        self, llm_request: LlmRequest, stream: bool = False
    ) -> AsyncGenerator[LlmResponse, None]:
        self.calls += 1
        yield LlmResponse(
            content=types.Content(role="model", parts=[types.Part(text="unexpected")]),
            turn_complete=True,
        )


def _replace_models(agent, model: CountingModel) -> None:
    if isinstance(agent, LlmAgent):
        agent.model = model
    for child in agent.sub_agents:
        _replace_models(child, model)


@pytest.mark.asyncio
async def test_parallel_preflight_refuses_off_topic_before_any_model_call():
    model = CountingModel()
    root = create_root_agent()
    _replace_models(root, model)
    service = InMemorySessionService()
    runner = Runner(app_name="root-preflight-test", agent=root, session_service=service)
    session = await service.create_session(
        app_name="root-preflight-test", user_id="patient:test"
    )
    events = [
        event
        async for event in runner.run_async(
            user_id="patient:test",
            session_id=session.id,
            new_message=types.Content(
                role="user", parts=[types.Part(text="What is the weather?")]
            ),
        )
    ]
    assert model.calls == 0
    assert any(
        event.content
        and any(
            part.text
            == "I am a healthcare intake assistant. I can only help with patient intake questions."
            for part in (event.content.parts or [])
        )
        for event in events
    )
