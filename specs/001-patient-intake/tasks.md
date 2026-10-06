# Tasks: Patient Intake Assistant

**Input**: Design documents from `specs/001-patient-intake/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`

**Tests**: Included because the task request explicitly asks for tool unit tests, an end-to-end integration test, and guardrail tests.

**Organization**: Tasks are grouped by spec user story. Shared project setup and safety/persistence foundations precede story work.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel with other marked tasks in the same phase because it uses separate files and has no unfinished dependency.
- **[Story]**: User story mapping from `spec.md`.
- Every task includes the file path it creates or changes.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize the Python application and shared configuration.

- [x] T001 Create the `src/healthcare_intake/` package and `tests/unit/`, `tests/integration/`, and `tests/acceptance/` directories per `specs/001-patient-intake/plan.md`.
- [x] T002 Use the already installed project dependencies; do not reinstall them.
- [x] T003 [P] Use the existing local `.env` and its `GOOGLE_API_KEY`; do not recreate or overwrite the user's credentials.
- [x] T004 [P] Implement validated environment configuration for model credentials, RAG corpus, SQLite path, recent-turn window, and token threshold in `src/healthcare_intake/config.py`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Provide safe input gating and durable session primitives required by the stories.

- [x] T005 Implement an ADK `SqliteSessionService` factory and lifecycle wrapper using the installed API in `src/healthcare_intake/services/session_service.py`; do not subclass `BaseSessionService` or reimplement ADK event persistence.
- [x] T006 Implement session lookup and resume helpers scoped by `app_name`, session capability, and `session_id` in `src/healthcare_intake/services/session_repository.py`.
- [x] T007 Implement a deterministic, non-generative healthcare scope classifier and exact refusal response in `src/healthcare_intake/agents/guardrail_agent.py`.
- [x] T008 Implement the RootAgent `before_model_callback` to validate scope before any model call and return the exact refusal for off-topic input in `src/healthcare_intake/callbacks/input_guardrail.py`.
- [x] T009 Implement model-bound input validation and content-free logging in `src/healthcare_intake/services/input_validation.py` and `src/healthcare_intake/services/safe_logging.py`.

**Checkpoint**: Shared configuration, durable-session construction, and a non-model safety gate are available before user-facing agent flows are connected.

---

## Phase 3: User Story 1 - Complete Patient Intake (Priority: P1) — MVP

**Goal**: Collect symptoms, allergies, medications, and medical history one question at a time, preserve answers, and confirm the completed intake.

**Independent Test**: Run the intake flow with a patient who answers all four topics, repeats an answered question, and corrects an answer at review; verify one question per turn, no repeated allergy/medication prompts, and an updated final summary.

### Tests for User Story 1

- [x] T010 [P] [US1] Add unit tests for saving, retrieving, and checking answered intake fields in `tests/unit/test_intake_tools.py`.
- [x] T011 [P] [US1] Add agent-flow tests for one-question-at-a-time behavior, repeated questions, and corrected confirmation data in `tests/acceptance/test_intake_flow.py`.

### Implementation for User Story 1

- [x] T012 [P] [US1] Define validated intake topic and response structures for symptoms, allergies, medications, and medical history in `src/healthcare_intake/models/intake.py`.
- [x] T013 [US1] Implement `save_patient_info(field, value)`, `get_patient_info(field)`, and `check_if_answered(field)` against the session state key `intake_data` in `src/healthcare_intake/tools/intake_tools.py`.
- [x] T014 [US1] Implement IntakeAgent instructions and tool wiring so it checks saved state before selecting exactly one unanswered or genuinely ambiguous question in `src/healthcare_intake/agents/intake_agent.py`.
- [x] T015 [US1] Implement intake completion summary and correction handling, updating canonical session data before confirmation, in `src/healthcare_intake/tools/intake_tools.py`.
- [x] T016 [US1] Implement the Streamlit intake chat surface with `st.chat_message` and a single current question in `src/healthcare_intake/app.py`.

**Checkpoint**: The IntakeAgent can be tested independently; do not expose it through the app until the RootAgent safety gate and routing in User Story 2 are complete.

---

## Phase 4: User Story 2 - Stay Within Healthcare Scope (Priority: P1)

**Goal**: Reject off-topic requests with the required exact response before invoking any model.

**Independent Test**: Submit a healthcare intake message and an off-topic message such as “What is the weather?”; assert the exact refusal for the latter and zero model calls for that request.

### Tests for User Story 2

- [x] T017 [P] [US2] Add tests proving healthcare input passes and off-topic input returns the exact refusal without a model invocation in `tests/unit/test_input_guardrail.py`.
- [x] T018 [P] [US2] Add callback integration tests proving the guardrail executes before RootAgent model invocation in `tests/integration/test_guardrail_order.py` and `tests/integration/test_root_pipeline_preflight.py`.

### Implementation for User Story 2

- [x] T019 [US2] Wire the deterministic GuardrailAgent through `before_model_callback` on RootAgent and route accepted requests by intent to IntakeAgent or RAGAgent in `src/healthcare_intake/agents/root_agent.py`.
- [x] T020 [US2] Add fail-closed handling for ambiguous scope classifications while preserving the required exact refusal for off-topic requests in `src/healthcare_intake/agents/guardrail_agent.py`.

**Checkpoint**: Every entry to an LLM-backed agent is protected by the pre-model callback; the classifier itself makes no model call.

---

## Phase 5: User Story 3 - Resume an Intake (Priority: P2)

**Goal**: Restore persisted answers after restart using the same authenticated session identity.

**Independent Test**: Save answers, restart the app, resume with the same `app_name`, `user_id`, and `session_id`, and verify all answers return without re-asking allergies or medications; verify another user's session cannot read them.

### Tests for User Story 3

- [x] T021 [P] [US3] Add SQLite session service tests for create, get, durable event timestamps, close, and same-ID resume in `tests/integration/test_sqlite_session_service.py`.
- [x] T022 [P] [US3] Add restart and cross-session isolation acceptance tests in `tests/acceptance/test_session_recovery.py` and `tests/integration/test_sqlite_session_service.py`.

### Implementation for User Story 3

- [x] T023 [US3] Configure `SqliteSessionService` in the ADK Runner and persist session state/events through supported ADK APIs in `src/healthcare_intake/app.py` and `src/healthcare_intake/services/session_service.py`.
- [x] T024 [US3] Rehydrate `intake_data` and saved summary from the existing session before the next question is selected in `src/healthcare_intake/services/session_repository.py`.
- [x] T025 [US3] Implement session creation/resume and display the current session identifier and intake progress in the Streamlit sidebar in `src/healthcare_intake/app.py`.

**Checkpoint**: A restart preserves patient progress in SQLite; session identifiers are never treated as authorization by themselves.

---

## Phase 6: User Story 4 - Ask a Verified Healthcare Question (Priority: P2)

**Goal**: Answer healthcare questions from the verified RAG corpus with available citations and a safe exact fallback when no evidence is found.

**Independent Test**: Ask one question with corpus support and one without; verify grounded text and source metadata for the supported answer and the exact no-results response for the unsupported answer.

### Tests for User Story 4

- [x] T026 [P] [US4] Add retrieval tests for configured corpus, source metadata, empty results, and safe fallback in `tests/unit/test_rag_service.py` and `tests/acceptance/test_rag_answers.py`.
- [x] T027 [P] [US4] Add RAGAgent tests proving only returned source metadata is retained and no-grounding results use the exact response in `tests/acceptance/test_rag_answers.py`.

### Implementation for User Story 4

- [x] T028 [US4] Configure Vertex AI `VertexAiRagRetrieval` for the configured corpus and normalize returned source URI/title metadata in `src/healthcare_intake/services/rag_service.py`.
- [x] T029 [US4] Implement RAGAgent instructions that answer only from retrieved evidence, retain returned metadata, and return the exact fallback when grounding is empty in `src/healthcare_intake/agents/rag_agent.py` and `src/healthcare_intake/callbacks/output_safety.py`.
- [x] T030 [US4] Compose `ParallelAgent` deterministic scope/input preflight before RootAgent and `SequentialAgent` intake/RAG workflows in `src/healthcare_intake/agents/root_agent.py`, `src/healthcare_intake/agents/intake_agent.py`, and `src/healthcare_intake/agents/rag_agent.py`.

**Checkpoint**: Verified Q&A is independently testable and cannot fall back to unsupported model knowledge when retrieval is empty or unavailable.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Complete context management, end-to-end verification, and operational guidance across stories.

- [x] T031 [P] Implement configurable sliding-window selection and threshold-triggered summarization, persisting the summary without replacing canonical intake data, in `src/healthcare_intake/services/context_manager.py`.
- [x] T032 Implement grounded medical output validation and session-scoped handling before display in `src/healthcare_intake/callbacks/output_safety.py`.
- [x] T033 [P] Add tests proving context summarization retains intake answers across token pressure and session resume in `tests/integration/test_context_management.py`.
- [x] T034 Add local end-to-end integration coverage for guardrail, intake, persistence, RAG fallback, and confirmation in `tests/integration/test_patient_intake_flow.py`.
- [ ] T035 Validate live model response latency and local session retrieval targets, recording environment and measurements in `tests/acceptance/test_performance_targets.py`; live model latency remains unmeasured.
- [x] T036 Run local/mock quickstart scenarios and record cloud-only deviations in `specs/001-patient-intake/quickstart-results.md`.

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; T003 and T004 can run in parallel after directory creation.
- **Foundational (Phase 2)**: Depends on setup. Session service setup and deterministic guardrail can proceed independently after configuration; all story integration depends on this phase.
- **US1 (Phase 3)** and **US2 (Phase 4)**: Both are P1. Their agent behavior can be implemented in parallel after foundations; final user-facing flows require the RootAgent safety gate.
- **US3 (Phase 5)**: Depends on the shared SQLite service from Phase 2 and intake state shape from US1.
- **US4 (Phase 6)**: Depends on shared configuration and RootAgent routing from US2; retrieval/answer work is isolated from intake state mutation.
- **Polish (Phase 7)**: Depends on the stories selected for the release; final full-flow and performance checks require all four stories.

### User Story Dependencies

- **US1 (P1)**: Depends only on foundational session-state and safety interfaces; independently testable with a test session.
- **US2 (P1)**: Depends only on the foundational deterministic guardrail; RootAgent routing wires the accepted flow after IntakeAgent and RAGAgent exist.
- **US3 (P2)**: Depends on session service foundation and US1's answer-state shape; adds durable restart recovery and user-scoped access.
- **US4 (P2)**: Depends on the foundational validated configuration and US2's RootAgent routing; does not depend on US1's intake collection behavior.

### Parallel Opportunities

- Setup: T003 and T004 can run in parallel after T001.
- Foundations: T005/T006 and T007/T008 touch separate services and can be developed in parallel; T009 can proceed independently once configuration exists.
- US1: T010, T011, and T012 are separate tests/model files and can begin together; implementation of tools and agent behavior follows their contracts.
- US2: T017 and T018 are separate test files and can be authored in parallel; callback wiring follows the foundational callback.
- US3: T021 and T022 can be authored in parallel; session UI work can proceed independently from recovery test creation.
- US4: T026 and T027 can be authored in parallel; service and agent implementation follow result contract agreement.
- Polish: T031, T032, and T033 touch separate context, output-safety, and test files; T034 depends on story integrations.

## Parallel Examples

### User Story 1

```text
Task: T010 tests/unit/test_intake_tools.py
Task: T011 tests/acceptance/test_intake_flow.py
Task: T012 src/healthcare_intake/models/intake.py
```

### User Story 2

```text
Task: T017 tests/unit/test_input_guardrail.py
Task: T018 tests/integration/test_guardrail_order.py
```

### User Story 3

```text
Task: T021 tests/integration/test_sqlite_session_service.py
Task: T022 tests/acceptance/test_session_recovery.py
```

### User Story 4

```text
Task: T026 tests/unit/test_rag_service.py
Task: T027 tests/acceptance/test_rag_answers.py
```

## Implementation Strategy

### MVP First

Build User Story 1 first as the patient value slice. The minimum safe releasable MVP includes
both P1 stories: complete intake and the US2 pre-model refusal gate wired into RootAgent.
Do not expose a model-backed intake path until the guardrail integration task is complete.

### Incremental Delivery

1. Complete setup and foundations.
2. Build and independently validate US1 intake capture and confirmation.
3. Complete US2 and verify exact pre-model refusal, then route accepted input to the intake flow.
4. Add US3 restart recovery and session isolation.
5. Add US4 RAG-grounded healthcare answers.
6. Complete context, output-safety, end-to-end, and performance checks.

## Notes

- `SqliteSessionService` is the ADK implementation; do not create a parallel custom
  `BaseSessionService` implementation or manually append events that ADK Runner already
  persists.
- A model-backed parallel guardrail or classification prompt cannot satisfy rejection before
  any model invocation. The scope check is deterministic and runs in `before_model_callback`;
  `ParallelAgent` is reserved for independent downstream RAG work.
- The task request names `intake_data` as the session-state key; these tasks use that key
  consistently. Align implementation with this feature-specific name even though earlier
  planning notes used `intake_answers`.
- Never put real credentials in committed files. `.env.example` documents required keys; a
  local `.env` remains untracked.
- Each task uses the required checkbox, sequential ID, optional `[P]`, story label where
  applicable, and an explicit target path.
