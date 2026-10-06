"""Streamlit patient intake interface."""

from __future__ import annotations

import asyncio
import sys
import uuid
from pathlib import Path

import streamlit as st
from google.adk.runners import Runner
from google.genai import types

_SRC_ROOT = str(Path(__file__).resolve().parents[1])
if _SRC_ROOT not in sys.path:
    sys.path.insert(0, _SRC_ROOT)

from healthcare_intake.agents.root_agent import root_agent
from healthcare_intake.config import settings
from healthcare_intake.services.session_repository import get_or_create_session
from healthcare_intake.services.session_service import create_session_service


@st.cache_resource
def _runtime():
    service = create_session_service(settings.sqlite_path)
    runner = Runner(
        app_name=settings.app_name,
        agent=root_agent,
        session_service=service,
        auto_create_session=False,
    )
    return service, runner


async def _load_session(service, session_id: str):
    return await get_or_create_session(
        service, app_name=settings.app_name, session_id=session_id
    )


async def _run_turn(runner, service, session_id: str, message: str) -> str:
    await _load_session(service, session_id)
    user_id = f"patient:{session_id}"
    answer = "I couldn't safely prepare a response. Please try again."
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=types.Content(role="user", parts=[types.Part(text=message)]),
    ):
        if event.is_final_response() and event.content:
            text = " ".join(
                part.text for part in (event.content.parts or []) if part.text
            ).strip()
            if text:
                answer = text
    return answer


async def _get_state(service, session_id: str):
    return await _load_session(service, session_id)


def main() -> None:
    st.set_page_config(page_title="Patient Intake", page_icon="🩺")
    st.title("Patient Intake Assistant")
    st.caption("Share information for your care team or ask a verified healthcare question.")

    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    session_id = st.sidebar.text_input(
        "Session ID", value=st.session_state.session_id, help="Keep this ID to resume this intake."
    ).strip()
    if session_id:
        st.session_state.session_id = session_id
    else:
        st.warning("Enter a session ID to continue.")
        st.stop()

    service, runner = _runtime()
    try:
        session = asyncio.run(_get_state(service, session_id))
    except Exception:
        st.error("This session could not be loaded. Check the session ID and try again.")
        st.stop()

    answers = session.state.get("intake_data", {})
    st.sidebar.subheader("Saved intake")
    if answers:
        for field, item in answers.items():
            if isinstance(item, dict):
                st.sidebar.write(f"**{field.replace('_', ' ').title()}**: {item.get('value', '')}")
    else:
        st.sidebar.write("No answers saved yet.")
    st.sidebar.caption(f"Status: {session.state.get('intake_status', 'in_progress')}")

    if "messages" not in st.session_state:
        st.session_state.messages = []
    for role, content in st.session_state.messages:
        with st.chat_message(role):
            st.markdown(content)

    prompt = st.chat_input("Ask an intake or healthcare question")
    if prompt:
        st.session_state.messages.append(("user", prompt))
        with st.chat_message("user"):
            st.markdown(prompt)
        try:
            response = asyncio.run(_run_turn(runner, service, session_id, prompt))
        except Exception:
            response = "I couldn't safely process that request. Please try again."
        st.session_state.messages.append(("assistant", response))
        with st.chat_message("assistant"):
            st.markdown(response)


if __name__ == "__main__":
    main()
