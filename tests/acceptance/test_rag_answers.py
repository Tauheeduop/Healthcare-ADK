from types import SimpleNamespace

from google.adk.models.llm_response import LlmResponse
from google.genai import types

from healthcare_intake.callbacks.output_safety import validate_rag_output
from healthcare_intake.services.rag_service import normalize_grounding_sources
from healthcare_intake.tools.rag_tools import NO_VERIFIED_INFORMATION, answer_for_retrieval_result


def test_empty_retrieval_returns_exact_required_fallback():
    assert answer_for_retrieval_result([]) == "I don't have verified information on that"
    assert answer_for_retrieval_result([]) == NO_VERIFIED_INFORMATION


def test_rag_output_without_grounding_is_replaced_with_exact_fallback():
    response = LlmResponse(
        content=types.Content(role="model", parts=[types.Part(text="Unsupported answer")]),
        turn_complete=True,
    )
    safe = validate_rag_output(SimpleNamespace(), response)
    assert safe.content.parts[0].text == NO_VERIFIED_INFORMATION


def test_rag_output_with_retrieved_source_metadata_is_allowed():
    metadata = types.GroundingMetadata(
        grounding_chunks=[
            types.GroundingChunk(
                retrieved_context=types.GroundingChunkRetrievedContext(
                    uri="https://health.example/source",
                    title="Verified healthcare source",
                    text="Source evidence",
                )
            )
        ]
    )
    response = LlmResponse(
        content=types.Content(role="model", parts=[types.Part(text="Grounded answer")]),
        grounding_metadata=metadata,
        turn_complete=True,
    )
    context = SimpleNamespace(state={})
    assert validate_rag_output(context, response) is None
    assert context.state["rag_sources"] == [
        {"uri": "https://health.example/source", "title": "Verified healthcare source"}
    ]


def test_source_normalization_ignores_missing_citation_fields():
    metadata = types.GroundingMetadata(
        grounding_chunks=[types.GroundingChunk(retrieved_context=types.GroundingChunkRetrievedContext(text="evidence"))]
    )
    assert normalize_grounding_sources(metadata) == []


def test_non_rag_grounding_does_not_satisfy_verified_corpus_requirement():
    metadata = types.GroundingMetadata(
        grounding_chunks=[
            types.GroundingChunk(
                web=types.GroundingChunkWeb(uri="https://example.org", title="Web result")
            )
        ]
    )
    response = LlmResponse(
        content=types.Content(role="model", parts=[types.Part(text="Unverified answer")]),
        grounding_metadata=metadata,
        turn_complete=True,
    )
    safe = validate_rag_output(SimpleNamespace(state={}), response)
    assert safe.content.parts[0].text == NO_VERIFIED_INFORMATION
