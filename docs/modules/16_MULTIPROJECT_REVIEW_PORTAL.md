# Module 16 — Multi-project persistence and human review portal

## Outcome

Specvora now persists multiple projects and proposal-review state in SQLite. The local portal
at `/portal` lists registered projects, shows the durable review queue, loads proposal details,
and lets a person accept or reject every proposal with a rationale and final confirmation.

## Authority and data flow

1. A project JSON is validated and confined to its declared workspace.
2. A proposal envelope is confined, parsed, hash-recorded, and deterministically revalidated.
3. SQLite records the review as `PENDING`; duplicate IDs and proposal hashes are rejected.
4. The human dispositions every proposal and explicitly confirms the immutable decision.
5. The existing Module 14 service creates the review record and promoted catalog.
6. Only after successful promotion does SQLite transition the item to `REVIEWED`.

The database coordinates work but does not replace source artifacts, policy validation, or
human authority. Database files are ignored by Git and the path can be selected with
`SPECVORA_DB_PATH`.

## Local-only boundary

This MVP portal deliberately has no identity provider, role-based authorization, signed
approval, or CSRF defense. Run it on a trusted local machine and do not bind it to an untrusted
network. Those controls are mandatory before a hosted or shared deployment.
