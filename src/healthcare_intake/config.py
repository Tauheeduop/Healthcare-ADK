"""Application configuration loaded from the environment and local .env file."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _positive_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a positive integer") from exc
    if parsed < 1:
        raise ValueError(f"{name} must be a positive integer")
    return parsed


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("ADK_APP_NAME", "healthcare_intake")
    model: str = os.getenv("GOOGLE_MODEL", "gemini-2.5-flash")
    google_api_key: str | None = os.getenv("GOOGLE_API_KEY")
    rag_corpus: str | None = os.getenv("RAG_CORPUS")
    sqlite_path: Path = Path(os.getenv("SQLITE_PATH", "data/healthcare_intake.db"))
    recent_turns: int = _positive_int("CONTEXT_LAST_N_TURNS", 10)
    summary_token_threshold: int = _positive_int("CONTEXT_SUMMARY_TOKEN_THRESHOLD", 6000)


settings = Settings()
