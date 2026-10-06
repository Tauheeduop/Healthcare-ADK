from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

from healthcare_intake.config import settings


def test_streamlit_app_renders_chat_and_session_sidebar(tmp_path):
    previous_path = settings.sqlite_path
    object.__setattr__(settings, "sqlite_path", tmp_path / "ui.db")
    try:
        app_path = Path(__file__).resolve().parents[2] / "src" / "healthcare_intake" / "app.py"
        app = AppTest.from_file(str(app_path)).run(timeout=15)
        assert not app.exception
        assert [item.value for item in app.title] == ["Patient Intake Assistant"]
        assert app.chat_input
    finally:
        object.__setattr__(settings, "sqlite_path", previous_path)
