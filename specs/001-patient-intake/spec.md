# Feature Specification: Patient Intake Assistant

**Feature Branch**: `001-patient-intake`

**Created**: 2026-10-06

**Status**: Draft

**Input**: User description: "Create a specification for a Patient Intake Assistant with patient intake, healthcare guardrail, session persistence, and RAG-powered answers."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Complete Patient Intake (Priority: P1)

As a patient, I want to answer questions about my symptoms, allergies, medications, and
medical history so the care team has accurate information before my visit.

**Why this priority**: Collecting a complete and reliable intake is the primary purpose
of the assistant and provides direct value before a visit.

**Independent Test**: A patient completes an intake and reviews the collected answers;
the care team receives a summary containing the answers provided.

**Acceptance Scenarios**:

1. **Given** a patient starts an intake, **When** the assistant requests information,
   **Then** it asks one question at a time about symptoms, allergies, medications, and
   medical history.
2. **Given** a patient has answered a question during the current session, **When** the
   intake continues or the patient repeats a question, **Then** the assistant uses the
   recorded answer and does not ask that question again.
3. **Given** allergies or medications have already been answered in the current session,
   **When** the intake continues or resumes, **Then** the assistant never re-asks those
   questions.
4. **Given** the required intake questions have been answered, **When** the intake ends,
   **Then** the assistant presents a confirmation of collected information and allows
   the patient to correct inaccurate entries.

---

### User Story 2 - Stay Within Healthcare Scope (Priority: P1)

As a healthcare administrator, I want the assistant to refuse non-healthcare questions
so that it stays focused on patient intake and compliant use.

**Why this priority**: The scope guard protects patients and must apply to every
interaction before medical generation begins.

**Independent Test**: Submit healthcare and non-healthcare requests and verify that
non-healthcare requests receive the specified refusal without invoking a language model.

**Acceptance Scenarios**:

1. **Given** a patient asks a non-healthcare question such as "What is the weather?",
   **When** the request is checked, **Then** the assistant responds exactly: "I am a
   healthcare intake assistant. I can only help with patient intake questions."
2. **Given** a request is outside healthcare intake scope, **When** it is received,
   **Then** the guardrail rejects it before any model invocation.

---

### User Story 3 - Resume an Intake (Priority: P2)

As a patient, I want intake progress to survive an app restart so that I can continue
without losing answers after a connection drop.

**Why this priority**: Recovery preserves patient effort and enables continuity across
interrupted visits.

**Independent Test**: Answer several intake questions, restart the app, resume using the
same session identifier, and verify prior answers remain available without being asked
again.

**Acceptance Scenarios**:

1. **Given** an intake has saved answers, **When** the app restarts and the patient resumes
   with the same `session_id`, **Then** the assistant restores the saved progress.
2. **Given** a patient resumes a session with saved allergy or medication answers,
   **When** intake continues, **Then** those questions are not re-asked.

---

### User Story 4 - Ask a Verified Healthcare Question (Priority: P2)

As a patient, I want accurate answers to healthcare questions from verified sources so I
can understand information relevant to my intake.

**Why this priority**: Grounded answers help patients while keeping clinical information
reliable and transparent.

**Independent Test**: Ask a question supported by the healthcare knowledge corpus and one
that is not supported; verify sourced answers and the specified no-results response.

**Acceptance Scenarios**:

1. **Given** a healthcare question has relevant material in the verified corpus, **When**
   the patient asks it, **Then** the assistant retrieves relevant material and answers
   with a source citation when one is available.
2. **Given** retrieval returns no relevant results, **When** the patient asks a healthcare
   question, **Then** the assistant says exactly: "I don't have verified information on
   that" and does not invent an answer.

### Edge Cases

- A patient asks a non-healthcare question (for example, "What is the weather?"); the
  healthcare-scope refusal is returned before model invocation.
- A patient repeats a question already answered; the assistant uses the session answer
  rather than asking for the same information again.
- A patient returns after an app restart; the same `session_id` restores the intake
  progress, including allergy and medication answers.
- The conversation exceeds the available context limit; earlier relevant answers remain
  available through a concise summary, and the assistant does not ask those questions
  again.
- The patient gives an unclear or incomplete answer; the assistant asks one focused
  clarification question and retains the information already collected.
- The verified corpus has no relevant result or is unavailable; the assistant does not
  present an unsupported medical answer and communicates that verified information is
  unavailable.
- The patient corrects an answer during final confirmation; the corrected value replaces
  the earlier value in the confirmed intake.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The assistant MUST collect the patient's symptoms, allergies, medications,
  and medical history before completing intake.
- **FR-002**: The assistant MUST ask no more than one intake question at a time.
- **FR-003**: The assistant MUST retain answers throughout the active session and use them
  when deciding what information remains to be collected.
- **FR-004**: The assistant MUST NOT ask again for allergy or medication information that
  the patient already answered in the same session, including after session resumption.
- **FR-005**: The assistant MUST present a summary of collected intake data at completion
  and allow the patient to correct it before confirmation.
- **FR-006**: The assistant MUST reject non-healthcare requests before model invocation
  and respond exactly: "I am a healthcare intake assistant. I can only help with patient
  intake questions."
- **FR-007**: The assistant MUST persist all session state in SQLite and MUST restore
  intake progress when resumed using the same `session_id`.
- **FR-008**: The assistant MUST retrieve healthcare answers from the verified healthcare
  RAG corpus and cite a source when one is available.
- **FR-009**: When retrieval returns no relevant result, the assistant MUST respond exactly:
  "I don't have verified information on that" and MUST NOT invent a medical answer.
- **FR-010**: The assistant MUST preserve safety-critical intake facts when managing
  conversation context that exceeds the available token limit, using a sliding window and
  summary of relevant earlier turns.
- **FR-011**: The assistant MUST validate patient input before any model invocation and
  validate medical output before presenting it.
- **FR-012**: Session data MUST remain scoped to its session and MUST NOT be disclosed to
  another session.

### Key Entities *(include if data involved)*

- **Intake Session**: A patient's active or resumable intake, identified by a `session_id`,
  with progress and collected responses.
- **Intake Response**: A patient-provided answer associated with an intake topic, including
  symptoms, allergies, medications, or medical history, and its confirmation or correction
  status.
- **Retrieved Source**: Verified healthcare material used to support an answer, with source
  details suitable for citation when available.
- **Intake Summary**: The consolidated responses presented to the patient for confirmation
  at the end of intake.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In acceptance scenarios, patients are asked only one intake question at a time
  and complete all four required intake topics before final confirmation.
- **SC-002**: In 100% of repeated-question and resumed-session scenarios, previously answered
  allergy and medication questions are not asked again.
- **SC-003**: In 100% of non-healthcare request scenarios, the exact refusal is returned and
  no model invocation occurs.
- **SC-004**: In 100% of restart recovery scenarios using the same `session_id`, saved intake
  answers are restored without loss.
- **SC-005**: In 100% of retrieval scenarios, supported answers cite an available source and
  no-result cases use the specified response without unsupported medical claims.
- **SC-006**: Patients can review and correct collected information before confirming the
  completed intake.

## Assumptions

- Intake begins when a patient opens or resumes an intake session; identity verification and
  account enrollment are outside this feature's scope.
- The patient or application can supply the same `session_id` when resuming an existing
  session.
- The verified healthcare corpus is available to the assistant and provides source metadata
  when citations are possible.
- The assistant collects information and provides grounded general answers; it does not
  diagnose conditions, prescribe treatment, or replace a clinician.
- SQLite is the required persistence store for all session state, as specified by the
  project constitution and feature request.
- When the context limit is approached, a summary preserves all collected intake answers
  needed for continuity; the patient is asked to clarify only genuinely missing or ambiguous
  information.
