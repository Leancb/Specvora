"""Server-owned trust configuration and action-bound approval consumption."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from pydantic import BaseModel

from specvora.approval_ledger import claim_github_reference
from specvora.signed_approval import SignedApproval, consume_approval, verify_approval


def canonical_action(action: dict) -> bytes:
    return json.dumps(action, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def authorization_mode() -> str:
    mode = os.getenv("SPECVORA_AUTH_MODE", "signed")
    if mode not in {"signed", "local-development"}:
        raise ValueError("Invalid server authorization mode")
    return mode


def authorize_action(
    envelope: SignedApproval | None,
    action: bytes,
    project_id: str,
    purpose: str,
    reviewer: str | None = None,
) -> str | None:
    if authorization_mode() == "local-development":
        return None
    if envelope is None:
        raise ValueError("Signed approval is required")
    key_path = os.getenv("SPECVORA_TRUSTED_PUBLIC_KEY")
    ledger_backend = os.getenv("SPECVORA_APPROVAL_LEDGER_BACKEND", "sqlite")
    trusted_reviewer = os.getenv("SPECVORA_APPROVER_NAME")
    if not key_path or not trusted_reviewer:
        raise ValueError("Server signing trust configuration is incomplete")
    if envelope.claims.reviewer != trusted_reviewer or (
        reviewer is not None and reviewer != trusted_reviewer
    ):
        raise ValueError("Reviewer does not match the configured signing identity")
    if not project_id:
        raise ValueError("Signed execution requires a project ID")
    key = Ed25519PublicKey.from_public_bytes(Path(key_path).read_bytes())
    now = datetime.now(UTC)
    if ledger_backend == "sqlite":
        ledger_path = os.getenv("SPECVORA_APPROVAL_LEDGER")
        if not ledger_path:
            raise ValueError("Server signing trust configuration is incomplete")
        claims = consume_approval(
            envelope, action, key, project_id, purpose, now, Path(ledger_path)
        )
    elif ledger_backend == "github-ref":
        claims = verify_approval(envelope, action, key, project_id, purpose, now)
        repository = os.getenv("SPECVORA_GITHUB_LEDGER_REPOSITORY", "")
        commit_sha = os.getenv("SPECVORA_GITHUB_LEDGER_SHA", "")
        token = os.getenv("SPECVORA_GITHUB_LEDGER_TOKEN", "")
        claim_github_reference(claims.approval_id, repository, commit_sha, token)
    else:
        raise ValueError("Invalid approval ledger backend")
    return str(claims.approval_id)


def execution_action(request: BaseModel, kind: str) -> bytes:
    fields = request.model_dump(mode="json", exclude={"signed_approval"})
    root = Path(fields["workspace_root"]).resolve()
    generated = Path(fields["generated_dir"]).resolve()
    if not generated.is_relative_to(root) or not generated.is_dir():
        raise ValueError("Execution artifacts escape the workspace or are missing")
    files = {}
    for path in sorted(generated.rglob("*")):
        relative = path.relative_to(generated)
        if any(part in {"node_modules", "__pycache__", ".pytest_cache"} for part in relative.parts):
            continue
        if not path.resolve().is_relative_to(generated):
            raise ValueError("Execution artifact link escapes the generated directory")
        if path.is_file():
            files[relative.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    path_mode = os.getenv("SPECVORA_ACTION_PATH_MODE", "absolute")
    if path_mode not in {"absolute", "workspace-relative"}:
        raise ValueError("Invalid execution action path mode")
    report = Path(fields["report_path"]).resolve()
    if not report.is_relative_to(root):
        raise ValueError("Execution report escapes the workspace")
    if path_mode == "workspace-relative":
        fields["workspace_root"] = "$WORKSPACE"
        fields["generated_dir"] = generated.relative_to(root).as_posix()
        fields["report_path"] = report.relative_to(root).as_posix()
        version = "execution-v2-portable"
    else:
        for name in ("workspace_root", "generated_dir", "report_path"):
            fields[name] = str(Path(fields[name]).resolve())
        version = "execution-v1"
    fields["allowed_hosts"] = sorted(set(fields["allowed_hosts"]))
    return canonical_action({"version": version, "kind": kind, "request": fields, "files": files})
