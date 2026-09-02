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

## Trainer checklist

- learners can distinguish proposal, validation, authorization, and execution;
- learners can trace requirement to scenario and generated test;
- learners can explain each confidence component;
- learners can detect a modified audit log;
- learners know that release recommendations do not replace accountable people.
