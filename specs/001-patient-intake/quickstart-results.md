# Quickstart Validation Results

**Date**: 2026-10-06

## Completed locally

- Streamlit `AppTest` rendered the Patient Intake Assistant title and chat input without
  application exceptions.
- Intake tool and acceptance tests verified one-field-at-a-time progression, answer saving,
  allergy/medication non-repetition, correction, and confirmation.
- SQLite integration tests verified state and event timestamps survive service recreation,
  same-session resume works, and a different user scope cannot access the session.
- Guardrail tests verified the exact off-topic refusal and zero model invocations through the
  composed deterministic parallel preflight and RootAgent callback.
- Context tests verified old-turn summarization, a bounded recent window, and preservation of
  structured intake data.
- RAG tests verified the configured `VertexAiRagRetrieval`, citation metadata handling, and
  the exact no-grounding fallback.
- Automated suite: `python -m pytest -q --basetemp=.pytest-tmp-run` — 28 passed.
- Python compilation: `python -m compileall -q src/healthcare_intake tests` — passed.
- Local SQLite average state retrieval remained below the 100 ms acceptance target.

## External validation not run

- No live request was sent to Vertex AI or the configured RAG corpus. Real corpus access,
  citation rendering, cloud authentication, and response latency under 3 seconds still need
  a deployment-environment smoke run.
- The installed Google ADK 2.11 emits deprecation warnings for `SequentialAgent` and
  `ParallelAgent`; they execute successfully in the current environment but may be removed
  in a future ADK release.
- No patient data or API key was included in test output.
