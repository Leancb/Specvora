# Module 06 — Controlled Local Pytest Runner

## Objective

Execute only human-approved generated Pytest files through a fixed, confined process and feed the resulting JSON report into normalized evidence and release confidence.

## Controls

- exact human approval token `APPROVED`;
- exact target-host allowlist inherited from the execution policy;
- fixed file name `test_generated_api.py` inside the workspace;
- Python executable from the current trusted runtime;
- fixed `python -m pytest` argument list;
- `shell=False`, preventing shell interpolation;
- report output confined to the workspace;
- timeout from 1 to 300 seconds;
- captured output truncated at 20,000 characters;
- environment reduced to required Windows/Python runtime variables (`APPDATA`, `LOCALAPPDATA`, `PATH`, `SYSTEMROOT`, temporary directories) and `SPECVORA_BASE_URL`;
- no API keys or arbitrary parent-process variables are inherited.

## End-to-end flow

`human approval -> policy validation -> fixed Pytest process -> JSON report -> evidence normalization -> confidence assessment -> audit chain`

A nonzero test exit is evidence, not a runner crash. Missing report output and timeouts are runner failures and stop normalization.

## CLI

```powershell
specvora run-pytest `
  --workspace-root workspaces\petstore-demo `
  --generated-dir workspaces\petstore-demo\generated `
  --report-out workspaces\petstore-demo\runs\report.json `
  --evidence-out workspaces\petstore-demo\runs\evidence.json `
  --audit-log workspaces\petstore-demo\runs\audit.jsonl `
  --base-url http://localhost:8080 `
  --allowed-host localhost `
  --approval APPROVED `
  --project-id petstore-demo `
  --run-id local-001 `
  --requirements-total 5 `
  --requirements-covered 5
```

## Deliberate API limitation

The MVP exposes execution only through the local CLI. The FastAPI portal does not receive a remote execution endpoint because authentication, authorization, CSRF protection, process isolation, and tenant boundaries are not yet implemented.
