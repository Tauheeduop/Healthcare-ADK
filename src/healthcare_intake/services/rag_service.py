"""Configured Vertex AI RAG Engine retrieval integration."""

from __future__ import annotations

from google.adk.tools.retrieval.vertex_ai_rag_retrieval import VertexAiRagRetrieval
from google.genai import types


def create_vertex_rag_retrieval(corpus: str | None) -> VertexAiRagRetrieval | None:
    if not corpus:
        return None
    return VertexAiRagRetrieval(
        name="retrieve_healthcare_sources",
        description=(
            "Retrieve verified healthcare source passages for the patient's medical "
            "question. Use this before answering any healthcare knowledge question."
        ),
        rag_corpora=[corpus],
        similarity_top_k=5,
    )


def normalize_grounding_sources(metadata: types.GroundingMetadata | None) -> list[dict[str, str]]:
    """Extract only source details actually returned by Vertex grounding metadata."""
    normalized: list[dict[str, str]] = []
    for chunk in getattr(metadata, "grounding_chunks", None) or []:
        source = getattr(chunk, "retrieved_context", None)
        if source is None:
            continue
        entry = {
            key: value
            for key, value in {
                "uri": getattr(source, "uri", None),
                "title": getattr(source, "title", None),
            }.items()
            if isinstance(value, str) and value
        }
        if entry:
            normalized.append(entry)
    return normalized
