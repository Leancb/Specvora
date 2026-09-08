"""Leased, auditable execution cycles for read-only OIDC monitoring."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict

from specvora.oidc_alert import deliver_oidc_alert
from specvora.oidc_monitor import monitor_oidc_trust


class OidcMonitorCycleResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: Literal["specvora-oidc-cycle-v1"] = "specvora-oidc-cycle-v1"
    cycle_id: str
    status: Literal["COMPLETED", "SKIPPED_LEASE", "DELIVERY_FAILED"]
    monitor_status: Literal["HEALTHY", "REVIEW_REQUIRED", "BLOCKED"] | None = None
    delivery_status: Literal["NO_ALERT", "DELIVERED", "DELIVERY_FAILED"] | None = None
    alert_id: str | None = None


class OidcMonitorCycleStore:
    def __init__(self, database: Path, workspace_root: Path):
        self.database = _confined(database, workspace_root, ".db")
        self.database.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def acquire(self, name: str, owner: str, now: datetime, ttl_seconds: int) -> bool:
        _validate_identity(name, "lease name")
        _validate_identity(owner, "lease owner")
        if now.tzinfo is None or not 30 <= ttl_seconds <= 3600:
            raise ValueError("OIDC monitor lease configuration is invalid")
        expires_at = (now.astimezone(UTC) + timedelta(seconds=ttl_seconds)).isoformat()
        instant = now.astimezone(UTC).isoformat()
        with self._transaction() as connection:
            changed = connection.execute(
                """INSERT INTO oidc_monitor_leases(name, owner, expires_at)
                   VALUES (?, ?, ?)
                   ON CONFLICT(name) DO UPDATE SET owner=excluded.owner,
                     expires_at=excluded.expires_at
                   WHERE oidc_monitor_leases.expires_at <= ?""",
                (name, owner, expires_at, instant),
            ).rowcount
        return changed == 1

    def release(self, name: str, owner: str) -> None:
        with self._transaction() as connection:
            connection.execute(
                "DELETE FROM oidc_monitor_leases WHERE name = ? AND owner = ?", (name, owner)
            )

    def record(
        self,
        cycle_id: str,
        observed_at: datetime,
        monitor_status: str,
        delivery_status: str,
        alert_id: str | None,
        report_sha256: str,
    ) -> None:
        _validate_identity(cycle_id, "cycle id")
        if observed_at.tzinfo is None:
            raise ValueError("OIDC monitor observation must be timezone-aware")
        if monitor_status not in {"HEALTHY", "REVIEW_REQUIRED", "BLOCKED"}:
            raise ValueError("OIDC monitor status is invalid")
        if delivery_status not in {"NO_ALERT", "DELIVERED", "DELIVERY_FAILED"}:
            raise ValueError("OIDC monitor delivery status is invalid")
        if len(report_sha256) != 64:
            raise ValueError("OIDC monitor report digest is invalid")
        with self._transaction() as connection:
            connection.execute(
                """INSERT INTO oidc_monitor_history
                   (cycle_id, observed_at, monitor_status, delivery_status, alert_id,
                    report_sha256) VALUES (?, ?, ?, ?, ?, ?)""",
                (cycle_id, observed_at.astimezone(UTC).isoformat(), monitor_status,
                 delivery_status, alert_id, report_sha256),
            )

    def history(self, limit: int = 20) -> list[dict[str, object]]:
        if not 1 <= limit <= 100:
            raise ValueError("OIDC monitor history limit is invalid")
        with sqlite3.connect(self.database) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """SELECT cycle_id, observed_at, monitor_status, delivery_status,
                          alert_id, report_sha256
                   FROM oidc_monitor_history ORDER BY observed_at DESC, cycle_id DESC LIMIT ?""",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def _initialize(self) -> None:
        with self._transaction() as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS oidc_monitor_leases(
                   name TEXT PRIMARY KEY, owner TEXT NOT NULL, expires_at TEXT NOT NULL)"""
            )
            connection.execute(
                """CREATE TABLE IF NOT EXISTS oidc_monitor_history(
                   cycle_id TEXT PRIMARY KEY, observed_at TEXT NOT NULL,
                   monitor_status TEXT NOT NULL, delivery_status TEXT NOT NULL,
                   alert_id TEXT, report_sha256 TEXT NOT NULL)"""
            )

    @contextmanager
    def _transaction(self):
        connection = sqlite3.connect(self.database, timeout=10, isolation_level=None)
        try:
            connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()


def run_oidc_monitor_cycle(
    discovery_endpoint: str,
    issuer: str,
    provider_allowed_hosts: set[str],
    trust_file: Path,
    audit_log: Path,
    workspace_root: Path,
    alert_endpoint: str,
    alert_allowed_hosts: set[str],
    alert_token: str,
    state_database: Path,
    *,
    cycle_id: str | None = None,
    lease_name: str = "oidc-trust-monitor",
    lease_owner: str | None = None,
    lease_seconds: int = 120,
    now: datetime | None = None,
    discovery_transport=None,
    alert_transport=None,
    sleeper=None,
) -> OidcMonitorCycleResult:
    instant = (now or datetime.now(UTC)).astimezone(UTC)
    identifier = cycle_id or str(uuid4())
    owner = lease_owner or str(uuid4())
    store = OidcMonitorCycleStore(state_database, workspace_root)
    if not store.acquire(lease_name, owner, instant, lease_seconds):
        return OidcMonitorCycleResult(cycle_id=identifier, status="SKIPPED_LEASE")
    try:
        report = monitor_oidc_trust(
            discovery_endpoint, issuer, provider_allowed_hosts, trust_file, audit_log,
            workspace_root, now=instant, transport=discovery_transport,
        )
        canonical = json.dumps(
            report.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
        ).encode()
        digest = hashlib.sha256(canonical).hexdigest()
        try:
            delivery = deliver_oidc_alert(
                report, alert_endpoint, alert_allowed_hosts, alert_token,
                transport=alert_transport, **({} if sleeper is None else {"sleeper": sleeper}),
            )
        except (RuntimeError, ValueError):
            store.record(identifier, instant, report.status, "DELIVERY_FAILED", None, digest)
            return OidcMonitorCycleResult(
                cycle_id=identifier, status="DELIVERY_FAILED",
                monitor_status=report.status, delivery_status="DELIVERY_FAILED",
            )
        store.record(
            identifier, instant, report.status, str(delivery["status"]),
            delivery["alert_id"] if isinstance(delivery["alert_id"], str) else None, digest,
        )
        return OidcMonitorCycleResult(
            cycle_id=identifier, status="COMPLETED", monitor_status=report.status,
            delivery_status=delivery["status"], alert_id=delivery["alert_id"],
        )
    finally:
        store.release(lease_name, owner)


def _confined(path: Path, root: Path, suffix: str) -> Path:
    resolved = (path if path.is_absolute() else root / path).resolve()
    if resolved.suffix.lower() != suffix or not resolved.is_relative_to(root.resolve()):
        raise ValueError("OIDC monitor state escapes the workspace")
    return resolved


def _validate_identity(value: str, label: str) -> None:
    if not 1 <= len(value) <= 128 or any(character.isspace() for character in value):
        raise ValueError(f"OIDC monitor {label} is invalid")
