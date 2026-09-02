# Module 03 — Deterministic Schema Data Generation

## Objective

Transform OpenAPI parameter and JSON request-body schemas into reviewable valid and negative data cases without AI, randomness, network calls, or hidden heuristics.

## Supported schema subset

- object properties and required fields;
- arrays with one deterministic item;
- string examples, defaults, enums, and `minLength`;
- integer and number `minimum`;
- booleans;
- parameter schemas for path, query, header, and cookie locations.

Unsupported keywords remain visible in the source contract and are not guessed. `$ref`, composition keywords, formats, patterns, and complex array constraints are planned extensions.

## Generated cases

- one valid case for every operation;
- one omission case for each required parameter;
- one omission case for each required JSON body property;
- one invalid boundary case for the first deterministic `minLength`, `minimum`, or enum constraint.

The output is `request-cases.json` beside the quality plan, traceability matrix, generated test, and CI workflow.

## Safety and ownership

Cases are data proposals. They are not executed automatically, do not contain secrets, and do not bypass the existing host allowlist, approval, or workspace policy.

## Demonstration

```powershell
specvora analyze examples\petstore_project.json
Get-Content workspaces\petstore-demo\generated\request-cases.json
```

## Acceptance evidence

- deterministic examples cover supported primitive and nested structures;
- required parameter and body omissions are independently generated;
- boundaries are derived from the contract, not copied from implementation code;
- the full pipeline writes the new artifact without changing existing interfaces.
