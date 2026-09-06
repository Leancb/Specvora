"""Durable approval consumption backends controlled by the execution environment."""

from __future__ import annotations

import re
from uuid import UUID

import httpx

_REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_COMMIT_SHA = re.compile(r"^[0-9a-fA-F]{40}$")


def claim_github_reference(
    approval_id: UUID,
    repository: str,
    commit_sha: str,
    token: str,
    *,
    client: httpx.Client | None = None,
) -> str:
    """Atomically claim an approval UUID by creating a unique Git tag reference."""
    if not _REPOSITORY.fullmatch(repository):
        raise ValueError("GitHub ledger repository is invalid")
    if not _COMMIT_SHA.fullmatch(commit_sha):
        raise ValueError("GitHub ledger commit SHA is invalid")
    if not token.strip():
        raise ValueError("GitHub ledger token is missing")
    reference = f"refs/tags/specvora-approvals/{approval_id}"
    owns_client = client is None
    http = client or httpx.Client(timeout=10, follow_redirects=False)
    try:
        response = http.post(
            f"https://api.github.com/repos/{repository}/git/refs",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": "2026-03-10",
            },
            json={"ref": reference, "sha": commit_sha.lower()},
        )
    except httpx.HTTPError as exc:
        raise ValueError("GitHub approval ledger is unavailable") from exc
    finally:
        if owns_client:
            http.close()
    if response.status_code == 201:
        return reference
    if response.status_code in {409, 422}:
        raise ValueError("Approval ledger rejected claim; approval may already be consumed")
    if response.status_code in {401, 403}:
        raise ValueError("GitHub approval ledger authorization failed")
    raise ValueError(f"GitHub approval ledger failed with status {response.status_code}")
