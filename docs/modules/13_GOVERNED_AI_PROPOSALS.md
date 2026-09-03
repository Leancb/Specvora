# Module 13 — Governed AI Scenario Proposals

## Objective

Use optional OpenAI assistance to propose additional API quality scenarios without
allowing model output to become code, policy, approval, or execution authority.

## Opt-in boundary

The deterministic pipeline remains the default and does not require an API key. AI
proposals require both:

- an explicit `specvora propose-ai` command;
- `SPECVORA_AI_ENABLED=true` in the active environment.

The API key is loaded from the ignored local environment and is never copied into prompts,
artifacts, generated tests, runner environments, or Git.

## Agent contract

Specvora uses one focused OpenAI Agents SDK agent with no tools and a Pydantic
`AIProposalBatch` output type. The model receives only normalized requirements,
documented operations, and existing scenarios. It does not receive base URLs, host
allowlists, local paths, credentials, or executable access.

The default model is `gpt-5.6-luna`, with an explicit `--model` override for an accountable
cost and model-access policy. The prompt contract is recorded in
`docs/ai/SCENARIO_PROPOSER_PROMPT.md`.

## Deterministic validation

Structured output is necessary but not sufficient. After schema parsing, local policy
checks that:

- proposal IDs are unique;
- each requirement exactly matches project input;
- every operation ID exists in the OpenAPI contract;
- positive statuses match documented success statuses;
- negative statuses are 4xx/5xx and do not overlap documented successes.

Any violation produces a finding and marks the whole envelope `BLOCKED`.

## Provenance and authority

Every saved JSON envelope records the provider family, model, prompt version, input hash,
creation time, validation findings, and the fixed authority marker
`human-review-required`. Passing policy produces `READY_FOR_HUMAN_REVIEW`, never
`APPROVED`.

AI proposals remain separate from deterministic scenarios and generated tests. Promotion
of an accepted proposal requires a future explicit human-review workflow.

## Operational failure

The first live smoke request reached OpenAI successfully but the selected API project had
no remaining credits. Specvora classifies `credit_balance_exhausted` separately from a
transient rate limit and does not retry automatically.
