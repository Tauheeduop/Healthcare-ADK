# Research: Patient Intake Assistant

## Agent orchestration and guardrail ordering

**Decision**: Use a RootAgent for accepted-request intent routing. Enforce scope in a
deterministic `before_model_callback` before RootAgent calls a model. Use `SequentialAgent`
for operations that require order. Restrict `ParallelAgent` to independent, read-only
retrieval/relevance operations after the scope gate; merge their results explicitly.

**Rationale**: ADK sequential workflows run children in fixed order. Parallel workflows run
independent branches and do not automatically share conversation history or safely coordinate
shared state. A model-backed guardrail cannot reject off-topic requests before any model
invocation because its classification call itself uses a model. Callback refusal is the
documented short-circuit mechanism: return an LLM response to stop that model call; returning
`None` proceeds. The guardrail classifier therefore must not be generative.

**Alternatives considered**: An all-sequential flow cannot route dynamically by intent.
Parallelizing the scope check with the answer path breaks the required gate ordering. An LLM
classifier before the answer agent still violates the literal no-model-call requirement for
off-topic input.

**Version decision**: Pin Google ADK to a compatible 1.x release for the requested
`SequentialAgent` and `ParallelAgent` workflow classes. Current ADK documentation marks these
templated workflows as superseded by graph-based/dynamic workflows starting in ADK 2.0. Review
this pin before an upgrade; do not silently substitute workflow primitives.

Sources: [ADK sequential agents](https://adk.dev/agents/workflow-agents/sequential-agents/),
[ADK parallel agents](https://adk.dev/agents/workflow-agents/parallel-agents/),
[ADK callbacks](https://adk.dev/callbacks/types-of-callbacks/),
[ADK LLM agents](https://adk.dev/agents/llm-agents/).

## SQLite session persistence

**Decision**: Use ADK `SqliteSessionService` with a stable local database path. Resolve a
resume request with the same app name, authenticated user ID, and session ID; fetch an existing
session rather than creating a duplicate. Store visit-level answers and summary in ordinary
session state, and persist event/state changes through the session service.

**Rationale**: The service persists session/event state to SQLite. ADK session identity is
scoped by `(app_name, user_id, session_id)`, so the same session ID alone is not sufficient
authorization or lookup scope. Streamlit Session State is tied to the browser WebSocket and
does not survive reloads, so it can only serve as a UI cache. Do not put patient facts in
`temp:` state because it is ephemeral. Keep state values JSON serializable.

**Alternatives considered**: In-memory ADK state does not survive restart. ADK's general
`DatabaseSessionService` can use SQLite via SQLAlchemy and an async SQLite driver, but the
dedicated service better matches this local single-instance plan. A shared multi-worker
deployment may require revisiting the storage service.

Sources: [ADK session service and resume](https://google.github.io/adk-docs/sessions/session/),
[ADK session state](https://google.github.io/adk-docs/sessions/state/),
[ADK SQLite implementation](https://github.com/google/adk-python/blob/main/src/google/adk/sessions/sqlite_session_service.py),
[Streamlit Session State](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state),
[Streamlit statefulness](https://docs.streamlit.io/develop/concepts/architecture/session-state).

## Context window management

**Decision**: Keep a configurable last-N event/turn window in model context. When a separately
configured token threshold is reached, summarize older turns and persist the summary in ADK
session state. Rehydrate that summary on every resumed session and include it with the recent
window. Keep structured intake answers as canonical state; summaries are not authoritative
replacements for allergy, medication, or other intake fields.

**Rationale**: ADK recent-event loading can bound retrieved history but does not delete old
persisted events or itself implement the required summarization behavior. Explicit summary
state preserves continuity without depending on the limited history window. The spec does not
set N or a token threshold; both remain deployment configuration, with values selected against
the chosen model's context capacity and reserved output budget.

**Alternatives considered**: Sending the entire event history grows context without bound.
Using only a recent-event limit can hide old intake answers and does not satisfy the summary
requirement. Storing answers only in prose summaries risks dropping structured or safety-critical
facts.

Source: [ADK session history configuration and state](https://google.github.io/adk-docs/sessions/session/).

## Vertex AI RAG and citations

**Decision**: Retrieve relevant corpus contexts for healthcare questions, retain returned
source URI/title with each context, and constrain RAGAgent answers to those contexts. If no
relevant contexts are returned, use the exact fallback from the specification. Cite a source
when returned metadata makes one available.

**Rationale**: Vertex AI RAG retrieval returns context records and generation retrieval results
can include source URI, title, and text. Retaining metadata makes citations traceable to
retrieval results rather than model-invented prose.

**Alternatives considered**: Generating citations from model text without source metadata is
not verifiable. Answering from model knowledge when retrieval is empty violates the grounding
requirement.

Sources: [Vertex AI RAG quickstart](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/rag-quickstart),
[Vertex AI retrieved context schema](https://cloud.google.com/vertex-ai/generative-ai/docs/reference/rest/v1/GenerateContentResponse),
[Vertex AI retrieval and ranking](https://cloud.google.com/vertex-ai/generative-ai/docs/retrieval-and-ranking).

## Streamlit interaction

**Decision**: Render only the current intake question, commit the response on submit, then
rerun the app from durable session state. Rehydrate on browser reload/app restart. Keep
patient/session data out of URL query parameters.

**Rationale**: Streamlit reruns the script on interaction, and Session State is not durable
across a WebSocket reset. The durable ADK session service is required for recovery.

**Alternatives considered**: Storing the intake only in Streamlit state loses progress on
reload. Batching multiple intake questions into one form conflicts with the one-question-at-a-
time requirement.

Sources: [Streamlit Session State](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state),
[Streamlit architecture](https://docs.streamlit.io/develop/concepts/architecture/architecture),
[Streamlit forms](https://docs.streamlit.io/develop/concepts/architecture/forms).
