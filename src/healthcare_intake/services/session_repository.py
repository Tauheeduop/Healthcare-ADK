"""Session creation and resume helpers scoped to one local patient capability."""

from __future__ import annotations

from google.adk.sessions.base_session_service import BaseSessionService
from google.adk.sessions.session import Session


async def get_or_create_session(
    service: BaseSessionService,
    *,
    app_name: str,
    session_id: str,
) -> Session:
    """Load an existing session or create it; IDs are unguessable local capabilities."""
    user_id = f"patient:{session_id}"
    session = await service.get_session(
        app_name=app_name, user_id=user_id, session_id=session_id
    )
    if session is not None:
        return session
    return await service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
        state={"intake_data": {}, "intake_status": "in_progress"},
    )
