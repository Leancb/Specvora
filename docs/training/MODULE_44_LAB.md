# Module 44 lab — Scheduled monitor cycles

1. Run `python -m pytest tests/test_oidc_cycle.py tests/test_oidc_cycle_scripts.py -q`.
2. Start eight simultaneous lease acquisitions and confirm exactly one owner succeeds.
3. Advance controlled time past expiry and confirm a new owner can reclaim the lease.
4. Run a healthy cycle and verify no request reaches the alert receiver.
5. Run an overlapping-key observation and inspect the fixed history row and report digest.
6. Reject alert delivery; verify `DELIVERY_FAILED`, absence of tokens/bodies and lease release.
7. Inspect both PowerShell scripts and prove neither can propose, approve or apply a trust change.
8. Prepare a non-secret `.psd1` configuration. Register a local task only in a disposable lab by
   passing `-ApproveTaskRegistration`; do not place the runtime token in that file.

Explain why Task Scheduler overlap prevention and the SQLite lease are independent controls, and
why neither replaces a distributed lease or an operated alert SLO.
