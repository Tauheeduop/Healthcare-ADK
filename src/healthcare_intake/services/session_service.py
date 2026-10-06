"""Construction and lifecycle for ADK's durable SQLite session service."""

from __future__ import annotations

from pathlib import Path

from google.adk.sessions.sqlite_session_service import SqliteSessionService


def create_session_service(db_path: str | Path) -> SqliteSessionService:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return SqliteSessionService(db_path=str(path))


async def close_session_service(service: SqliteSessionService) -> None:
    """Compatibility lifecycle hook; ADK's SQLite service opens per-operation connections."""
    del service
