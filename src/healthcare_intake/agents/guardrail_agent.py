"""Deterministic healthcare scope classifier used before every model call."""

from __future__ import annotations

import re
from enum import Enum


class Scope(str, Enum):
    HEALTHCARE = "healthcare"
    OFF_TOPIC = "off_topic"


REFUSAL = "I am a healthcare intake assistant. I can only help with patient intake questions."

_HEALTHCARE_TERMS = re.compile(
    r"\b(health|medical|medicine|medication|drug|dose|dosage|symptom|symptoms|"
    r"allerg(?:y|ies|ic)|patient|doctor|clinician|hospital|clinic|treatment|diagnos(?:is|e)|"
    r"pain|fever|cough|headache|nausea|vomit(?:ing)?|rash|hives|dizz(?:y|iness)|"
    r"breath(?:ing)?|blood|heart|pressure|pregnan(?:t|cy)|injur(?:y|ed)|illness|disease|"
    r"surgery|vaccine|vaccination|history|intake|prescription|pill|tablet|capsule)\b",
    re.IGNORECASE,
)
_OFF_TOPIC_TERMS = re.compile(
    r"\b(weather|forecast|sports?|football|basketball|baseball|politics|election|"
    r"stock(?:s| market)?|cryptocurrency|bitcoin|recipe|joke|poem|write code|debug|"
    r"programming|travel itinerary|movie review)\b",
    re.IGNORECASE,
)
_UNRELATED_REQUEST_SHAPE = re.compile(
    r"^\s*(what|who|where|when|why|how|can you|could you|would you|"
    r"tell me|explain|write|create|make|show me|help me)\b",
    re.IGNORECASE,
)
_GREETING = re.compile(r"^\s*(hi|hello|hey|good morning|good afternoon|good evening)[!. ]*\s*$", re.I)


def classify_healthcare_scope(text: str, *, pending_topic: str | None = None) -> Scope:
    normalized = " ".join(text.split())
    if not normalized or _OFF_TOPIC_TERMS.search(normalized):
        return Scope.OFF_TOPIC
    if _GREETING.fullmatch(normalized) or _HEALTHCARE_TERMS.search(normalized):
        return Scope.HEALTHCARE
    if normalized.endswith("?") or _UNRELATED_REQUEST_SHAPE.search(normalized):
        return Scope.OFF_TOPIC
    if pending_topic and normalized.casefold() in {
        "yes", "no", "none", "not sure", "i don't know", "unknown", "skip"
    }:
        return Scope.HEALTHCARE
    if pending_topic and len(normalized.split()) <= 5:
        return Scope.HEALTHCARE
    return Scope.OFF_TOPIC
