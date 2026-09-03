# Training Lab — Governed AI Proposals

## Goal

Distinguish model proposal, structured-output validation, deterministic semantic policy,
human review, and execution authority.

## Preparation

Use a local `.env` that is ignored by Git:

```text
OPENAI_API_KEY=<configured securely>
SPECVORA_AI_ENABLED=true
SPECVORA_AI_MODEL=gpt-5.6-luna
```

The lab makes a paid API request and requires available OpenAI API credits.

## Lab

```powershell
specvora propose-ai examples\petstore_project.json `
  --workspace-root workspaces `
  --output workspaces\petstore-demo\proposals\ai.json
```

1. Inspect `source`, `model`, `prompt_version`, `input_sha256`, and `authority`.
2. Confirm no URL, key, executable code, or approval appears in the artifact.
3. Compare every requirement and operation ID with the source project and OpenAPI file.
4. Use a test provider fixture to return an invented operation and observe `BLOCKED`.
5. Return a positive scenario with an undocumented status and observe the finding.
6. Disable `SPECVORA_AI_ENABLED` and confirm no API request is attempted.
7. Explain the human decision required before a proposal can become a maintained test.

## Review questions

- Why does valid structured output still need semantic validation?
- Which data is intentionally excluded from the prompt?
- Why is `READY_FOR_HUMAN_REVIEW` not approval?
