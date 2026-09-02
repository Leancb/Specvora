# Training Lab — Deterministic Playwright Journeys

## Goal

Generate a browser-test proposal and explain why it remains separate from execution.

## Lab

1. Run `specvora analyze examples/web_project.json`.
2. Open `generated/playwright/playwright-plan.json` and trace every declared step.
3. Compare the plan with `test_generated_web.spec.ts`; confirm no selector was invented.
4. Confirm `quality-gate.json` says `READY_FOR_HUMAN_APPROVAL`, not `APPROVED`.
5. Move the first `goto` below a `click` and analyze again.
6. Confirm the gate becomes `BLOCKED` with `INVALID_JOURNEY`.
7. Try a `goto` path beginning with `//` and confirm input validation rejects it.
8. Restore the example and identify the review required before browser execution.

## Review questions

- Why must selectors come from an explicit journey instead of API inference?
- What attack can a protocol-relative path enable?
- Why are a valid gate and human approval still insufficient for unconstrained execution?
