# Training Lab — Controlled Playwright Execution

## Goal

Explain and exercise every policy decision between a generated journey and a browser run.

## Preparation

Generate the example and install its isolated browser-test dependencies only in an
authorized training environment:

```powershell
specvora analyze examples\web_project.json
cd workspaces\web-demo\generated\playwright
npm install
npx playwright install chromium
cd ..\..\..\..
```

## Lab

1. Inspect `playwright-plan.json`, the generated test, and `quality-gate.json`.
2. Run `specvora run-playwright` with `APPROVED`; confirm the dedicated approval rejects it.
3. Use `APPROVED_PLAYWRIGHT` and an allowlisted local training target.
4. Confirm the JSON report is created inside `workspaces/web-demo/runs`.
5. Change the requested port or add an allowlisted host not present in the plan.
6. Confirm plan-drift validation blocks execution.
7. Try to place the report outside the workspace and confirm confinement blocks it.
8. Restore the reviewed inputs and discuss what container isolation would add.

The approved command for the example is:

```powershell
specvora run-playwright `
  --workspace-root workspaces `
  --generated-dir workspaces\web-demo\generated `
  --report-out workspaces\web-demo\runs\playwright.json `
  --web-base-url http://localhost:3000 `
  --allowed-host localhost `
  --approval APPROVED_PLAYWRIGHT
```

## Review questions

- Why does browser execution require a token distinct from API execution?
- Why must runtime inputs match the reviewed plan?
- What does page-level request interception protect, and what does it not protect?
