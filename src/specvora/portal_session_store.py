"""Transactional local state for portal sessions and MFA replay prevention."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Protocol
from urllib.parse import quote, urlparse

import httpx


class PortalSessionState(Protocol):
    def claim_mfa_counter(self, username: str, counter: int) -> bool: ...
    def register_session(self, session_id: str, username: str, expires_at: datetime) -> None: ...
    def session_is_active(self, session_id: str, now: datetime) -> bool: ...
    def revoke_session(self, session_id: str) -> None: ...


class PortalSessionStore:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS mfa_counters (
                    username TEXT PRIMARY KEY,
                    last_counter INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS portal_sessions (
                    session_id TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    revoked INTEGER NOT NULL DEFAULT 0
                );
                """
            )

    def claim_mfa_counter(self, username: str, counter: int) -> bool:
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            result = connection.execute(
                """INSERT INTO mfa_counters(username, last_counter) VALUES (?, ?)
                ON CONFLICT(username) DO UPDATE SET last_counter=excluded.last_counter
                WHERE excluded.last_counter > mfa_counters.last_counter""",
                (username, counter),
            )
            connection.commit()
            return result.rowcount == 1

    def register_session(
        self, session_id: str, username: str, expires_at: datetime
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO portal_sessions(session_id, username, expires_at) VALUES (?, ?, ?)",
                (session_id, username, expires_at.isoformat()),
            )

    def session_is_active(self, session_id: str, now: datetime) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT expires_at, revoked FROM portal_sessions WHERE session_id=?",
                (session_id,),
            ).fetchone()
        return bool(row and not row[1] and now < datetime.fromisoformat(row[0]))

    def revoke_session(self, session_id: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "UPDATE portal_sessions SET revoked=1 WHERE session_id=?", (session_id,)
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA busy_timeout=10000")
        return connection


class HttpPortalSessionStore:
    """Client for a centralized service implementing the portal state contract."""

    def __init__(self, endpoint: str, token: str, *, transport=None):
        parsed = urlparse(endpoint)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("Portal state endpoint must be an HTTPS origin without credentials")
        if len(token) < 32 or any(character in token for character in "\r\n\x00"):
            raise ValueError("Portal state service token is invalid")
        self.endpoint = endpoint.rstrip("/")
        self.client = httpx.Client(
            headers={"Authorization": f"Bearer {token}"}, timeout=5,
            follow_redirects=False, trust_env=False, transport=transport,
        )

    def claim_mfa_counter(self, username: str, counter: int) -> bool:
        response = self._request("POST", "/v1/mfa-claims", json={"username": username,
                                                                  "counter": counter})
        if response.status_code == 201:
            return True
        if response.status_code == 409:
            return False
        raise RuntimeError("Central portal state service rejected MFA claim")

    def register_session(self, session_id: str, username: str, expires_at: datetime) -> None:
        response = self._request("POST", "/v1/sessions", json={"session_id": session_id,
            "username": username, "expires_at": expires_at.isoformat()})
        if response.status_code != 201:
            raise RuntimeError("Central portal state service rejected session registration")

    def session_is_active(self, session_id: str, now: datetime) -> bool:
        response = self._request("GET", f"/v1/sessions/{quote(session_id, safe='')}",
                                 params={"at": now.isoformat()})
        if response.status_code == 404:
            return False
        if response.status_code != 200:
            raise RuntimeError("Central portal state service rejected session lookup")
        payload = response.json()
        if set(payload) != {"active"} or not isinstance(payload["active"], bool):
            raise RuntimeError("Central portal state service returned an invalid response")
        return payload["active"]

    def revoke_session(self, session_id: str) -> None:
        response = self._request("DELETE", f"/v1/sessions/{quote(session_id, safe='')}")
        if response.status_code != 204:
            raise RuntimeError("Central portal state service rejected session revocation")

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        try:
            return self.client.request(method, self.endpoint + path, **kwargs)
        except httpx.HTTPError as exc:
            raise RuntimeError("Central portal state service is unavailable") from exc
