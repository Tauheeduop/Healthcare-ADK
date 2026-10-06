"""Vertex AI RAG retrieval tool configuration and safe empty-result behavior."""

from __future__ import annotations

from google.adk.tools.retrieval.vertex_ai_rag_retrieval import VertexAiRagRetrieval

from healthcare_intake.services.rag_service import create_vertex_rag_retrieval

NO_VERIFIED_INFORMATION = "I don't have verified information on that"


def create_rag_retrieval_tool(corpus: str | None) -> VertexAiRagRetrieval | None:
    return create_vertex_rag_retrieval(corpus)


def answer_for_retrieval_result(results: list[object]) -> str | None:
    """Return the required fallback when retrieval has no evidence."""
    return None if results else NO_VERIFIED_INFORMATION
