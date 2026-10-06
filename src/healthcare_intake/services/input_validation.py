"""Deterministic validation for user input before any model call."""

from __future__ import annotations

MAX_INPUT_LENGTH = 8000


def validate_user_text(text: str) -> str | None:
    if not text.strip():
        return "Please enter a message so I can help with your intake."
    if len(text) > MAX_INPUT_LENGTH:
        return "Please shorten your message and send it again."
    if "\x00" in text:
        return "Please remove unsupported characters and send your message again."
    return None
