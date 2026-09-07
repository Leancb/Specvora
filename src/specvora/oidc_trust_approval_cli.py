"""Operator interface for independently approved OIDC trust changes."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from specvora.oidc_trust_approval import (
    apply_approved_oidc_trust_change,
    propose_oidc_trust_change,
    verify_oidc_trust_audit,
)


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
        print(json.dumps({"proposal": str(args.proposal.resolve()),
                          "jwks_sha256": result.jwks_sha256, "key_ids": result.key_ids}))
    elif args.command == "apply":
        print(json.dumps(apply_approved_oidc_trust_change(
            args.proposal, args.approval, args.public_key, args.trust_file, args.ledger,
            args.audit_log, args.workspace_root, args.operator, now=datetime.now(UTC),
        )))
    else:
        print(json.dumps({"valid": verify_oidc_trust_audit(args.audit_log)}))


if __name__ == "__main__":
    main()
