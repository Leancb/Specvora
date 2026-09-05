# Specvora Training Guide

## Audience

QA engineers, developers, technical leaders, auditors, and product stakeholders learning autonomous quality engineering with human authority.

## Learning path

### Lesson 1 — Product and governance

Explain the principle: AI proposes, deterministic policies validate, and people retain authority. Identify requirements, contracts, generated code, and external targets as untrusted inputs.

Exercise: review `docs/PRODUCT.md`, `docs/ARCHITECTURE.md`, and `docs/SECURITY.md`. Describe who may authorize execution and why generation is not execution.

### Lesson 2 — Deterministic analysis

Run:

```powershell
specvora analyze examples\petstore_project.json
```

Inspect `quality-plan.json`, `traceability.json`, `test_generated_api.py`, and `github-actions.yml`. Verify that every operation has a positive scenario and required parameters produce a negative scenario.

### Lesson 3 — Execution policy

Study the allowlist, explicit `APPROVED` token, resolved workspace boundary, and fixed Pytest command. Discuss why substring host matching and arbitrary shell commands would be unsafe.

### Lesson 4 — Release confidence

Run:

```powershell
specvora assess examples\petstore_results.json --audit-log workspaces\petstore-demo\runs\audit.jsonl
specvora verify-audit workspaces\petstore-demo\runs\audit.jsonl
```

Change one failed test into a critical failure and predict the decision before running again. Explain why a high score cannot override a critical failure.

### Lesson 5 — Evidence review

Run `python -m pytest --cov=specvora --cov-report=term-missing -q` and `python -m ruff check src tests`. Relate each control to its test rather than treating coverage as proof by itself.

### Lesson 6 — Generated-case validation

Inspect `request-cases.json` together with `validation-report.json`. Confirm positive cases satisfy the schema, negatives are rejected, and overlapping `oneOf` alternatives are reported before human approval.

### Lesson 7 — Generation quality gate

Compare `READY_FOR_HUMAN_APPROVAL`, explicit `APPROVED`, and release-confidence decisions. Demonstrate that a malformed or blocked gate prevents the local runner from starting.

### Lesson 8 — Deterministic Playwright journeys

Run `specvora analyze examples/web_project.json` and compare the declarative journey with
the generated Playwright plan and TypeScript. Demonstrate that invalid navigation is
rejected and that generation never launches a browser. Complete
`docs/training/MODULE_10_LAB.md`.

### Lesson 9 — Controlled Playwright execution

Trace the fixed browser command, dedicated approval, plan-drift checks, confined report,
filtered environment, and page-level host blocking. Complete
`docs/training/MODULE_11_LAB.md` and distinguish browser routing from OS-level isolation.

### Lesson 10 — Playwright evidence

Normalize a browser report, inspect its SHA-256 evidence, and follow the shared result into
release confidence and the hash-chained audit. Complete `docs/training/MODULE_12_LAB.md`
and demonstrate why flaky tests reduce confidence.

### Lesson 11 — Governed AI proposals

Run an opt-in structured proposal, inspect its provenance, and deliberately produce
semantic violations through the test fixture. Complete `docs/training/MODULE_13_LAB.md`
and explain why the model cannot approve, promote, generate, or execute its own output.

### Lesson 12 — Human proposal promotion

Review offline AI fixtures, disposition every proposal, and inspect the two input hashes,
immutable decision record, and promoted catalog. Complete
`docs/training/MODULE_14_LAB.md` and identify every authority boundary still remaining.

### Lesson 13 — Container network isolation

Create and verify an approved egress policy, inspect its default-deny rules, and trace how
the container applies them before dropping all capabilities. Complete
`docs/training/MODULE_15_LAB.md` and explain why the application allowlist and OS firewall
remain independent controls.

### Lesson 14 — Multi-project human review portal

Register two confined projects, queue a policy-ready proposal, and record a complete human
decision through the local portal. Complete `docs/training/MODULE_16_LAB.md` and explain why
SQLite status, a button click, and a model response are not independent release authority.

## Trainer checklist

Module 20: use `docs/training/MODULE_20_LAB.md` to demonstrate explicit 429/503 fixtures,
valid request baselines, restricted control headers and separate signed execution authority.

Module 19: complete `docs/training/MODULE_19_LAB.md` to bind promoted scenarios to
deterministic cases, inspect blocked fixtures and distinguish generation from signed execution.

Module 18: use `docs/training/MODULE_18_LAB.md` to migrate from unsigned labs, export action
bytes, sign offline and demonstrate rejection of drift and reused authorization.

Module 17: complete `docs/training/MODULE_17_LAB.md` to distinguish trusted-key verification,
one-time consumption, and combined API/browser recommendations from execution authority.

- learners can distinguish proposal, validation, authorization, and execution;
- learners can trace requirement to scenario and generated test;
- learners can explain each confidence component;
- learners can detect a modified audit log;
- learners can explain the boundary between browser-test generation and execution;
- learners can distinguish application-level request blocking from network isolation;
- learners can trace Playwright results into confidence without granting release authority;
- learners can separate AI proposal quality from deterministic policy and human authority;
- learners can explain why promotion is neither test generation nor execution approval;
- learners can distinguish an application allowlist from enforced network egress isolation;
- learners can trace a portal decision to its immutable review and promotion artifacts;
- learners know that release recommendations do not replace accountable people.
