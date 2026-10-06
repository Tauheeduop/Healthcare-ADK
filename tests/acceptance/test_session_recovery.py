from __future__ import annotations

import pytest

from healthcare_intake.services.session_repository import get_or_create_session
from healthcare_intake.services.session_service import create_session_service


@pytest.mark.asyncio
async def test_same_session_id_resumes_existing_intake(tmp_path):
    service = create_session_service(tmp_path / "intake.db")
    first = await get_or_create_session(
        service, app_name="acceptance", session_id="resume-123"
    )
    assert first.id == "resume-123"
    resumed = await get_or_create_session(
        service, app_name="acceptance", session_id="resume-123"
    )
    assert resumed.id == first.id
    assert resumed.state["intake_status"] == "in_progress"
