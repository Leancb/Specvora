# Module 11 — Controlled Playwright Execution

## Objective

Run a reviewed Playwright proposal through a narrow execution boundary without allowing
arbitrary commands, paths, targets, or inherited secrets.

## Preconditions

The runner fails closed unless all conditions are true:

1. the approval token is exactly `APPROVED_PLAYWRIGHT`;
2. `quality-gate.json` is `READY_FOR_HUMAN_APPROVAL`;
3. the web base URL host is exactly allowlisted;
4. the requested URL and allowlist match the reviewed `playwright-plan.json`;
5. the generated directory, Playwright files, and report stay inside the workspace;
6. every required generated artifact exists.

The report must also stay outside the generated directory so it cannot overwrite a
reviewed artifact.

The dedicated approval token prevents an API-test approval from silently authorizing a
browser run.

## Fixed execution

The command is constructed internally and runs with `shell=False`:

```text
npx playwright test test_generated_web.spec.ts --config=playwright.config.ts --reporter=json
```

The environment contains only a small runtime allowlist. Application secrets such as
`OPENAI_API_KEY` are not inherited. Execution has a bounded timeout, bounded captured
output, and requires a valid JSON report.

## Browser network boundary

Generated tests install a Playwright route before each journey. Requests whose hostname
is not in the reviewed allowlist are aborted. This covers traffic initiated through the
generated page journeys, including redirects and subresources.

This is an application-level control, not operating-system network isolation. A later
container/egress module must provide defense in depth against a compromised runtime.

## Evidence boundary

The raw Playwright JSON report is written inside the workspace. Module 11 deliberately
does not pass that report to the Pytest evidence normalizer. Browser evidence
normalization and release-confidence integration remain separate work.
