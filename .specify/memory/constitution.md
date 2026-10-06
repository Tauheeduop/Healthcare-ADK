<!--
Sync Impact Report
- Version change: unratified template → 1.0.0
- Modified principles: template placeholders → Patient Safety and Grounded Responses; Visit Session Continuity; Healthcare Scope Guardrails; Durable and Private Patient Data; Bounded Context and Responsive Operation
- Added sections: Technical and Performance Standards; Security and Quality Workflow
- Removed sections: none
- Follow-up TODO: confirm the original ratification date.
-->
# Healthcare Multi-Agent Orchestration System Constitution

## Core Principles

### I. Patient Safety and Grounded Responses
Every patient-facing medical claim MUST be supported by verified medical data or relevant
Vertex AI RAG Engine retrieval. Agents MUST identify uncertainty, avoid unsupported diagnosis
or treatment claims, and direct users to appropriate professional care when the system cannot
answer safely. Safety takes precedence over latency or conversational completeness.

### II. Visit Session Continuity
Information a patient has already provided during the current visit MUST remain available to
subsequent agents and MUST NOT be requested again unless clarification is necessary because it
is missing, ambiguous, or potentially changed. Session handoffs MUST preserve relevant facts
and their provenance.

### III. Healthcare Scope Guardrails
The system MUST reject non-healthcare requests before they reach healthcare agents and return
a clear, respectful refusal that explains its healthcare scope. Guardrails MUST also prevent
unsafe or out-of-scope medical responses at the output boundary.

### IV. Durable and Private Patient Data
Patient and session data needed for continuity, audit, and recovery MUST persist in SQLite.
Access MUST be scoped to the active session and authorized workflow. Patient-identifying data
MUST NOT be exposed outside that session or included in unrelated logs, outputs, or retrieval
contexts.

### V. Bounded Context and Responsive Operation
Conversation context MUST use a sliding window with summaries of relevant earlier turns to
control token growth while preserving safety-critical facts. The implementation MUST target
response latency below 3 seconds and session-state retrieval below 100 milliseconds; any
measured breach MUST be visible in performance review and addressed without weakening safety.

## Technical Standards

The application MUST use Python 3.11 or newer, Google ADK agent primitives (`LlmAgent`,
`SequentialAgent`, and `ParallelAgent`), SQLite for persistent session storage, Streamlit for
the user interface, and Vertex AI RAG Engine for retrieval. Input validation MUST occur before
any model call. Outputs MUST be validated for medical safety before delivery. Changes to these
standards require an explicit constitution amendment.

## Security and Quality Workflow

Every model-bound input MUST be validated for healthcare scope, malformed content, and
session boundaries. Every patient-facing output MUST pass safety validation and must not leak
PII across sessions. Design and review artifacts MUST describe how session continuity, durable
storage, retrieval grounding, and both latency targets are preserved. Compliance reviews MUST
include checks for these controls and document exceptions with rationale and remediation.

## Governance

This constitution governs product behavior, architecture, and development decisions. Amendments
MUST be proposed as a documented change describing the rationale and impact on existing
requirements. Each change MUST be reviewed for patient safety, privacy, compatibility, and
compliance before adoption. Projects and reviews MUST check relevant work against these
principles; a conflict MUST be resolved in favor of patient safety and privacy.

Versioning follows semantic versioning: MAJOR for incompatible changes to principles or
governance, MINOR for added principles or materially expanded requirements, and PATCH for
clarifications that do not change obligations. The project MUST review compliance at feature
planning and implementation review, and revisit this constitution when a requirement or
technology standard changes. Any approved exception MUST be documented, scoped, and time-bound.

**Version**: 1.0.0 | **Ratified**: TODO(RATIFICATION_DATE): confirm original adoption date | **Last Amended**: 2026-10-06
