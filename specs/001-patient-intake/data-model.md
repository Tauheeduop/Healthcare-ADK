# Data Model: Patient Intake Assistant

## Intake Session

Represents one resumable visit intake.

| Field | Meaning | Validation |
|---|---|---|
| `app_name` | ADK application scope | Required and stable for this application |
| `user_id` | Authenticated user scope | Required; must be checked before session access |
| `session_id` | Stable identifier used to resume | Required; unique within the app/user scope |
| `status` | Intake lifecycle state | `in_progress`, `awaiting_confirmation`, or `confirmed` |
| `intake_answers` | Structured answers by intake topic | JSON-serializable; only values supplied or confirmed by patient |
| `conversation_summary` | Summary of older relevant turns | Optional text; cannot replace canonical structured answers |
| `created_at`, `updated_at` | Session timestamps | UTC timestamps |
| `events` | Ordered conversation and state changes | Persisted; associated with the owning session |

The ADK session service uses `(app_name, user_id, session_id)` for lookup. Application
authorization must validate the user scope before loading or mutating a session.

## Intake Response

One answer associated with an intake topic.

| Field | Meaning | Validation |
|---|---|---|
| `topic` | Intake category | `symptoms`, `allergies`, `medications`, or `medical_history` |
| `value` | Patient-provided answer | Preserve meaning; validate size and type; do not infer missing facts |
| `status` | Collection state | `answered`, `needs_clarification`, or `corrected` |
| `source_event_id` | Event that supplied or corrected the answer | Must belong to the same session |
| `updated_at` | Last update time | UTC timestamp |

An unanswered topic is absent or explicitly pending. Existing answered allergy and medication
topics are never prompted again. A patient correction replaces the current value while event
history preserves the change for audit.

## Conversation Summary

Persisted context for older turns excluded from the active sliding window.

| Field | Meaning | Validation |
|---|---|---|
| `text` | Concise summary of relevant earlier turns | Must preserve safety-relevant context and not invent facts |
| `covered_through_event_id` | Last event represented by the summary | Must refer to an event in the same session |
| `created_at` | Summary generation time | UTC timestamp |

## Retrieved Source

Verified corpus material used to answer a healthcare question.

| Field | Meaning | Validation |
|---|---|---|
| `uri` | Source location | Retain exact retrieval metadata when available |
| `title` | Human-readable source title | Retain when available |
| `text` | Retrieved evidence | Used only for the current grounded answer; associate with retrieval event |
| `retrieval_id` | Retrieval event identifier | Same session; used to associate citations with the answer |

An empty result set triggers the specified no-verified-information response. A missing URI or
title means citation metadata is unavailable; the agent must not fabricate citation details.

## Intake Summary

The patient-facing review of collected answers before confirmation. It is derived from
canonical `intake_answers`, may contain incomplete topics clearly marked as unanswered, and
must reflect corrections before status transitions to `confirmed`.

## State Transitions

```text
in_progress -> awaiting_confirmation -> confirmed
      ^                 |
      +---- correction -+
```

Persist every transition and answer update in the owning session. A resumed session restores
its state and summary before the next question is selected.
