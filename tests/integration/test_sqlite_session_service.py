from __future__ import annotations

from datetime import UTC, datetime

import pytest
from google.adk.events import Event
from google.adk.events.event_actions import EventActions
from google.adk.sessions.base_session_service import GetSessionConfig
from google.genai import types

from healthcare_intake.services.session_repository import get_or_create_session
from healthcare_intake.services.session_service import (
    close_session_service,
    create_session_service,
)


@pytest.mark.asyncio
async def test_sqlite_session_and_events_survive_service_restart(tmp_path):
    db_path = tmp_path / "sessions.db"
    service = create_session_service(db_path)
    session = await get_or_create_session(
        service, app_name="intake-test", session_id="session-123"
    )
    event = Event(
        invocation_id="invocation-1",
        author="user",
        timestamp=datetime.now(UTC).timestamp(),
        content=types.Content(role="user", parts=[types.Part(text="intake started")]),
        actions=EventActions(
            state_delta={"intake_data": {"allergies": {"value": "None", "status": "answered"}}}
        ),
    )
    await service.append_event(session, event)
    await close_session_service(service)

    reopened = create_session_service(db_path)
    restored = await reopened.get_session(
        app_name="intake-test",
        user_id="patient:session-123",
        session_id="session-123",
        config=GetSessionConfig(num_recent_events=10),
    )
    assert restored is not None
    assert restored.state["intake_data"]["allergies"]["value"] == "None"
    assert restored.events[-1].timestamp > 0


@pytest.mark.asyncio
async def test_session_lookup_is_scoped_by_user_and_session(tmp_path):
    service = create_session_service(tmp_path / "sessions.db")
    await service.create_session(
        app_name="intake-test", user_id="patient-a", session_id="same-id"
    )
    assert await service.get_session(
        app_name="intake-test", user_id="patient-b", session_id="same-id"
    ) is None
