# Module 21 — Portal promoted generation

The local portal now exposes reviewed promotion scenarios and deterministic request cases,
then accepts an explicit scenario-to-case binding for a new plan. It derives project,
proposal, decision, review and catalog paths from the registered review; browsers cannot
substitute arbitrary source paths.

`GET /api/reviews/{review_id}/generation` returns promoted scenarios, cases grouped by
OpenAPI operation and existing plan IDs. `POST` accepts only a constrained `plan_id` and
typed bindings. Both the binding artifact and generated plan remain inside the registered
workspace. Existing identifiers are rejected and never overwritten.

The portal button generates artifacts only. It does not start a target, sign an action,
execute Pytest, ingest evidence or decide release. Private keys remain outside the portal.
The existing signed runner is the sole execution path.

This remains a local training portal without authenticated sessions. Do not expose it to a
network or treat browser access as user identity. Authentication and production roles are
still pending roadmap work.
