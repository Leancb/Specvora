"""Confined, incremental export of structured portal security events."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel, ConfigDict, Field


class SecurityExportEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: int = Field(gt=0)
    event_type: Literal[
        "login_failed", "login_throttled", "login_succeeded",
        "recovery_used", "recovery_rotated",
    ]
    subject: str = Field(pattern=r"^[0-9a-f]{64}$")
    occurred_at: datetime


class SecurityExportCheckpoint(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: Literal["specvora-security-export-v1"] = "specvora-security-export-v1"
    last_event_id: int = Field(default=0, ge=0)


def export_security_events(
    state_db: Path,
    checkpoint_path: Path,
    endpoint: str,
    allowed_hosts: list[str],
    token: str,
    *,
    batch_size: int = 100,
    transport=None,
    sleeper: Callable[[float], None] = time.sleep,
) -> dict[str, int | str]:
    parsed = urlparse(endpoint)
    normalized_hosts = {host.casefold().rstrip(".") for host in allowed_hosts}
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.hostname.casefold().rstrip(".") not in normalized_hosts
    ):
        raise ValueError("SIEM endpoint must be an allowed HTTPS destination without credentials")
    if not 32 <= len(token) <= 4096 or any(character.isspace() for character in token):
        raise ValueError("SIEM runtime token is invalid")
    if not 1 <= batch_size <= 500:
        raise ValueError("Security export batch size must be between 1 and 500")
    checkpoint = _load_checkpoint(checkpoint_path)
    events = _read_events(state_db, checkpoint.last_event_id, batch_size)
    if not events:
        return {"status": "NO_EVENTS", "exported": 0,
                "last_event_id": checkpoint.last_event_id}
    payload = {
        "version": "specvora-security-events-v1",
        "events": [event.model_dump(mode="json") for event in events],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    batch_id = hashlib.sha256(canonical).hexdigest()
    client = httpx.Client(timeout=5, follow_redirects=False, trust_env=False, transport=transport)
    accepted = False
    for attempt in range(3):
        try:
            response = client.post(
                endpoint,
                content=canonical,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "Idempotency-Key": batch_id,
                },
            )
            if response.status_code in {200, 202}:
                accepted = True
                break
            if response.status_code != 429 and not 500 <= response.status_code <= 599:
                break
        except httpx.HTTPError:
            pass
        if attempt < 2:
            sleeper(float(2**attempt))
    client.close()
    if not accepted:
        raise RuntimeError("SIEM collector did not accept the security event batch")
    last_event_id = events[-1].event_id
    _write_checkpoint(checkpoint_path, SecurityExportCheckpoint(last_event_id=last_event_id))
    return {"status": "EXPORTED", "exported": len(events),
            "last_event_id": last_event_id, "batch_id": batch_id}


def _read_events(path: Path, after_id: int, limit: int) -> list[SecurityExportEvent]:
    if not path.is_file():
        raise ValueError("Portal state database does not exist")
    with sqlite3.connect(f"file:{path.resolve().as_posix()}?mode=ro", uri=True) as connection:
        rows = connection.execute(
            """SELECT event_id, event_type, subject, occurred_at FROM security_events
            WHERE event_id > ? ORDER BY event_id LIMIT ?""",
            (after_id, limit),
        ).fetchall()
    return [SecurityExportEvent(event_id=row[0], event_type=row[1], subject=row[2],
                                occurred_at=row[3]) for row in rows]


def _load_checkpoint(path: Path) -> SecurityExportCheckpoint:
    if not path.exists():
        return SecurityExportCheckpoint()
    return SecurityExportCheckpoint.model_validate_json(path.read_bytes())


def _write_checkpoint(path: Path, checkpoint: SecurityExportCheckpoint) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    nonce = hashlib.sha256(str(time.time_ns()).encode()).hexdigest()[:16]
    temporary = path.with_name(f".{path.name}.{nonce}.tmp")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(checkpoint.model_dump_json(indent=2) + "\n")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
