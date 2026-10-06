# RAG Retrieval Contract

## Request

- Input is a validated healthcare question from the active session.
- Retrieval targets the configured verified healthcare corpus.
- Retrieval execution does not receive patient data from unrelated sessions.

## Result handling

- Preserve retrieved evidence text and available source URI/title with the current answer.
- The response may cite only source metadata actually returned by retrieval.
- The response must remain grounded in retrieved evidence and pass medical output validation.
- If retrieval returns no relevant contexts, return exactly: `I don't have verified information
  on that` and do not supply an unsupported answer.
- Retrieval errors must fail safely: do not substitute model-only medical knowledge; report
  that verified information is unavailable.
