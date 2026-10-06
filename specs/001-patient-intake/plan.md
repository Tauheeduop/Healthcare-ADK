# Implementation Plan: Patient Intake Assistant

**Branch**: `001-patient-intake` | **Date**: 2026-10-06 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification at `specs/001-patient-intake/spec.md` and user-provided
architecture and implementation sequence.

## Summary

Build a Streamlit patient intake experience backed by a Google ADK multi-agent workflow.
A deterministic, pre-model healthcare scope gate rejects off-topic input with the exact
required refusal. An accepted request is routed by RootAgent to IntakeAgent or RAGAgent.
SQLite-backed ADK sessions preserve answers and summaries across restarts; a configurable
recent-turn window and persisted summary keep model context bounded. RAG answers use Vertex
AI RAG Engine results and retain source metadata for citations.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Google ADK 1.x (pin a release compatible with `SequentialAgent`,
`ParallelAgent`, and `LlmAgent`); Streamlit; Vertex AI RAG Engine client; `aiosqlite` as
required by the ADK SQLite session service.

**Storage**: SQLite through ADK `SqliteSessionService`; one stable database file for local
deployment, with session state and event history persisted.

**Testing**: pytest unit, integration, and Streamlit/ADK workflow acceptance tests; mocked
model and retrieval boundaries for deterministic safety and no-result scenarios.

**Target Platform**: Local or single-instance Python application with Google Cloud access to
Vertex AI; multi-worker deployment is outside this feature's scope until SQLite concurrency
and shared-storage requirements are specified.

**Project Type**: Single-project Python web application.

**Performance Goals**: Response latency target below 3 seconds and session-state retrieval
below 100 milliseconds, subject to measurement and a defined test environment.

**Constraints**: Off-topic requests must be rejected before any model invocation. Patient
data must remain scoped to its session. SQLite values must be serializable. Context
management must preserve safety-critical intake answers. A model-backed classifier cannot
serve as the pre-model guardrail.

**Scale/Scope**: One patient intake conversation per session; symptoms, allergies,
medications, medical history, session recovery, verified medical Q&A, and final confirmation.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Patient safety and grounding**: Pass. RAGAgent answers only from retrieved verified
  context; empty retrieval yields the exact specified fallback. Validate output before display.
- **Session continuity**: Pass. Read `state.get('intake_answers')` before selecting the next
  question; preserve answer provenance and never repeat answered allergy/medication prompts.
- **Healthcare scope guardrails**: Pass with a design constraint. A deterministic callback
  runs before RootAgent's model. It returns the exact refusal without invoking the model for
  off-topic input. A model-backed GuardrailAgent cannot perform this gate.
- **Durable and private patient data**: Pass. Persist session state and event history in
  SQLite, key access by authenticated user and session, and keep patient data out of unrelated
  logs and cross-session contexts.
- **Bounded context and responsiveness**: Pass. Keep configurable recent turns, summarize
  older relevant turns at a configured token threshold, and persist the summary in session
  state. Measure both constitution latency targets without weakening safety.
- **Technical standards**: Pass with a version constraint. Pin compatible Google ADK 1.x
  because current ADK 2.x documentation marks templated `SequentialAgent` and `ParallelAgent`
  workflows as superseded. Revisit this constraint before upgrading to ADK 2.x.

No constitutional violations remain after these constraints. No complexity exceptions apply.

## Project Structure

### Documentation (this feature)

```text
specs/001-patient-intake/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── intake-interaction.md
    └── rag-retrieval.md
```

### Source Code (repository root)

```text
src/healthcare_intake/
├── agents/
│   ├── root_agent.py
│   ├── intake_agent.py
│   ├── rag_agent.py
│   └── guardrail_agent.py
├── callbacks/
│   ├── input_guardrail.py
│   └── output_safety.py
├── services/
│   ├── session_service.py
│   ├── context_manager.py
│   └── rag_service.py
├── tools/
│   └── intake_tools.py
└── app.py

tests/
├── unit/
├── integration/
└── acceptance/
```

**Structure Decision**: Use a single Python package. Keep ADK agents, guardrail callbacks,
storage/context services, and Streamlit entry point separated so the pre-model safety path
can be tested independently from generation and retrieval.

## Architecture and Flow

1. Streamlit obtains or resumes a stable session identifier and loads the corresponding ADK
   session. Streamlit Session State is only a rerun/UI cache; SQLite is the durable source.
2. The RootAgent's `before_model_callback` invokes the deterministic GuardrailAgent before
   any LLM call. Off-topic input returns the exact refusal immediately. The initial classifier
   is non-generative; uncertain classifications fail closed pending clarification.
3. For accepted healthcare input, RootAgent uses intent to hand off to IntakeAgent or
   RAGAgent. Agent descriptions and routing instructions define these bounded roles.
4. IntakeAgent reads `intake_answers` before asking a single focused question. Intake tools
   save, correct, and retrieve structured answers in the active ADK session state. Existing
   allergy and medication answers are never requested again.
5. For retrieval questions, a ParallelAgent runs retrieval and independent source-metadata
   validation as read-only work. A deterministic merge retains valid source metadata. A
   SequentialAgent then orders evidence checking and response generation. Neither workflow
   gates off-topic input or writes shared intake state. Empty results use the required exact
   fallback.
6. Before display, output safety validation checks that medical claims are grounded and that
   patient data belongs to the active session. Persist state/event changes before reporting
   successful completion to the UI.
7. A configurable context manager retains the last N turns. When the configured token
   threshold is crossed, it summarizes older relevant turns, preserves all intake answers
   and safety-critical facts, stores the summary in session state, and supplies the summary
   plus recent window to the next model call.

## Implementation Sequence

1. Set up the Python ADK project structure and pin a compatible ADK 1.x release.
2. Implement and configure SQLite persistence through `SqliteSessionService`; verify resume
   uses the existing app/user/session identity.
3. Build the deterministic guardrail and pre-model callback; prove off-topic requests stop
   before any model call.
4. Build intake tools for saving, retrieving, and correcting symptoms, allergy, medication,
   and medical-history responses.
5. Build the Vertex AI RAG retrieval tool and preserve source metadata, including empty-result
   behavior.
6. Compose RootAgent intent routing, ordered SequentialAgent workflows, downstream read-only
   ParallelAgent tasks, response validation, and configurable context management.
7. Build the Streamlit interface for one-question-at-a-time intake, confirmation, and session
   resume.
8. Run end-to-end acceptance scenarios for safety gating, continuity, persistence, RAG
   grounding, token-limit handling, and recovery.

## Complexity Tracking

No constitution violations requiring an exception.
