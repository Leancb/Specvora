# Module 10 — Deterministic Playwright Journey Generation

## Objective

Turn explicit, declarative web journeys into reviewable Playwright proposals without
guessing selectors, accepting arbitrary scripts, or granting execution authority.

## Journey contract

A project may declare a `web_base_url` and one or more `web_journeys`. Both are required
together. The base URL hostname must exactly match `allowed_hosts`, and each journey must
start with a relative `goto` step.

The deterministic action vocabulary is intentionally small:

- `goto`: navigate to a relative path;
- `click`: click a declared selector;
- `fill`: fill a declared selector with a declared value;
- `assert_visible`: verify that a declared selector is visible.

Protocol-relative paths and arbitrary JavaScript are not part of the model. Values are
JSON encoded before they are written into TypeScript.

## Generated artifacts

The `generated/playwright` directory contains:

- `playwright-plan.json`: normalized, auditable journey intent;
- `playwright.config.ts`: the allowlisted base URL and conservative defaults;
- `test_generated_web.spec.ts`: generated Playwright tests;
- `package.json`: an isolated test-project manifest.

These files are proposals. Generation does not install dependencies, launch a browser, or
authorize a run.

## Quality boundary

Journey validation joins API case validation before `quality-gate.json` is produced. A
journey that does not begin with `goto` raises `INVALID_JOURNEY` and changes the gate to
`BLOCKED`. A valid gate means only that a human may begin review.

## Current limitation

Module 10 generates Playwright artifacts but never executes them. Browser execution,
network confinement, and a dedicated approval record belong to the next module.
