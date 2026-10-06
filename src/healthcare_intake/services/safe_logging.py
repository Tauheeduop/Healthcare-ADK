"""Logging helpers that deliberately exclude patient content and identifiers."""

from __future__ import annotations

import logging

logger = logging.getLogger("healthcare_intake")


def log_event(event_name: str) -> None:
    """Record a fixed event label only; never pass patient text, answers, or IDs."""
    logger.info("intake_event=%s", event_name)
