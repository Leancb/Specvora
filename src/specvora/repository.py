from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class ProjectRepository:
    def __init__(self, database: Path) -> None:
        self.database = database
        database.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database, timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with closing(self._connect()) as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    project_id TEXT PRIMARY KEY,
                    project_file TEXT NOT NULL,
                    workspace_root TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS reviews (
                    review_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL REFERENCES projects(project_id),
                    proposal_file TEXT NOT NULL,
                    proposal_sha256 TEXT NOT NULL UNIQUE,
                    status TEXT NOT NULL CHECK(status IN ('PENDING', 'REVIEWED')),
                    created_at TEXT NOT NULL,
                    reviewed_at TEXT,
                    review_record TEXT,
                    promotion_catalog TEXT
                );
                """
            )
            connection.commit()

    def add_project(
        self, project_id: str, project_file: Path, workspace_root: Path
    ) -> dict[str, Any]:
        created = datetime.now(UTC).isoformat()
        try:
            with closing(self._connect()) as connection:
                connection.execute(
                    "INSERT INTO projects VALUES (?, ?, ?, ?)",
                    (project_id, str(project_file), str(workspace_root), created),
                )
                connection.commit()
        except sqlite3.IntegrityError as exc:
            raise ValueError(f"Project already exists: {project_id}") from exc
        return self.get_project(project_id)

    def get_project(self, project_id: str) -> dict[str, Any]:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT * FROM projects WHERE project_id = ?", (project_id,)
            ).fetchone()
        if row is None:
            raise ValueError(f"Project was not found: {project_id}")
        return dict(row)

    def list_projects(self) -> list[dict[str, Any]]:
        with closing(self._connect()) as connection:
            rows = connection.execute("SELECT * FROM projects ORDER BY project_id").fetchall()
        return [dict(row) for row in rows]

    def add_review(
        self, review_id: str, project_id: str, proposal_file: Path, proposal_sha256: str
    ) -> dict[str, Any]:
        try:
            with closing(self._connect()) as connection:
                connection.execute(
                    "INSERT INTO reviews(review_id, project_id, proposal_file, proposal_sha256, "
                    "status, created_at) VALUES (?, ?, ?, ?, 'PENDING', ?)",
                    (
                        review_id,
                        project_id,
                        str(proposal_file),
                        proposal_sha256,
                        datetime.now(UTC).isoformat(),
                    ),
                )
                connection.commit()
        except sqlite3.IntegrityError as exc:
            raise ValueError("Review ID or proposal already exists") from exc
        return self.get_review(review_id)

    def get_review(self, review_id: str) -> dict[str, Any]:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT * FROM reviews WHERE review_id = ?", (review_id,)
            ).fetchone()
        if row is None:
            raise ValueError(f"Review was not found: {review_id}")
        return dict(row)

    def list_reviews(self, status: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM reviews"
        parameters: tuple[str, ...] = ()
        if status is not None:
            if status not in {"PENDING", "REVIEWED"}:
                raise ValueError("Review status filter is invalid")
            query += " WHERE status = ?"
            parameters = (status,)
        with closing(self._connect()) as connection:
            rows = connection.execute(query + " ORDER BY created_at", parameters).fetchall()
        return [dict(row) for row in rows]

    def complete_review(self, review_id: str, record: Path, catalog: Path) -> dict[str, Any]:
        with closing(self._connect()) as connection:
            cursor = connection.execute(
                "UPDATE reviews SET status='REVIEWED', reviewed_at=?, review_record=?, "
                "promotion_catalog=? WHERE review_id=? AND status='PENDING'",
                (datetime.now(UTC).isoformat(), str(record), str(catalog), review_id),
            )
            if cursor.rowcount != 1:
                raise ValueError("Review is no longer pending")
            connection.commit()
        return self.get_review(review_id)
