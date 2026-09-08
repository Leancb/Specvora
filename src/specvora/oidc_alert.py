"""Authenticated, idempotent delivery of deterministic OIDC trust alerts."""

from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Callable
from urllib.parse import urlparse

import httpx

from specvora.oidc_monitor import OidcTrustMonitorReport


def deliver_oidc_alert(
    report: OidcTrustMonitorReport,
    endpoint: str,
    allowed_hosts: set[str],
    token: str,
    *,
    transport=None,
    sleeper: Callable[[float], None] = time.sleep,
) -> dict[str, object]:
    if report.status == "HEALTHY":
        return {"status": "NO_ALERT", "alert_id": None, "attempts": 0}
    parsed = urlparse(endpoint)
    normalized_hosts = {host.casefold().rstrip(".") for host in allowed_hosts}
    host = parsed.hostname.casefold().rstrip(".") if parsed.hostname else ""
    if (
        parsed.scheme != "https" or not host or host not in normalized_hosts
        or parsed.username or parsed.password or parsed.query or parsed.fragment or not parsed.path
    ):
        raise ValueError("OIDC alert endpoint is not an allowed HTTPS destination")
    if not 32 <= len(token) <= 4096 or any(character.isspace() for character in token):
        raise ValueError("OIDC alert runtime token is invalid")
    signal = {
        "status": report.status, "issuer": report.issuer,
        "current_jwks_sha256": report.current_jwks_sha256,
        "discovered_jwks_sha256": report.discovered_jwks_sha256,
        "current_key_ids": report.current_key_ids,
        "discovered_key_ids": report.discovered_key_ids,
        "findings": report.findings,
    }
    signal_bytes = json.dumps(signal, sort_keys=True, separators=(",", ":")).encode()
    alert_id = hashlib.sha256(signal_bytes).hexdigest()
    payload = {
        "version": "specvora-oidc-alert-v1", "alert_id": alert_id,
        "severity": "WARNING" if report.status == "REVIEW_REQUIRED" else "CRITICAL",
        "observed_at": report.checked_at.isoformat(), **signal,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    attempts = 0
    accepted = False
    with httpx.Client(
        timeout=5, follow_redirects=False, trust_env=False, transport=transport
    ) as client:
        for attempt in range(3):
            attempts += 1
            try:
                response = client.post(endpoint, content=canonical, headers={
                    "Authorization": f"Bearer {token}", "Content-Type": "application/json",
                    "Idempotency-Key": alert_id,
                })
                if response.status_code in {200, 202, 204}:
                    accepted = True
                    break
                if response.status_code != 429 and not 500 <= response.status_code <= 599:
                    break
            except httpx.HTTPError:
                pass
            if attempt < 2:
                sleeper(float(2**attempt))
    if not accepted:
        raise RuntimeError("OIDC alert receiver did not accept the alert")
    return {"status": "DELIVERED", "alert_id": alert_id, "attempts": attempts}
