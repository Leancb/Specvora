# Module 01 — Deterministic OpenAPI analysis

## Objective

Turn a validated project definition and OpenAPI 3 contract into a deterministic quality plan,
traceability matrix and readable Pytest/HTTPX suite without executing the generated code.

## Inputs and outputs

The project file identifies the project, requirements, OpenAPI document and workspace. The
pipeline validates and confines those paths, extracts operations, parameters, request bodies and
documented responses, then generates customer-owned artifacts under the project workspace.

Each operation receives a positive scenario. Required inputs also produce explicit negative
scenarios. Repeated analysis of identical bytes produces equivalent plans and tests, making human
review and later audit practical.

## Authority boundary

Generation is not execution. Generated code remains an inspectable artifact until a separate
execution policy validates the target, workspace and explicit human authorization. Optional AI
features introduced later cannot bypass this deterministic foundation.

## Demonstration

```powershell
specvora analyze examples\petstore_project.json
```

Inspect the generated quality plan, traceability matrix and Pytest file before approving any run.
