# Module 44 — Leased OIDC monitor cycles

Module 44 turns read-only trust monitoring and alert delivery into one bounded operational cycle
without granting scheduling code authority to change identity trust.

## Cycle contract

- A transactional SQLite lease admits only one owner for a named monitor at a time.
- Leases have a bounded lifetime and can be reclaimed after interruption or process loss.
- Every completed attempt records only cycle ID, time, enumerated monitor/delivery states, optional
  alert ID and the SHA-256 digest of the report.
- Tokens, remote bodies, discovery payloads and private material never enter monitor history.
- Healthy observations do not contact the alert receiver.
- Delivery failures are recorded generically and always release the lease.
- The CLI reads receiver authentication only from `SPECVORA_OIDC_ALERT_TOKEN` at runtime.
- The one-cycle and task-registration scripts contain no trust proposal, approval or apply command.

`scripts/run-oidc-monitor-cycle.ps1` is the scheduler-safe entry point. A `.psd1` configuration
file can hold non-secret endpoints and paths. `scripts/register-oidc-monitor-task.ps1` requires
`-ApproveTaskRegistration`, ignores overlapping Windows Task Scheduler instances and limits each
run to five minutes. Registration remains an explicit operator action.

SQLite coordinates one Windows host only. Production requires distributed leasing, managed
workload identity, receiver-side idempotency/retention, paging ownership and measured SLOs.
