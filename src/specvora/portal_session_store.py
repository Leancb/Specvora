"""Transactional local state for portal sessions and MFA replay prevention."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path


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
