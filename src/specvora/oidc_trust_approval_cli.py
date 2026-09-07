"""Operator interface for independently approved OIDC trust changes."""

import argparse
import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from specvora.oidc_trust_approval import (
    OidcTrustProposal,
    apply_approved_oidc_trust_change,
    propose_oidc_trust_change,
    verify_oidc_trust_audit,
)
from specvora.signed_approval import ApprovalClaims


def main() -> None:
    parser = argparse.ArgumentParser(prog="specvora-oidc-governance")
    parser.add_argument("--workspace-root", type=Path, required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    propose = commands.add_parser("propose")
    propose.add_argument("--project-id", required=True)
    propose.add_argument("--discovery-endpoint", required=True)
    propose.add_argument("--issuer", required=True)
    propose.add_argument("--allowed-host", action="append", required=True)
    propose.add_argument("--proposal", type=Path, required=True)
    propose.add_argument("--trust-file", type=Path, required=True)
    propose.add_argument("--bootstrap", action="store_true")
    prepare = commands.add_parser("prepare-approval")
    prepare.add_argument("--proposal", type=Path, required=True)
    prepare.add_argument("--reviewer", required=True)
    prepare.add_argument("--output", type=Path, required=True)
    prepare.add_argument("--valid-minutes", type=int, default=15, choices=range(5, 61))
    apply = commands.add_parser("apply")
    apply.add_argument("--proposal", type=Path, required=True)
    apply.add_argument("--approval", type=Path, required=True)
    apply.add_argument("--public-key", type=Path, required=True)
    apply.add_argument("--trust-file", type=Path, required=True)
    apply.add_argument("--ledger", type=Path, required=True)
    apply.add_argument("--audit-log", type=Path, required=True)
    apply.add_argument("--operator", required=True)
    verify = commands.add_parser("verify-audit")
    verify.add_argument("--audit-log", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "propose":
        result = propose_oidc_trust_change(
            args.project_id, args.discovery_endpoint, args.issuer, set(args.allowed_host),
            args.proposal, args.trust_file, args.workspace_root, bootstrap=args.bootstrap,
        )
        print(json.dumps({"proposal": str(_confined(args.proposal, args.workspace_root)),
                          "jwks_sha256": result.jwks_sha256, "key_ids": result.key_ids}))
    elif args.command == "prepare-approval":
        proposal_path = _confined(args.proposal, args.workspace_root)
        output_path = _confined(args.output, args.workspace_root)
        proposal_bytes = proposal_path.read_bytes()
        proposal = OidcTrustProposal.model_validate_json(proposal_bytes)
        issued = datetime.now(UTC)
        claims = ApprovalClaims(
            project_id=proposal.project_id, purpose="oidc-trust-change",
            reviewer=args.reviewer, artifact_sha256=hashlib.sha256(proposal_bytes).hexdigest(),
            issued_at=issued, expires_at=issued + timedelta(minutes=args.valid_minutes),
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(claims.model_dump_json(indent=2) + "\n")
        print(json.dumps({"claims": str(output_path)}))
    elif args.command == "apply":
        print(json.dumps(apply_approved_oidc_trust_change(
            args.proposal, args.approval, args.public_key, args.trust_file, args.ledger,
            args.audit_log, args.workspace_root, args.operator, now=datetime.now(UTC),
        )))
    else:
        print(json.dumps({"valid": verify_oidc_trust_audit(args.audit_log)}))


def _confined(path: Path, root: Path) -> Path:
    resolved = (path if path.is_absolute() else root / path).resolve()
    if resolved.suffix.lower() != ".json" or not resolved.is_relative_to(root.resolve()):
        raise ValueError("OIDC governance artifact escapes the workspace")
    return resolved


if __name__ == "__main__":
    main()
