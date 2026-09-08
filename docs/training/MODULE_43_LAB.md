# Module 43 lab — OIDC alert delivery

## Objective

Deliver a bounded trust alert while proving that notification cannot rotate keys.

## Exercise

1. Run `python -m pytest tests/test_oidc_alert.py -q`.
2. Submit a healthy report and confirm the controlled receiver receives no request.
3. Submit the same warning twice with different observation times.
4. Confirm both deliveries use the same SHA-256 `Idempotency-Key`.
5. Return 503 then 202 and observe one bounded retry.
6. Test an unallowlisted or HTTP destination and confirm rejection before transport.
7. Search the workflow script and verify it contains no trust-update command.

For an operated receiver, place its bearer only in `SPECVORA_OIDC_ALERT_TOKEN`, choose a new
confined report filename for each run, and invoke `scripts/monitor-and-alert-oidc.ps1`.
