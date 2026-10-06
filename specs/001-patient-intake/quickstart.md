# Quickstart: Patient Intake Assistant

This guide describes end-to-end validation after implementation. The application and tests
are implementation outputs and are not present yet.

## Prerequisites

- Python 3.11 or newer and project dependencies installed.
- Google Cloud credentials with access to the configured Vertex AI RAG corpus and model.
- A configured corpus containing verified healthcare sources for the supported scenarios.
- A writable local directory for the SQLite database.
- The implementation's configured context window size and token summarization threshold.

## Start the application

From the repository root, start Streamlit:

```powershell
streamlit run src/healthcare_intake/app.py
```

Open the local URL printed by Streamlit. Start a new intake session and record its session ID
for resume checks.

## Validate the patient intake flow

1. Begin intake and confirm that only one question is displayed at a time.
2. Answer symptoms, allergies, medications, and medical history.
3. Repeat an allergy or medication question. Confirm the saved answer is used and the topic
   is not requested again.
4. Reach the final review, correct one answer, and confirm the review reflects the correction.

Expected result: all four topics are represented, earlier answers remain available, and the
patient can correct collected information before the session becomes confirmed.

## Validate pre-model healthcare scope gating

1. Submit `What is the weather?` in a fresh session.
2. Inspect the model-call trace for the request.

Expected result: the response is exactly `I am a healthcare intake assistant. I can only
help with patient intake questions.` and the trace contains no model invocation for that
request.

## Validate verified retrieval

1. Ask a healthcare question whose answer is present in the configured corpus.
2. Confirm the answer is grounded in retrieved text and cites returned source metadata when
   available.
3. Ask a question with no matching corpus material.

Expected result: the first answer uses verified evidence; the second says exactly `I don't
have verified information on that` and does not provide an unsupported medical answer.

## Validate restart recovery and isolation

1. Save at least one answer, including allergies and medications, and note the session ID.
2. Stop and restart the application, then resume using the same session ID and authenticated
   user.
3. Confirm saved answers load and allergy/medication prompts are not repeated.
4. Open a different session and verify it cannot access the original session's data.

Expected result: the original session resumes from persisted SQLite state; another session
does not receive its answers.

## Validate context management

1. Configure a small recent-turn window and token threshold for the acceptance environment.
2. Continue the conversation until summarization is triggered.
3. Confirm that older turns are summarized, the summary is persisted, and structured intake
   answers remain intact.
4. Restart and resume, then confirm continuity and no repeated allergy or medication
   questions.

Expected result: recent turns and the persisted summary fit the model context while canonical
intake answers remain available.

## Run automated checks

From the repository root, run the unit, integration, and acceptance suites:

```powershell
python -m pytest
```

Expected result: all tests pass, including explicit assertions that off-topic requests make
zero model calls, resume restores session state, and empty RAG results use the exact fallback.
