"""Bound model context with a recent-turn window and persisted extractive summary."""

from __future__ import annotations

from google.genai import types


def _text(content: types.Content) -> str:
    return " ".join(part.text for part in (content.parts or []) if part.text)


def manage_request_context(request, state, *, last_n_turns: int, token_threshold: int) -> None:
    """Summarize old contents when over threshold, preserve a sliding window, and persist it.

    A token estimate of four characters per token avoids an additional external model call.
    Canonical intake data remains stored separately under `intake_data`.
    """
    contents = list(request.contents or [])
    if not contents:
        return
    window_size = max(2, last_n_turns * 2)
    estimated_tokens = sum(len(_text(item)) for item in contents) // 4
    summary = str(state.get("conversation_summary", ""))

    if estimated_tokens > token_threshold and len(contents) > window_size:
        old = contents[:-window_size]
        old_text = "\n".join(
            f"{item.role or 'turn'}: {_text(item)}" for item in old if _text(item)
        )
        combined = "\n".join(part for part in (summary, old_text) if part)
        # Keep the summary compact; the structured intake data is the source of truth.
        summary = combined[-4000:]
        state["conversation_summary"] = summary
        request.contents = contents[-window_size:]

    if summary:
        summary_content = types.Content(
            role="user",
            parts=[types.Part(text=f"Earlier conversation summary for continuity: {summary}")],
        )
        request.contents = [summary_content, *(request.contents or [])]
