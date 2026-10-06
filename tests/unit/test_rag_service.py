from __future__ import annotations

from healthcare_intake.tools.rag_tools import (
    NO_VERIFIED_INFORMATION,
    answer_for_retrieval_result,
    create_rag_retrieval_tool,
)


def test_vertex_rag_retrieval_tool_uses_configured_corpus():
    tool = create_rag_retrieval_tool("projects/demo/locations/us-central1/ragCorpora/123")
    assert tool is not None
    assert tool.vertex_rag_store.rag_corpora == [
        "projects/demo/locations/us-central1/ragCorpora/123"
    ]


def test_missing_corpus_or_results_fails_closed():
    assert create_rag_retrieval_tool(None) is None
    assert answer_for_retrieval_result([]) == NO_VERIFIED_INFORMATION
    assert answer_for_retrieval_result([{"text": "verified source"}]) is None
