# Training lab — Module 16

## Objective

Follow a proposal from a confined project into the durable review queue and through a human
decision without bypassing deterministic promotion policy.

## Exercise

1. Set `SPECVORA_DB_PATH=workspaces/training-specvora.db`.
2. Start `python -m uvicorn specvora.main:app --reload --port 8100`.
3. Use `/docs` to call `POST /api/projects` with a project file inside its workspace.
4. Call `POST /api/reviews` with a READY proposal and unique review ID.
5. Open `http://localhost:8100/portal`, select **Review proposals**, and disposition every item.
6. Inspect the generated decision, review record, promoted catalog, and database queue state.
7. Attempt the same decision again and confirm the immutable transition is rejected.

## Discussion

Explain why the portal is local-only, why dynamic content uses safe text rendering, and why
future authentication and signed approvals are necessary before multi-user deployment.
