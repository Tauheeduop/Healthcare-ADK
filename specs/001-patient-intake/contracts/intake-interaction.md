# Intake Interaction Contract

## Request

- A user message is submitted in the active intake session.
- Session lookup is scoped by authenticated `user_id` and stable `session_id`.
- Input is validated for healthcare scope and session boundaries before any model call.

## Responses

- **Off-topic input**: Do not invoke a model. Return exactly: `I am a healthcare intake
  assistant. I can only help with patient intake questions.`
- **Intake prompt**: Ask at most one focused question. Do not ask for an already answered
  allergy or medication topic.
- **Healthcare answer**: Ground claims in retrieved verified corpus material; cite source
  metadata when available.
- **No retrieved evidence**: Return exactly: `I don't have verified information on that`.
- **Intake completion**: Present collected values for review and correction before marking the
  session confirmed.

## Persistence and recovery

- Save state changes against the current session before reporting them as complete.
- Resume by loading the existing session using the same app, user, and session identifiers.
- Never use UI-only state as the durable source of patient answers.
- Never expose one session's data in another session's response.
