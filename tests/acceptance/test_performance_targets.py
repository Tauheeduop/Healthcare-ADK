from __future__ import annotations

from time import perf_counter

import pytest

from healthcare_intake.services.session_repository import get_or_create_session
from healthcare_intake.services.session_service import create_session_service


@pytest.mark.asyncio
async def test_local_session_state_retrieval_target_under_100ms(tmp_path):
    service = create_session_service(tmp_path / "performance.db")
    await get_or_create_session(service, app_name="performance", session_id="perf-session")
    started = perf_counter()
    for _ in range(20):
        session = await service.get_session(
            app_name="performance",
            user_id="patient:perf-session",
            session_id="perf-session",
        )
        assert session is not None
    average = (perf_counter() - started) / 20
    assert average < 0.1, f"average session retrieval was {average:.4f}s"
